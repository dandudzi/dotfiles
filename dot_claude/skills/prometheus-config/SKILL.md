---
name: prometheus-config
description: >
  Prometheus server configuration, scrape setup, service discovery, label manipulation,
  recording rules, alerting, and long-term storage. Use when configuring Prometheus
  for metrics collection at scale.
model: sonnet
---

# Prometheus Configuration

## When to Activate

- Setting up Prometheus scrape configs
- Configuring service discovery (Kubernetes, EC2, file-based)
- Designing alerting rules and alert routing
- Tuning cardinality and retention policies

## Prometheus Server Configuration

### Basic prometheus.yml

```yaml
global:
  scrape_interval: 30s          # Default scrape interval
  scrape_timeout: 10s           # Timeout per scrape
  evaluation_interval: 30s      # How often to evaluate alert rules
  external_labels:
    cluster: "production"
    region: "us-east-1"

alerting:
  alertmanagers:
  - static_configs:
    - targets: ["alertmanager:9093"]

rule_files:
- "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
    - targets: ["localhost:9090"]

  - job_name: "api-servers"
    scrape_interval: 15s        # Override global interval
    metrics_path: "/metrics"
    static_configs:
    - targets: ["api1:8080", "api2:8080"]
```

## Service Discovery

### Kubernetes

```yaml
scrape_configs:
- job_name: "kubernetes-pods"
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names: ["default", "monitoring"]

  relabel_configs:
  # Keep only pods with prometheus.io/scrape=true annotation
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: "true"

  # Use pod name as instance
  - source_labels: [__meta_kubernetes_pod_name]
    action: replace
    target_label: instance

  # Add namespace label
  - source_labels: [__meta_kubernetes_namespace]
    action: replace
    target_label: kubernetes_namespace
```

### File-Based SD

```yaml
scrape_configs:
- job_name: "file-sd"
  file_sd_configs:
  - files: ["/etc/prometheus/targets/*.yml"]
    refresh_interval: 30s
```

Target file `/etc/prometheus/targets/web-servers.yml`:

```yaml
- targets: ["web1:8080", "web2:8080"]
  labels:
    group: "web"
    env: "production"
```

### EC2 SD

```yaml
scrape_configs:
- job_name: "ec2-instances"
  ec2_sd_configs:
  - region: "us-east-1"
    port: 9100

  relabel_configs:
  - source_labels: [__meta_ec2_tag_Name]
    action: replace
    target_label: instance_name
```

## Label Manipulation

```yaml
relabel_configs:
# Keep targets matching a regex
- source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
  action: keep
  regex: "true"

# Drop specific targets
- source_labels: [job]
  action: drop
  regex: "unused-job"

# Replace label value (simple case)
- source_labels: [__meta_kubernetes_pod_label_version]
  action: replace
  target_label: version

# Use regex capture groups to manipulate addresses
- source_labels: [__address__]
  regex: "([^:]+)(?::(\d+))?"
  replacement: "${1}:8080"
  target_label: __address__

# Concatenate multiple labels
- source_labels: [namespace, pod_name]
  separator: "/"
  target_label: pod_id
```

## Recording Rules

Pre-compute expensive queries to reduce load:

```yaml
groups:
- name: api_metrics
  interval: 30s
  rules:
  - record: job:http_requests:rate5m
    expr: sum by (job) (rate(http_requests_total[5m]))

  - record: job:http_errors:rate5m
    expr: sum by (job) (rate(http_errors_total[5m]))

  - record: job:http_error_rate
    expr: (job:http_errors:rate5m / job:http_requests:rate5m) * 100

  - record: job:http_latency:p99
    expr: histogram_quantile(0.99, sum by (le, job) (rate(http_request_duration_seconds_bucket[5m])))
```

Use precomputed rules in alerts:

```promql
job:http_latency:p99 > 0.5
```

## Alerting Rules

### PrometheusRule CRD (Kubernetes)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
spec:
  groups:
  - name: api
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: job:http_error_rate > 5
      for: 5m
      annotations:
        summary: "{{ $labels.job }} error rate > 5%"
        description: "Error rate is {{ $value }}%"

    - alert: HighLatency
      expr: job:http_latency:p99 > 0.5
      for: 10m
      annotations:
        summary: "{{ $labels.job }} P99 latency > 500ms"
```

### Alertmanager Routing

**Security**: Use environment variables for webhook URLs, never hardcode.

```yaml
# alertmanager.yml
global:
  slack_api_url: ${SLACK_WEBHOOK_URL}
  pagerduty_api_key: ${PAGERDUTY_API_KEY}

route:
  receiver: "default"
  group_by: ["alertname", "job"]
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

  routes:
  # Critical → PagerDuty
  - match:
      severity: critical
    receiver: "pagerduty"
    continue: true

  # API alerts → #api-team
  - match:
      job: "api"
    receiver: "api-team"

# Inhibition: suppress lower-severity alerts if higher-severity exists
inhibit_rules:
- source_match:
    severity: critical
  target_match:
    severity: warning
  equal: ["job", "instance"]
```

### Setup with Environment Variables

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export PAGERDUTY_API_KEY="pdsk_xxxxx"

# Substitute variables before startup
envsubst < alertmanager.yml.template > alertmanager.yml && alertmanager --config.file=alertmanager.yml

# Or via Docker
docker run \
  -e SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL" \
  -e PAGERDUTY_API_KEY="$PAGERDUTY_API_KEY" \
  -v $(pwd)/alertmanager.yml.template:/etc/alertmanager/alertmanager.yml.template \
  --entrypoint sh \
  prom/alertmanager \
  -c 'envsubst < /etc/alertmanager/alertmanager.yml.template > /tmp/alertmanager.yml && alertmanager --config.file=/tmp/alertmanager.yml'
```

### Silences (Temporary Alert Suppression)

```bash
curl -X POST http://alertmanager:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "job", "value": "api", "isRegex": false},
      {"name": "alertname", "value": "HighErrorRate", "isRegex": false}
    ],
    "startsAt": "2026-03-15T10:00:00Z",
    "endsAt": "2026-03-15T12:00:00Z",
    "createdBy": "engineer@example.com",
    "comment": "Maintenance window"
  }'
```

## Long-Term Storage (Remote Write)

**Security**: Always use HTTPS with TLS. Metrics expose infrastructure topology — never use plaintext HTTP.

### Thanos Configuration

```yaml
global:
  external_labels:
    cluster: "prod"
    replica: "1"

remote_write:
- url: "https://thanos-receive.monitoring.svc.cluster.local/api/v1/receive"
  tls_config:
    ca_file: /etc/prometheus/certs/ca.crt
    cert_file: /etc/prometheus/certs/client.crt
    key_file: /etc/prometheus/certs/client.key
  queue_config:
    max_shards: 200
    max_samples_per_send: 10000
    batch_send_wait: 10s
```

### Cortex Configuration

```yaml
remote_write:
- url: "http://cortex:9009/api/prom/push"
  write_relabel_configs:
  # Drop high-cardinality metrics
  - source_labels: [__name__]
    regex: ".*_by_user_id"
    action: drop
```

## Cardinality Management

Identify high-cardinality metrics:

```promql
topk(20, max by (__name__) (count({__name__=~".+"}) by (__name__, job, instance)))
```

Drop unbounded labels:

```yaml
metric_relabel_configs:
# Drop request_id (unbounded, millions of unique values)
- source_labels: [__name__]
  regex: "http_request.*"
  action: drop_equal
  target_label: request_id

# Replace user_id with bounded segment
- source_labels: [user_id]
  regex: "user_([a-z]+)_.*"
  replacement: "$1"
  target_label: user_segment
```

Set size limits:

```yaml
global:
  max_scrape_size: 10MB
  metric_relabel_configs:
  - source_labels: [__name__]
    regex: "(http_request|grpc_request)_.*"
    action: keep
```

## Anti-Patterns

**Unbounded labels**: Never add user_id, request_id, or session_id as labels. Use bounded labels only (tiers, regions, versions).

**Wrong metric types**: Counters (monotonic) must use `_total` suffix. Gauges go up and down. Histograms measure distributions.

**Scrape frequency**: 5s is too aggressive. Default 30s, max 15s for critical services.

**No recording rules**: Don't compute expensive histogram_quantile() on every dashboard load — pre-compute with recording rules.

**Unbounded retention**: retention: 365d consumes too much disk. Use 15d locally + remote storage.

**Alerting on symptoms**: "CPU > 80%" is noisy during batch jobs. Alert on error rate > 5% or latency p99 > 500ms instead.

## Agent Support

- **observability-engineer** — System design, SLO strategy, alerting architecture
- **prometheus-expert** — PromQL optimization, performance tuning
