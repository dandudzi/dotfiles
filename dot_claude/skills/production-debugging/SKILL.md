---
name: production-debugging
description: Systematic debugging methodology, log analysis, metrics correlation, distributed tracing, and live debugging tools for production issues.
origin: ECC
---

# Production Debugging

## When to Activate

- Diagnosing production incidents with incomplete information
- Correlating logs, metrics, and traces to pinpoint root cause
- Querying structured logs with LogQL, Elasticsearch DSL, or CloudWatch Insights
- Analyzing database performance and lock contention
- Profiling memory, CPU, and goroutine leaks in production
- Making rollback vs fix-forward decisions
- Building hypothesis-driven debugging workflows

## Core Methodology

### Hypothesis-Driven Debugging Loop

1. **Form hypothesis**: Based on recent changes (deployment, config, traffic pattern)
2. **Gather evidence**: Query logs, metrics, traces by timestamp range
3. **Validate/refute**: Does evidence support hypothesis?
4. **Narrow scope**: If refuted, repeat with new hypothesis
5. **Confirm**: Once hypothesis validated, implement mitigation

**Never change multiple things at once.** Isolate each change to understand its effect.

## Structured Log Querying

### LogQL (Loki) Examples

```logql
# Find errors in last hour
{job="api-server"} |= "error" | json | level="error"

# Count 500 errors by service
sum by (service) (count_over_time({job=~"api|worker"} |= "500" [1m]))

# Trace request through service
{job=~"api|db"} | json | trace_id="abc123" | order by timestamp

# Latency p95 per endpoint
histogram_quantile(0.95, rate({job="api"} | json [1m]))
```

### Elasticsearch DSL

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "error" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "by_service": {
      "terms": { "field": "service.keyword" }
    }
  }
}
```

### CloudWatch Insights

```
fields @timestamp, @message, @duration
| filter @message like /error/
| stats count() as errors, avg(@duration) as avg_latency by service
| sort errors desc
```

## Metrics Correlation

### Timeline Alignment

Overlay deployment annotations on metrics graphs:
- Deployment start time
- Canary threshold breaches
- Rollback initiation
- All-clear signal

### Key Metrics During Incident

- **Error rate**: Request errors per second; 5xx vs 4xx
- **Latency**: p50, p95, p99 (tail latency indicates bottleneck)
- **Saturation**: CPU %, memory %, disk I/O, connection pool utilization
- **Business KPIs**: Transactions per second, conversion rate, revenue impact

### Divergence Detection

```
# Before deployment: p99 latency = 200ms
# After deployment: p99 latency = 500ms, error_rate = 0.1%
→ Recent change caused regression
```

## Distributed Trace Analysis

### Identifying Slow Spans

Trace structure:
```
Request starts → API gateway (5ms) → Auth service (100ms) → DB query (800ms) → Response
                                                             └─ BOTTLENECK
```

Tools: Jaeger, Zipkin, AWS X-Ray, OpenTelemetry

### Finding Error Propagation

Trace error from downstream (database timeout) back to upstream (API caller):
- Database timeout at span level
- API service retries (adds 1000ms)
- Caller receives 500 after 1.5s instead of 200ms response

### Upstream vs Downstream Blame

- **Upstream blame**: "My service is waiting for your slow response"
- **Downstream blame**: "Your service is sending me bad requests"

Traces show who's at fault.

## Live Debugging Tools

### Kubernetes

```bash
# SSH into pod
kubectl exec -it <pod> -- /bin/bash

# Stream logs with timestamps
kubectl logs -f <pod> --all-containers --tail=100

# Check resource requests vs actual usage
kubectl top pods
```

### Linux System Tools

```bash
# Process resource usage
top -p <pid>

# System call tracing
strace -e trace=network -f <process>

# Network connections and sockets
ss -tlnp | grep <port>
netstat -tulnp | grep <port>

# /proc inspection
cat /proc/<pid>/status          # Memory, threads, FDs
cat /proc/<pid>/limits          # Resource limits
cat /proc/<pid>/net/tcp         # TCP connections
```

### Profiling

```bash
# Python (py-spy, no restart needed)
py-spy record -o profile.svg -p <pid>

# JVM (async-profiler)
async-profiler record -d 30 -f <output.html> <pid>

# Go (pprof)
go tool pprof http://localhost:6060/debug/pprof/profile

# Node.js (Chrome DevTools)
node --inspect app.js
# Then open chrome://inspect
```

## Database Debugging

### Slow Query Log (PostgreSQL)

```sql
-- Enable slow query logging
SET log_min_duration_statement = 1000;  -- Log queries >1s

-- Query slow queries
SELECT query, mean_exec_time, calls
  FROM pg_stat_statements
 ORDER BY mean_exec_time DESC
 LIMIT 10;

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
```

### Lock Contention (PostgreSQL)

```sql
-- Find blocked queries
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
  FROM pg_catalog.pg_locks blocked_locks
  JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
  JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
  JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
 WHERE NOT blocked_locks.granted;
```

### Connection Pool

```bash
# PostgreSQL current connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Check pool exhaustion
SHOW max_connections;  # Server limit
SHOW pool_size;        # PgBouncer config
```

## Rollback Decision Matrix

| Signal | Keep | Rollback |
|--------|------|----------|
| Error rate spike immediately after deploy | Rollback | Rare |
| Gradual latency increase over hours | Investigate | Possible |
| Database migration incompatible | Rollback | Common |
| Customer-facing data loss | Rollback | Always |
| Business KPI decline | Evaluate | Usually |

**Rollback criteria**: Impact * Urgency > Investigation overhead

## Incident Timeline Template

```
14:05:00 UTC - Alert fired: error_rate > 5%
14:05:30 UTC - On-call acknowledged, SEV2 declared
14:06:00 UTC - Hypothesis: Recent deploy caused regression
14:06:30 UTC - Evidence: Error spike 3m after deploy, all errors in new code path
14:07:00 UTC - Action: Started canary rollback
14:07:45 UTC - Rollback complete, error rate back to baseline
14:15:00 UTC - All-clear signal
14:30:00 UTC - Postmortem scheduled

Action items:
- Add integration test for new code path
- Improve canary metrics dashboard
- Faster rollback automation
```

## Anti-Patterns

```python
# ANTI-PATTERN 1: Change multiple things, then debug
# Deploy code + config + DB migration, incident, unsure which caused it
# FIX: One change at a time with clear metrics per change

# ANTI-PATTERN 2: Delete logs/evidence during incident
# "Turn off verbose logging to save space"—now can't debug
# FIX: Preserve evidence first; analyze after mitigation

# ANTI-PATTERN 3: No timeline documentation
# "We fixed it but not sure exactly when or how"
# FIX: Timestamp every action and decision

# ANTI-PATTERN 4: Assuming change caused issue without evidence
# "Rollback because it deployed before incident"
# FIX: Correlate metrics; prove causation not just correlation

# ANTI-PATTERN 5: Debugging without hypothesis
# Randomly checking things, hoping for insight
# FIX: Form hypothesis, check evidence, narrow scope
```

## Agent Support

- **incident-responder** — Incident severity, triage, mitigation prioritization
- **python-expert** — Profiling Python services (py-spy, cProfile)
- **nodejs-expert** — Debugging Node.js with async-profiler and DevTools
- **sql-expert** — Query optimization and lock analysis
- **owasp-top10-expert** — Security aspects of incident response

## Skill References

- **incident-response-runbooks** — Specific runbook templates
- **kubernetes-debugging** — kubectl commands and container troubleshooting
- **observability-setup** — Metrics collection and trace instrumentation
