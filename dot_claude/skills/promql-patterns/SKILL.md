---
name: promql-patterns
description: >
  PromQL query patterns, dashboard design, templating, datasources, and Grafana panels.
  Use when building monitoring dashboards, writing queries, and designing visualizations.
model: sonnet
---

# PromQL Patterns

## When to Activate

- Writing PromQL queries for dashboards and alerts
- Designing Grafana dashboards using RED/USE methods
- Configuring dashboard variables and datasources
- Building SLO dashboards with error budgets
- Creating dashboard-as-code with Grafonnet or Terraform

## PromQL Basics

### Metric Types

**Counters** (always increasing): `rate()` to get rate of change.
```promql
rate(http_requests_total[5m])
increase(http_requests_total[1h])
```

**Gauges** (up or down): Use directly or calculate percentage.
```promql
node_memory_MemAvailable_bytes
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

**Histograms** (distributions): Use `histogram_quantile()` to extract percentiles.
```promql
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

## Essential Query Patterns

### Rate of Change
```promql
rate(http_requests_total[5m])
```

### Error Rate
```promql
sum by (job) (rate(http_errors_total[5m])) / sum by (job) (rate(http_requests_total[5m]))
```

### Percentile Latency
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Top N Results
```promql
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))
```

### Memory Usage Percentage
```promql
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

### Services Exceeding Threshold
```promql
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
```

### Label Extraction
```promql
label_replace(
  http_request_duration_seconds,
  "user_segment",
  "$1",
  "path",
  "^/users/([a-z]+)/.*"
)
```

### Aggregation Without Label
```promql
sum without (instance) (node_network_receive_bytes_total)
```

### Average Latency
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Memory Pressure Alert
```promql
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.8
```

## Grafana Dashboards

### RED Method (Services)

Monitor rate, errors, duration for every service.

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

### USE Method (Resources)

Monitor utilization, saturation, errors for CPU, memory, disk, network.

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

## Panel Types

### Time Series (Most Common)

For trending metrics over time. Rate, latency, errors.

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
      "unit": "rps"
    }
  }
}
```

### Stat (Single Number)

Current value with trend. Use for gauges: CPU%, memory, disk.

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

### Gauge (Radial)

Bounded metrics (0-100%) with color zones.

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

### Table

Display rows/columns. List services, errors, anomalies.

```json
{
  "type": "table",
  "title": "Service Status",
  "targets": [
    {
      "expr": "up{job=\"api\"}"
    }
  ]
}
```

### Heatmap

Show distributions and trends. Latency histograms (time X-axis, bucket Y-axis).

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

### Bar Chart

Compare values across categories. Errors by type, requests by endpoint.

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

## Templating Variables

### Datasource Variable

```json
{
  "name": "datasource",
  "type": "datasource",
  "datasource": "prometheus",
  "label": "Prometheus"
}
```

### Label Values Variable

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

### Chained Variables

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

### Use Variables in Queries

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

## Datasources

### Prometheus

```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy"
}
```

### Loki (Logs)

```json
{
  "name": "Loki",
  "type": "loki",
  "url": "http://loki:3100"
}
```

### Tempo (Traces)

```json
{
  "name": "Tempo",
  "type": "tempo",
  "url": "http://tempo:3100"
}
```

## LogQL Examples (Loki)

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

## Annotations (Deployments)

Add deployment annotations to dashboards:

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

## Grafana Alerting

### Alert Rule

```json
{
  "uid": "api_error_rate",
  "title": "High Error Rate",
  "condition": "A",
  "data": [
    {
      "refId": "A",
      "datasourceUid": "prometheus-uid",
      "expression": "(rate(http_errors_total[5m]) / rate(http_requests_total[5m])) > 0.05",
      "for": "5m"
    }
  ],
  "annotations": {
    "summary": "Error rate > 5%",
    "description": "{{ $value }}% errors"
  }
}
```

## SLO Dashboards

### Error Budget Burn Rate

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

### Multi-Window Burn Rate Alerts

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

## Dashboard-as-Code

### Grafonnet (Jsonnet)

```jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local prometheus = grafana.prometheus;

grafana.dashboard.new(
  title='API Service Health',
  description='RED method dashboard',
  timezone='browser',
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

### Terraform Grafana Provider

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
    title    = "API Service Health"
    timezone = "browser"
    panels = [
      {
        title      = "Request Rate"
        type       = "timeseries"
        datasource = "Prometheus"
        targets = [
          {
            expr         = "rate(http_requests_total{job='api'}[5m])"
            legendFormat = "{{ endpoint }}"
            refId        = "A"
          }
        ]
      }
    ]
  })
}
```

## Dashboard Anti-Patterns

**Too Many Panels**: 30+ panels → overwhelming. Use RED/USE method (3–5 key metrics per dashboard).

**Hardcoded Values**: Query with `instance="api1:8080"` can't reuse. Use `instance="$instance"` instead.

**Alerting on Everything**: Alert on every metric change → alert fatigue. Alert only on actionable metrics (error rate > 5%, not CPU > 80%).

**No Context**: Single value without trend line → can't tell if normal. Add time series with 6h–24h history.

**Missing Thresholds**: Panels don't show what's "bad". Add thresholds and color zones (green/yellow/red).

**Log Volume Queries**: Querying raw logs without metrics → slow, expensive. Use metrics (Prometheus) for trending, Loki for investigation only.

**Disconnected Signals**: Separate dashboards for metrics, logs, traces. Can't correlate error spike to slow span. Add annotations and cross-datasource links.

**High-Cardinality Panels**: 1000+ time series → illegible. Use `topk()` to limit, aggregate labels.

## Agent Support

- **observability-engineer** — Dashboard strategy, SLO design, trace integration
- **prometheus-expert** — PromQL optimization
