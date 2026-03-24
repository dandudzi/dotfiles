---
name: cost-optimization
description: Cloud cost visibility and optimization strategies for compute, storage, networking, and databases. Covers tagging, auto-scaling, resource rightsizing, FinOps practices, and cost allocation models.
origin: ECC
model: sonnet
---

# Cost Optimization

## When to Activate

- Implementing tagging strategy and cost visibility
- Optimizing compute (instances, containers, reservations, autoscaling)
- Optimizing storage tiers, networks, and databases

## Cost Visibility Foundation

### Mandatory Tagging Strategy

Every cloud resource must have these tags:

```yaml
Environment: dev|staging|prod
Team: platform|product|data
Service: api|frontend|database|queue
CostCenter: department identifier
Project: product or initiative name
ManagedBy: terraform|helm|manual
Owner: team or person responsible
```

**Enforcement:**
- AWS: Organizations policy to deny untagged resource creation
- GCP: Label enforcement via IAM condition
- Azure: Azure Policy for tag requirements

### Cost Explorer & Reports

**AWS:** Services → Cost Explorer, group by tags, set budget alerts.
**GCP:** Billing → Reports, export to BigQuery, use `gcloud billing budgets`.
**Azure:** Cost Management + Billing → Cost Analysis, use advisors for rightsizing.

### Cost Allocation Model (Chargeback)

```yaml
monthly_cost_per_team = (resource_cost * tag_percentage)
# Tag resources by owner; aggregate via Cost Explorer filters
```

## Compute Optimization

### Instance Sizing: On-Demand vs Commitment

**On-Demand:** dev/test, variable workloads.
**Reserved (1-3yr):** prod baseline, 30–60% savings.
**Spot/Preemptible:** batch/CI, 70% savings, 2–5min interruption.

Right-size to 70th percentile CPU + 20% headroom. Example: t3.xlarge at 15% → t3.small, save $1,800/year.

### AWS Compute Commitment

On-Demand: $0.42/hr. RI 1-yr: $0.25 (40%). RI 3-yr: $0.20 (52%). Spot: $0.13 (70%). Recommendation: 70% RI + 30% Spot.

**AWS CLI:** `aws ce get-cost-and-usage --group-by Type=INSTANCE_TYPE,Key=PURCHASE_TYPE` to analyze on-demand vs reserved gaps.

### GCP Compute Commitment

CUDs (1-3yr): 70% discount. Preemptible VMs: 70% discount, batch/non-critical. SUDs: automatic for >25% monthly use.

**GCP CLI:** `gcloud compute instances list` + `gcloud monitoring time-series list` to find CPU utilization and rightsizing opportunities.

### Container & Kubernetes Optimization

**Cluster Autoscaler / Karpenter:**
```yaml
Cluster Autoscaler settings:
  scale_down_enabled: true
  scale_down_delay_after_add: 10m
  scale_down_delay_after_failure: 3m
  scale_down_utilization_threshold: 0.65  # scale down if <65% used

Cost savings: Remove 20-30% of idle nodes in dev/test clusters
```

**Pod Resource Requests (Scheduler Bin-Packing):**
```yaml
# GOOD: Tight requests allow scheduler to pack pods efficiently
Pod A:
  requests: {cpu: 100m, memory: 128Mi}
  limits: {cpu: 500m, memory: 256Mi}

# BAD: Over-requested wastes capacity
Pod B:
  requests: {cpu: 2000m, memory: 4Gi}  # 10x actual usage
  limits: {cpu: 4000m, memory: 8Gi}

# Result: Pod A allows 2x pods per node; Pod B wastes 80% capacity
```

**Spot in Kubernetes:**
```yaml
# Use spot nodepool for stateless workloads
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
spec:
  replicas: 10
  template:
    spec:
      nodeSelector:
        cloud.google.com/gke-nodepool: spot-pool
      tolerations:
      - key: cloud.google.com/gke-preemptible
        operator: Equal
        value: "true"
        effect: NoSchedule
```

Cost: 10 replicas × $0.15/hr (spot) = $1.50/hr vs $5/hr on-demand. Saves $2,520/month.

## Storage Optimization

### S3 / Cloud Storage Tiering

**AWS S3 Storage Classes:**

```yaml
S3 Standard:
  cost: $0.023/GB/month
  use: frequently accessed data (default)

S3 Standard-IA (Infrequent Access):
  cost: $0.0125/GB/month + $0.01/1000 requests
  use: backup, logs accessed <once/month
  savings: 46% vs Standard if <2x retrieval cost

S3 Intelligent-Tiering:
  cost: $0.0025/1000 objects monitored (auto-moves to cheaper tier)
  use: unknown access patterns, set-and-forget

S3 Glacier Instant:
  cost: $0.004/GB/month
  retrieval: <1ms (for compliance holds, rare access)

S3 Glacier Flexible:
  cost: $0.0036/GB/month
  retrieval: 1-5 minutes ($0.03/GB retrieval cost)
  use: archives, legal hold, annual tax records

S3 Deep Archive:
  cost: $0.00099/GB/month
  retrieval: 12+ hours ($0.02/GB cost)
  use: 7+ year retention, rarely accessed
```

**S3 Intelligent-Tiering Configuration:**

```json
{
  "Id": "auto-tier-policy",
  "Filter": {"Prefix": "logs/"},
  "Status": "Enabled",
  "Tierings": [
    {
      "Days": 90,
      "AccessTier": "ARCHIVE_ACCESS"
    },
    {
      "Days": 180,
      "AccessTier": "DEEP_ARCHIVE_ACCESS"
    }
  ]
}
```

**Cost Example:** 100GB logs/month → Standard (3mo) + Glacier (3mo) + Deep Archive (6mo) = $45/year vs $166/year untiered (73% savings)

**Lifecycle Policy (Terraform):**

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "cost_opt" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "archive-old-logs"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years
    }
  }
}
```

**GCP Cloud Storage Tiers:**

```yaml
Standard:
  cost: $0.020/GB/month
  use: high-access, temporary data

Nearline:
  cost: $0.010/GB/month + retrieval fee
  use: accessed monthly or less

Coldline:
  cost: $0.004/GB/month + retrieval fee
  use: accessed quarterly or less (3-month minimum)

Archive:
  cost: $0.0012/GB/month + retrieval fee
  use: accessed <1/year (legal, compliance hold, backups)
```

## Database Cost Optimization

### RDS / Cloud SQL Optimization

**Right-Size Database Instances:**

Query CloudWatch/Cloud SQL Insights for peak CPU. If peak <20%, downsize. If >80%, add read replica.

**Aurora Serverless v2 vs Provisioned:**

Provisioned m6i.large: $306/month. Serverless v2: 1 ACU $43.80/month. Use provisioned for steady load (40% RI discount), serverless v2 for bursty (50–70% savings). Dev: serverless v2 with auto-pause.

**Read Replicas (Only When Needed):**

1. Optimize queries/indexes, 2. add read cache (ElastiCache), 3. add replica only if >80% CPU. ElastiCache t4g.small ($40/month) vs read replica ($600/month).

### DynamoDB / Firestore Optimization

**DynamoDB Billing Modes:**

Provisioned: fixed RCU/WCU, $75/month for 100 RCU + 50 WCU. On-Demand: $1.25/million RCU, use for spiky workloads. Calculate break-even for both modes.

**Firestore Cost Optimization:**

Reads $0.06/100K, writes $0.18/100K. Batch writes (100x cost reduction), denormalize data, archive to Cloud Storage. Example: 1M reads + 100K writes ($78) → 500K reads + 50K writes ($39) = $468/year savings.

## Network Cost Optimization

### Data Transfer Pricing

**AWS Data Transfer (Per Region Pair):**

```
Ingress:     Free
Egress within region: Free (same AZ) / $0.01/GB (cross-AZ)
Egress to internet: $0.09/GB (first 1GB free)
Egress to another region: $0.02/GB
```

**Cost Optimization:**

```yaml
Problem: Instances in us-east-1a and us-east-1b
  - 10TB cross-AZ per month = 10,000 × $0.01 = $100/month

Solution 1: Place in same AZ
  - Cost: $0 (but less HA)

Solution 2: Use VPC Endpoint for S3
  - Cost: $7.20 (VPC endpoint) + free S3 access in same region
  - Savings: $20/month for 2TB egress to S3

Solution 3: Use CloudFront for static assets
  - Origin egress: $0.085/GB (slightly cheaper)
  - CloudFront to internet: $0.085/GB
  - Cost break-even at >1TB/month egress
  - Benefit: 50ms latency improvement globally
```

**NAT Gateway Cost Analysis:**

3 AZs = 3 × $32/month + $0.45/GB. Consolidate if uneven traffic (save $32+/month). Use gateway endpoints for S3/DynamoDB (free).

**VPC Endpoint:** Gateway (free for S3/DynamoDB). Interface ($7.20/month + $0.01/million requests). ROI at >$50/month NAT savings.

## FinOps Process

### Monthly Cost Review Workflow

Pull cost report, group by team/service, identify top 5 drivers (compare M/M), set targets (e.g., 10% dev compute reduction), assign ownership.

### Anomaly Detection & Alerts

**AWS Budgets:** Set alerts at 50%, 80%, 100%. Auto-responses: stop untagged resources, disable autoscaling if over forecast.
**GCP:** `gcloud billing budgets create --threshold-rule percent=50,100`.
**CloudWatch Anomaly:** ML-based detection alerts on spend >2σ (95% confidence).

## Anti-Patterns

### Cost Anti-Pattern 1: Over-Provisioning Without Monitoring

Monitor 2 weeks, right-size to 70th percentile CPU + 20% headroom. Example: m6i.4xlarge at 10% CPU → downsize to m6i.large, save $180K/year (50 instances).

### Cost Anti-Pattern 2: Ignoring Data Transfer Costs

Use snapshots + cross-region restore, not full replication. Snapshot ($3.60) + test instance (1 day, $20) vs 500GB cross-region copy ($10K).

### Cost Anti-Pattern 3: Multiple NAT Gateways Without Traffic Analysis

Analyze VPC Flow Logs; consolidate to 1-2 NAT gateways if traffic uneven. Save $32–64/month.

### Cost Anti-Pattern 4: Reserved Instances for Unpredictable Workloads

Use on-demand for dev (flexibility), RI for stable prod (60% discount), Spot for batch (70% discount).

### Cost Anti-Pattern 5: Orphaned Resources

Script monthly cleanup: unattached volumes, orphaned replicas, unused Elastic IPs. Tag with "delete-date", auto-cleanup after 30 days.

## Agent Support

Delegate cluster cost optimization to **cloud-architect** for node rightsizing and Spot strategies. Consult **sql-expert** for query optimization.
