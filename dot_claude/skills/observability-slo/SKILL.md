---
name: observability-slo
description: >
  SLI/SLO definition, error budgets, burn rate alerting, and SLO-driven incident response.
  Use when defining service objectives, calculating error budgets, or responding to budget depletion.
model: sonnet
---

# SLI/SLO Framework

Trigger on: "SLO", "SLI", "error budget", "burn rate", "service level".

## Core Definitions

**SLI** (Service Level Indicator): Quantitative measure of service behaviour (request latency p99, error rate, availability).

**SLO** (Service Level Objective): Target value for an SLI over a time window (99.9% of requests complete in <200ms over 28 days).

**Error Budget**: Allowed unreliability = 100% − SLO target. A 99.9% SLO permits 0.1% downtime.

## SLI Selection by Service Type

| Service Type | Primary SLI | Secondary SLI |
|-------------|------------|---------------|
| User-facing API | Request success rate | p99 latency |
| Data pipeline | Freshness (data age) | Completeness rate |
| Async worker | Task success rate | Processing latency |
| Storage system | Durability | Read latency |

## Error Budget Calculation and Burn Rate

### Formula

```
# 28-day error budget
Total minutes = 28 × 24 × 60 = 40,320
Error budget minutes = 40,320 × (1 - SLO_target)

# For 99.9% SLO:
Error budget minutes = 40,320 × 0.001 = 40.32 minutes

# Burn rate ratio
burn_rate = error_rate / (1 - SLO_target)
```

### Burn Rate Interpretation

Burn rate > 1 means consuming budget faster than allowed. Burn rate = 14.4 means budget exhausted in 2 hours (40.32 min / 14.4 = 2.8 hours).

### Detailed Walkthrough

```
Service: payment-api
SLO: 99.9% success over 28 days
Error budget: 40.32 minutes

Current error rate: 0.005 (0.5%)
Burn rate = 0.005 / 0.001 = 5×

Interpretation:
- Consuming budget 5× faster than allowed
- Budget exhausted in 40.32 / 5 = 8 hours
- Page on-call immediately (SLO at risk)
```

## Alerting Thresholds by Burn Rate

| Burn Rate | Budget Exhausted | Action |
|-----------|------------------|--------|
| 14.4× | 1 hour | Critical: Page immediately |
| 6× | 6 hours | High: Page on-call |
| 3× | 3 days | Medium: Ticket (this sprint) |
| 1× | 28 days | Normal (no alert) |

**Alert rule (Prometheus)**:
```yaml
- alert: BudgetBurnCritical
  expr: |
    (sum(rate(http_requests_total{status=~"5.."}[5m])) /
    sum(rate(http_requests_total[5m]))) / 0.001 > 14.4
  for: 5m
  labels:
    severity: critical
```

## SLO-Driven Incident Response

1. **Identify**: Which SLI violated? What's the error rate?
2. **Quantify**: Calculate burn rate. Compare against thresholds.
3. **Escalate**: If burn rate > 6×, page on-call immediately.
4. **Remediate**: Focus on restoring service, not preventing future SLO violations.
5. **Post-incident**: Only if error budget depleted — review why SLO was missed.

## Budget Management

- **Reserve at start of period**: Keep 20% in reserve for unexpected failures.
- **Monitor throughout**: Track cumulative error rate daily.
- **Warn at 50%**: Alert when half of monthly budget consumed.
- **Stop new deploys at 100%**: No risky changes once budget exhausted.
- **Review at end**: Analyze how budget was consumed; adjust SLO if needed.

## Anti-Patterns

❌ SLO too loose (99% = 3.6 hours downtime/month) — causes alert fatigue from normal events.

❌ SLO too tight (99.99% = 4 min/month) — impossible to maintain; demoralizes team.

❌ Single SLI per service — must combine availability + latency + correctness.

❌ No error budget tracking — burns surprise.

❌ Freezing deploys on every SLO miss — prevents learning. Use error budget, not incidents.
