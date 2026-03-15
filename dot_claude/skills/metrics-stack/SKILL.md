---
name: metrics-stack
description: >
  Prometheus and Grafana monitoring stack: server configuration, PromQL queries,
  alerting rules, dashboard design, SLO panels, and dashboard-as-code.
  Use when configuring the Prometheus/Grafana observability stack.
---

# Metrics Stack

## When to Activate

- Setting up or troubleshooting Prometheus scrape configs
- Configuring Kubernetes service discovery or file-based SD
- Writing PromQL queries for dashboards and alerts
- Defining PrometheusRule CRD resources (Kubernetes operator)
- Implementing long-term metrics storage with Thanos, Cortex, or Mimir
- Managing high-cardinality labels and controlling metrics explosion
- Tuning scrape intervals, timeout, and retention policies
- Designing alerting rules with inhibition and routing
- Designing dashboards for new services or infrastructure
- Choosing panel types for specific metrics
- Configuring templating variables and datasources
- Implementing SLO dashboards with error budgets
- Building dashboard-as-code with Grafonnet or Terraform
- Adding annotations for deployments and incidents
- Troubleshooting slow dashboard queries
- Standardizing dashboard design across teams

## Part 1: Prometheus Configuration

Master Prometheus server setup, scrape configuration, service discovery, PromQL queries, and alerting rules for reliable metrics collection at scale.

### Prometheus Server Configuration

#### Basic prometheus.yml Structure

```yaml
global:
  scrape_interval: 30s          # Default scrape interval
  scrape_timeout: 10s           # Timeout per scrape
  evaluation_interval: 30s      # How often to evaluate alert rules
  external_labels:
    cluster: "production"
    region: "us-east-1"

# Alert configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets: ["alertmanager:9093"]

# Alert rule files
rule_files:
- "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
    - targets: ["localhost:9090"]

  - job_name: "api-servers"
    scrape_interval: 15s        # Override global interval
    scrape_timeout: 5s
    metrics_path: "/metrics"    # Default is /metrics
    static_configs:
    - targets: ["api1:8080", "api2:8080"]
```

#### Service Discovery Patterns

##### Kubernetes SD

```yaml
scrape_configs:
- job_name: "kubernetes-pods"
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names: ["default", "monitoring"]

  relabel_configs:
  # Only scrape pods with annotation prometheus.io/scrape=true
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: "true"

  # Get port from annotation
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
    action: replace
    target_label: __param_port
    regex: ([^:]+)(?::\d+)?;(\d+)
    replacement: $1:$2

  # Use pod name as instance label
  - source_labels: [__meta_kubernetes_pod_name]
    action: replace
    target_label: instance

  # Add namespace label
  - source_labels: [__meta_kubernetes_namespace]
    action: replace
    target_label: kubernetes_namespace

  # Add pod label
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: replace
    target_label: kubernetes_app
```

##### File-Based SD (Dynamic Targets)

```yaml
scrape_configs:
- job_name: "file-sd"
  file_sd_configs:
  - files: ["/etc/prometheus/targets/*.yml"]
    refresh_interval: 30s
```

Example target file `/etc/prometheus/targets/web-servers.yml`:

```yaml
- targets: ["web1:8080", "web2:8080"]
  labels:
    group: "web"
    env: "production"
```

##### EC2 SD

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

  - source_labels: [__meta_ec2_instance_type]
    action: replace
    target_label: instance_type
```

### Relabeling for Label Manipulation

```yaml
relabel_configs:
# Drop targets where label doesn't match
- source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
  action: keep
  regex: "true"

# Drop specific targets
- source_labels: [job]
  action: drop
  regex: "unused-job"

# Replace label value
- source_labels: [__meta_kubernetes_pod_label_version]
  action: replace
  target_label: version

# Use regex capture groups
- source_labels: [__address__]
  regex: "([^:]+)(?::(\d+))?"
  replacement: "${1}:8080"
  target_label: __address__

# Concatenate labels
- source_labels: [namespace, pod_name]
  separator: "/"
  target_label: pod_id
```

### PromQL Essentials

#### Counter Queries (Always Increasing)

```promql
# Request rate (requests per second)
rate(http_requests_total[5m])

# Total requests over time window
increase(http_requests_total[1h])

# Compare request rates by endpoint
rate(http_requests_total{job="api"}[5m]) / rate(http_requests_total{job="api"}[1h]) * 100
```

#### Gauge Queries (Can Go Up or Down)

```promql
# Current memory usage
node_memory_MemAvailable_bytes

# Memory usage as percentage
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

#### Histogram Queries (Distribution)

```promql
# P99 latency (99th percentile)
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Average latency
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

#### Aggregation

```promql
# Sum by label
sum by (job) (rate(http_requests_total[5m]))

# Top 5 endpoints by traffic
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))

# Without label (remove label after aggregation)
sum without (instance) (node_network_receive_bytes_total)
```

#### Label Manipulation

```promql
# Extract label (regex capture)
label_replace(metric, "new_label", "$1", "old_label", "prefix_(.+)_suffix")

# Example: extract user_id from path
label_replace(
  http_request_duration_seconds,
  "user_segment",
  "$1",
  "path",
  "^/users/([a-z]+)/.*"
)
```

#### Complex Queries

```promql
# Error rate by service
sum by (job) (rate(http_errors_total[5m])) / sum by (job) (rate(http_requests_total[5m]))

# Which services are slow? (P99 > 500ms)
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5

# Memory pressure (available < 20% of total)
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.8
```

### Recording Rules

Pre-compute expensive queries to reduce query load:

```yaml
groups:
- name: api_metrics
  interval: 30s
  rules:
  # Record request rate
  - record: job:http_requests:rate5m
    expr: sum by (job) (rate(http_requests_total[5m]))

  # Record error rate
  - record: job:http_errors:rate5m
    expr: sum by (job) (rate(http_errors_total[5m]))

  # Record error rate percentage
  - record: job:http_error_rate
    expr: (job:http_errors:rate5m / job:http_requests:rate5m) * 100

  # Record P99 latency
  - record: job:http_latency:p99
    expr: histogram_quantile(0.99, sum by (le, job) (rate(http_request_duration_seconds_bucket[5m])))
```

Use recording rules in alerts and dashboards:

```promql
# Use precomputed rule instead of expensive histogram_quantile
job:http_latency:p99 > 0.5
```

### Alerting Rules

#### PrometheusRule CRD (Kubernetes)

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
        description: "P99 latency is {{ $value }}s"

    - alert: ServiceDown
      expr: up{job="api"} == 0
      for: 2m
      annotations:
        summary: "{{ $labels.instance }} is down"
```

#### Alertmanager Routing

**Security Requirement**: Webhook URLs MUST NEVER be hardcoded in configuration files. Use environment variables for all secrets (Slack URLs, PagerDuty tokens, etc.). Never commit webhook URLs to version control.

```yaml
# alertmanager.yml
global:
  # Load webhook URL from environment variable
  slack_api_url: ${SLACK_WEBHOOK_URL}
  pagerduty_api_key: ${PAGERDUTY_API_KEY}

route:
  # Default route
  receiver: "default"
  group_by: ["alertname", "job"]
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

  # Child routes
  routes:
  # Critical alerts (page on-call)
  - match:
      severity: critical
    receiver: "pagerduty"
    continue: true

  # API alerts → #api-team
  - match:
      job: "api"
    receiver: "api-team"

  # Database alerts → #dba-team
  - match:
      job: "postgres"
    receiver: "dba-team"

# Inhibition: suppress lower-severity alerts if higher-severity exists
inhibit_rules:
- source_match:
    severity: critical
  target_match:
    severity: warning
  equal: ["job", "instance"]
```

**Setup Instructions:**

```bash
# Export environment variables (DO NOT hardcode in config)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export PAGERDUTY_API_KEY="pdsk_xxxxx"

# Start alertmanager with envsubst to substitute variables
envsubst < alertmanager.yml.template > alertmanager.yml && alertmanager --config.file=alertmanager.yml

# Docker example:
docker run \
  -e SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL" \
  -e PAGERDUTY_API_KEY="$PAGERDUTY_API_KEY" \
  -v $(pwd)/alertmanager.yml.template:/etc/alertmanager/alertmanager.yml.template \
  --entrypoint sh \
  prom/alertmanager \
  -c 'envsubst < /etc/alertmanager/alertmanager.yml.template > /tmp/alertmanager.yml && alertmanager --config.file=/tmp/alertmanager.yml'
```

**Kubernetes Secret Example:**

```bash
kubectl create secret generic alertmanager-secrets \
  --from-literal=slack-webhook-url="$SLACK_WEBHOOK_URL" \
  --from-literal=pagerduty-api-key="$PAGERDUTY_API_KEY"

# Reference in Prometheus Operator PrometheusRule
```

#### Silences (Temporary Alert Suppression)

```bash
# Create silence via Alertmanager API
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
    "comment": "Maintenance window for database migration"
  }'
```

### Long-Term Storage (Remote Write)

**Security Requirement**: Remote write endpoints MUST use HTTPS with TLS validation. Metrics expose topology, performance baselines, and infrastructure details — never send over plaintext HTTP.

#### Thanos Configuration

```yaml
global:
  external_labels:
    cluster: "prod"
    replica: "1"  # For HA setups

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

# CRITICAL: Never use http:// — metrics expose topology, performance baselines, and infrastructure details
# Always use https:// with TLS validation to prevent MITM attacks and credential exposure
```

#### Cortex Configuration

```yaml
remote_write:
- url: "http://cortex:9009/api/prom/push"
  write_relabel_configs:
  # Drop internal metrics
  - source_labels: [__name__]
    regex: "prometheus_.*"
    action: drop

  # Drop high-cardinality metrics
  - source_labels: [__name__]
    regex: ".*_by_user_id"
    action: drop
```

### Cardinality Management

#### Identify High-Cardinality Metrics

```promql
# Count unique label values per metric
count by (__name__) (count by (__name__, job) (metrics))

# Find metrics with most label combinations
topk(20, max by (__name__) (count({__name__=~".+"}) by (__name__, job, instance)))
```

#### Drop High-Cardinality Labels

```yaml
metric_relabel_configs:
# Drop request_id (unbounded, millions of unique values)
- source_labels: [__name__]
  regex: "http_request.*"
  action: drop_equal
  target_label: request_id

# Replace user_id with user_segment
- source_labels: [user_id]
  regex: "user_([a-z]+)_.*"
  replacement: "$1"
  target_label: user_segment
```

#### Set Limits

```yaml
# prometheus.yml
global:
  max_scrape_size: 10MB
  metric_relabel_configs:
  - source_labels: [__name__]
    regex: "(http_request|grpc_request)_.*"
    action: keep
```

### Prometheus Anti-Patterns

```yaml
# ANTI-PATTERN 1: Unbounded label values
- job_name: api
  static_configs:
  - targets: ["localhost:8080"]
  relabel_configs:
  - source_labels: [user_id]  # Millions of unique values!
    action: replace
    target_label: user

# CORRECT: Only bounded labels
relabel_configs:
- source_labels: [user_tier]  # [free, standard, premium]
  action: replace
  target_label: user_segment

# ANTI-PATTERN 2: Using gauge for monotonic data (counters)
# A gauge can go up or down, counters only increase
# Metrics: requests_total, bytes_sent_total must be counters, not gauges

# ANTI-PATTERN 3: Scraping too frequently
# Scrape interval: 5s (too aggressive, causes load)
# CORRECT: 30s default, 15s max for critical services

# ANTI-PATTERN 4: No recording rules for complex queries
# Dashboard queries: histogram_quantile(0.99, ...) on every load
# CORRECT: Pre-compute with recording rules, query the rule instead

# ANTI-PATTERN 5: Keeping all time series forever
# retention: 365d (years of disk space)
# CORRECT: retention: 15d locally, use remote storage for long-term

# ANTI-PATTERN 6: Alerting on symptoms, not causes
# Alert: "CPU > 80%" (normal during batch jobs)
# CORRECT: Alert on error rate > 5%, latency p99 > 500ms (actionable)
```

## Part 2: Grafana Dashboards

Design effective dashboards for monitoring applications and infrastructure using RED method for services, USE method for resources, and SLO-driven alerting.

### Dashboard Design Principles

#### RED Method (Services)

Monitor three signals for every service:

| Signal | Metric | Threshold |
|--------|--------|-----------|
| **Rate** | Requests per second | Should be stable |
| **Errors** | Error count / error rate | Should be < 1% |
| **Duration** | Latency (p50, p95, p99) | p99 < 500ms typical |

```
Dashboard: API Service Health
├── Rate
│   ├── Current RPS (gauge)
│   ├── RPS trend (time series)
│   └── RPS by endpoint (table)
├── Errors
│   ├── Error rate % (gauge)
│   ├── Error count by type (bar chart)
│   └── Error rate trend (time series)
└── Duration
    ├── P99 latency (gauge)
    ├── Latency heatmap (heatmap)
    └── Latency distribution (histogram)
```

#### USE Method (Resources)

Monitor three signals for every resource (CPU, memory, disk, network):

| Signal | Metric | Concern |
|--------|--------|---------|
| **Utilization** | % in use (0-100) | Headroom available? |
| **Saturation** | Queue depth / wait time | Contention? |
| **Errors** | Error count | Hardware failures? |

```
Dashboard: Infrastructure Health
├── CPU
│   ├── Utilization % (gauge)
│   ├── Load average (time series)
│   └── Throttling events (counter)
├── Memory
│   ├── Used % (gauge)
│   ├── Pressure (PSI metrics)
│   └── OOM events (counter)
├── Disk
│   ├── Utilization % (gauge)
│   ├── IOPS (time series)
│   └── I/O latency (histogram)
└── Network
    ├── Bandwidth in/out (time series)
    ├── Packet loss (gauge)
    └── Connection count (gauge)
```

### Panel Types and When to Use

#### Time Series (Most Common)

For trending metrics over time. Suitable for rate, latency, errors.

```json
{
  "type": "timeseries",
  "title": "Request Rate",
  "targets": [
    {
      "expr": "rate(http_requests_total[5m])",
      "legendFormat": "{{ job }}"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "rps",
      "custom": {
        "hideFrom": {"tooltip": false, "legend": false}
      }
    }
  }
}
```

#### Stat (Single Number)

Current value with optional trend arrow. Use for gauges: CPU%, memory, disk space.

```json
{
  "type": "stat",
  "title": "CPU Usage",
  "targets": [
    {
      "expr": "100 * (1 - avg(node_memory_MemAvailable_bytes) / avg(node_memory_MemTotal_bytes))"
    }
  ],
  "options": {
    "graphMode": "area",
    "textMode": "value_and_name"
  }
}
```

#### Gauge (Radial)

Visualize bounded metrics (0-100%) with zones (green/yellow/red).

```json
{
  "type": "gauge",
  "title": "Error Rate",
  "targets": [
    {
      "expr": "(rate(http_errors_total[5m]) / rate(http_requests_total[5m])) * 100"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "min": 0,
      "max": 100,
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": 0},
          {"color": "yellow", "value": 1},
          {"color": "red", "value": 5}
        ]
      }
    }
  }
}
```

#### Table

Display data in rows/columns. Use for listing services, errors, anomalies.

```json
{
  "type": "table",
  "title": "Service Status",
  "targets": [
    {
      "expr": "up{job=\"api\"}"
    }
  ],
  "options": {
    "footer": {"show": false},
    "showHeader": true,
    "sortBy": [{"displayName": "Time", "desc": true}]
  }
}
```

#### Heatmap

Visualize distributions and trends. Ideal for latency histograms (time on X, bucket on Y).

```json
{
  "type": "heatmap",
  "title": "Request Latency Distribution",
  "targets": [
    {
      "expr": "rate(http_request_duration_seconds_bucket[5m])"
    }
  ]
}
```

#### Bar Chart

Compare values across categories. Use for errors by type, requests by endpoint.

```json
{
  "type": "barchart",
  "title": "Errors by Type",
  "targets": [
    {
      "expr": "topk(10, sum by (error_type) (rate(http_errors_total[5m])))"
    }
  ],
  "options": {
    "orientation": "auto"
  }
}
```

### Templating Variables

#### Datasource Variable

```json
{
  "name": "datasource",
  "type": "datasource",
  "datasource": "prometheus",
  "label": "Prometheus"
}
```

#### Label Values Variable

```json
{
  "name": "job",
  "type": "query",
  "datasource": "Prometheus",
  "query": "label_values(up, job)",
  "multi": false,
  "current": {"selected": true, "text": "api", "value": "api"}
}
```

#### Chained Variables

```json
[
  {
    "name": "job",
    "type": "query",
    "query": "label_values(up, job)",
    "current": {"text": "api", "value": "api"}
  },
  {
    "name": "instance",
    "type": "query",
    "query": "label_values(up{job=\"$job\"}, instance)",
    "depends_on": "job"
  }
]
```

#### Using Variables in Queries

```json
{
  "targets": [
    {
      "expr": "rate(http_requests_total{job=\"$job\", instance=\"$instance\"}[5m])",
      "legendFormat": "{{ endpoint }}"
    }
  ]
}
```

### Datasources

#### Prometheus

```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy"
}
```

#### Loki (Logs)

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100"
}
```

#### Tempo (Traces)

```json
{
  "name": "Tempo",
  "type": "tempo",
  "url": "http://tempo:3100"
}
```

#### Elasticsearch (Logs/Metrics)

```json
{
  "name": "Elasticsearch",
  "type": "elasticsearch",
  "url": "http://elasticsearch:9200",
  "database": "logstash-*"
}
```

### LogQL Examples (Loki)

```logql
# All logs from service
{service="api"}

# Filter by log level
{service="api"} | json | level="error"

# Parse JSON and extract fields
{service="api"} | json error_type, duration_ms

# Calculate error rate
sum(rate({service="api"} | json level="error" [5m])) / sum(rate({service="api"} [5m]))

# Logs for a trace
{trace_id="4bf92f3577b34da6a3ce929d0e0e4736"}
```

### Annotations (Deployments, Incidents)

#### Add Annotation to Dashboard

```json
{
  "name": "deployments",
  "type": "prometheus",
  "expr": "ALERTS{alertname=\"Deployment\"}",
  "tagKeys": "deployment,version",
  "textKeys": "message"
}
```

#### Example: Overlay Deployments

```json
{
  "annotations": {
    "list": [
      {
        "builtIn": 0,
        "datasource": "Prometheus",
        "enable": true,
        "expr": "deployment_timestamp",
        "iconColor": "blue",
        "name": "Deployments",
        "tagKeys": "service,version"
      }
    ]
  }
}
```

### Grafana Alerting

#### Alert Rule

```json
{
  "uid": "api_error_rate",
  "title": "High Error Rate",
  "condition": "A",
  "data": [
    {
      "refId": "A",
      "queryType": "",
      "relativeTimeRange": {"from": 300, "to": 0},
      "datasourceUid": "prometheus-uid",
      "expression": "(rate(http_errors_total[5m]) / rate(http_requests_total[5m])) > 0.05",
      "intervalMs": 1000,
      "maxDataPoints": 43200
    }
  ],
  "noDataState": "NoData",
  "execErrState": "Alerting",
  "for": "5m",
  "annotations": {
    "summary": "Error rate > 5%",
    "description": "{{ $value }}% errors"
  }
}
```

#### Notification Policy

```yaml
apiVersion: monitoring.coreos.com/v1alpha1
kind: AlertingPolicy
metadata:
  name: api-alerts
spec:
  receiver: api-team
  groupBy: ["alertname", "job"]
  groupWait: 10s
  groupInterval: 10s
  repeatInterval: 12h

  routes:
  - receiver: pagerduty
    match:
      severity: critical
    continue: true
  - receiver: slack-api
    match:
      team: api
```

### SLO Dashboards

#### Error Budget Burn Rate (Google SRE)

```json
{
  "title": "Error Budget Burn Rate (30-day)",
  "targets": [
    {
      "expr": "(\n  rate(http_errors_total{job=\"api\"}[5m])\n  /\n  rate(http_requests_total{job=\"api\"}[5m])\n) / 0.01",
      "legendFormat": "Burn rate (1% error budget)"
    }
  ]
}
```

#### Multi-Window Multi-Burn-Rate Alerts

```yaml
alerts:
- alert: HighBurnRate5m
  expr: burn_rate_5m > 36  # 36x budget = 100% gone in 30 days
  for: 5m

- alert: HighBurnRate1h
  expr: burn_rate_1h > 6   # 6x budget = 100% gone in 5 days
  for: 1h

- alert: HighBurnRate6h
  expr: burn_rate_6h > 1   # 1x budget = 100% gone in 30 days
  for: 6h
```

### Dashboard-as-Code (Grafonnet)

#### Basic Dashboard with Grafonnet (Jsonnet)

```jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local prometheus = grafana.prometheus;

grafana.dashboard.new(
  title='API Service Health',
  description='RED method dashboard for API service',
  timezone='browser',
  time=grafana.time.range('now-6h', 'now'),
)
.addPanel(
  grafana.timeseries.new(
    title='Request Rate',
    datasource='Prometheus',
    targets=[
      prometheus.target(
        expr='rate(http_requests_total{job="api"}[5m])',
        legendFormat='{{ endpoint }}',
      ),
    ],
  ),
  gridPos={h: 8, w: 12, x: 0, y: 0},
)
.addPanel(
  grafana.stat.new(
    title='Error Rate',
    datasource='Prometheus',
    targets=[
      prometheus.target(
        expr='(rate(http_errors_total{job="api"}[5m]) / rate(http_requests_total{job="api"}[5m])) * 100',
      ),
    ],
    unit='percent',
  ),
  gridPos={h: 4, w: 6, x: 12, y: 0},
)
```

#### Grafonnet with Variables

```jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local variable = grafana.template;

grafana.dashboard.new()
  .addTemplate(
    variable.new(
      name='job',
      datasource='Prometheus',
      query='label_values(up, job)',
      current='api',
      multi=false,
    )
  )
  .addTemplate(
    variable.new(
      name='instance',
      datasource='Prometheus',
      query='label_values(up{job="$job"}, instance)',
      current='',
      multi=true,
    )
  )
  .addPanel(
    grafana.timeseries.new(
      title='Request Rate',
      targets=[
        prometheus.target('rate(http_requests_total{job="$job",instance=~"$instance"}[5m])'),
      ],
    ),
  )
```

#### Terraform Grafana Provider

```hcl
terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
  }
}

provider "grafana" {
  url  = "http://grafana:3000"
  auth = var.grafana_api_token
}

resource "grafana_dashboard" "api_health" {
  config_json = jsonencode({
    title       = "API Service Health"
    timezone    = "browser"
    panels = [
      {
        title      = "Request Rate"
        type       = "timeseries"
        datasource = "Prometheus"
        targets = [
          {
            expr           = "rate(http_requests_total{job='api'}[5m])"
            legendFormat   = "{{ endpoint }}"
            refId          = "A"
          }
        ]
      }
    ]
  })
}
```

### Dashboard Anti-Patterns

```
ANTI-PATTERN 1: Too Many Panels
- 30+ panels on one dashboard → overwhelming, slow to load
- Solution: Focus on RED or USE method (3-5 key metrics)

ANTI-PATTERN 2: No Templating (Hardcoded Values)
- Query: rate(http_requests_total{instance="api1:8080"}[5m])
- Can't reuse dashboard for other instances
- Solution: Use variables: {instance="$instance"}

ANTI-PATTERN 3: Alerting on Everything
- Alert on every metric change → alert fatigue
- Solution: Alert on actionable metrics (error rate > 5%, not CPU > 80%)

ANTI-PATTERN 4: No Context (Missing Time Range)
- Metric value without trend → can't tell if normal
- Solution: Use time series with 6h-24h context

ANTI-PATTERN 5: Metrics Without Thresholds
- Panels don't show what's "bad" → hard to interpret
- Solution: Add thresholds, color zones (green/yellow/red)

ANTI-PATTERN 6: Loki Queries Without Metrics
- Log volume → expensive to query, slow dashboard
- Solution: Use metrics (Prometheus) for trending, Loki for investigation

ANTI-PATTERN 7: Not Correlating Signals
- Separate dashboards for metrics, logs, traces
- Can't connect error spike to slow span
- Solution: Use annotations, cross-datasource links

ANTI-PATTERN 8: High-Cardinality Panels
- Panel with 1000+ time series → illegible
- Solution: Use topk() to limit results, aggregate labels
```

## Agent Support

- **observability-engineer** — System design, SLO strategy, alerting architecture, dashboard strategy
- **prometheus-expert** — PromQL optimization, performance tuning

## Skill References

- **observability-engineer** — Correlating traces with metrics, Tempo integration for trace visualization
