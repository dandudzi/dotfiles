---
name: cost-optimization
description: Cloud cost visibility and optimization strategies for compute, storage, networking, and databases. Covers tagging, auto-scaling, resource rightsizing, FinOps practices, and cost allocation models.
origin: ECC
---

# Cost Optimization

Practical strategies for visibility, rightsizing, and reducing cloud spend across AWS, GCP, and Azure.

## When to Activate

- Implementing cost visibility and tagging strategy
- Optimizing compute costs (instances, containers, serverless)
- Tuning auto-scaling policies and reserved capacity
- Evaluating storage tiers and lifecycle policies
- Reducing network egress costs
- Database cost optimization (RDS, DynamoDB, Firestore)
- Running FinOps process (cost allocation, chargeback)
- Setting up cost anomaly detection
- Kubernetes cluster cost optimization

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

**AWS Cost Explorer:**
```bash
# Console: Services → Cost Explorer
# Dashboard: Group by Tag → filter by Team
# Report: Daily costs by service, trend analysis
# Budget alerts: email when spending exceeds threshold
```

**GCP Billing:**
```bash
# Console: Billing → Reports
# Filter by label (team, project)
# Set up BigQuery export for custom analysis
# Programmatic: `gcloud billing budgets`
```

**Azure Cost Management:**
```bash
# Portal: Cost Management + Billing → Cost Analysis
# Group by Resource Group, Tag, Service
# Advisors: Recommendations for rightsizing, reserved instances
```

### Cost Allocation Model (Chargeback)

```yaml
# Show back cost to teams
monthly_cost_per_team = (resource_cost * tag_percentage)

Example:
  API Team Prod Costs:
  - EC2 (prod-api-*): $2,500
  - RDS (prod-api-db): $1,200
  - CloudFront (prod-assets): $800 shared with Frontend
  ────────────────────────────────
  Monthly Bill: $4,500

  Chargeback breakdown:
  - Compute: $2,500 (100% API Team)
  - Database: $1,200 (100% API Team)
  - CDN: $400 (50% API Team, tagged by both teams)
  = Total: $4,100
```

## Compute Optimization

### Instance Sizing: On-Demand vs Commitment

**Use On-Demand for:**
- Development and test environments
- Variable or unpredictable workloads
- New services with unknown capacity needs

**Use Reserved Instances / Savings Plans:**
- Baseline production load (predictable minimum)
- 1-year or 3-year commitment = 30-60% savings

**Use Spot / Preemptible:**
- Batch jobs, CI/CD, non-critical services
- Tolerance for 2-5 minute interruption
- Additional 70% savings vs on-demand

**Right-Sizing Formula:**
```
Recommendation = Peak CPU 70th percentile + 20% headroom
Example: EC2 t3.xlarge at 15% CPU → downsize to t3.small
Savings: $150/month × 12 months = $1,800/year per instance
```

### AWS Compute Commitment

```
+─────────────────────────────────────────────────────────────+
│ On-Demand: $0.42/hour (m6i.large)                          │
│ RI 1-yr: $0.25/hour (40% discount)                         │
│ RI 3-yr: $0.20/hour (52% discount)                         │
│ Savings Plan 1-yr: $0.26/hour (flexible instance type)     │
│ Savings Plan 3-yr: $0.21/hour                              │
│ Spot: $0.13/hour (70% discount, 2-5min notice)             │
│                                                             │
│ Recommendation: Mix Reserved (70%) + Spot (30%)            │
│ baseline load on RI, spike capacity from Spot              │
+─────────────────────────────────────────────────────────────+
```

**AWS CLI: Cost Analysis**
```bash
# Get instance usage and cost
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=INSTANCE_TYPE,Key=PURCHASE_TYPE \
  --filter file://filter.json

# filter.json
{
  "Tags": {
    "Key": "Environment",
    "Values": ["prod"]
  }
}

# Output: On-Demand cost vs Reserved usage gaps
```

### GCP Compute Commitment

```yaml
Commitment Tiers (1 or 3 year):
  n2-standard-4: $0.21/hour (3-year = 70% discount)
  n2-standard-4 On-Demand: $0.25/hour

Recommendations:
  - Committed use discounts (CUDs): stable production workloads
  - Preemptible VMs (70% discount): batch, non-critical services
  - Sustained use discounts (SUDs): automatic for >25% monthly usage
```

**GCP CLI:**
```bash
# Identify optimization opportunities
gcloud compute instances list \
  --format='table(name, machineType.machine_type(), cpuPlatform, status)' \
  --filter='status=RUNNING'

# Check CPU utilization
gcloud monitoring time-series list \
  --filter='metric.type=compute.googleapis.com/instance/cpu/utilization AND resource.labels.instance_id:INSTANCE_ID'
```

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
# Use nodepool with spot instances for stateless workloads
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
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: [batch-processor]
              topologyKey: kubernetes.io/hostname
            weight: 100
```

**Cost Projection:**
```
10 replicas × $0.15/hour (spot) = $1.50/hour
vs 10 × $0.50/hour (on-demand) = $5.00/hour
Monthly savings: $2,520 (45 days × 24 hours × $2.50)
```

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

**Cost Calculation:**
```
Input: 100GB of logs per month, average age 6 months
- Month 1-3: S3 Standard = 100 × $0.023 × 3 = $6.90
- Month 4-6: S3 Glacier = 200 × $0.004 × 3 = $2.40
- Month 7+: S3 Deep Archive = 100 × $0.001 × 12 = $1.20
Annual cost: ~$45 with intelligent tiering
Without tiering: 600GB × $0.023 × 12 = $165.60
Savings: $120.60/year (73% reduction)
```

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

```sql
-- Find actual peak CPU usage (CloudWatch / Cloud SQL Insights)
SELECT
  db_instance,
  MAX(cpu_util) as peak_cpu,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY cpu_util) as p99_cpu
FROM cloudwatch_metrics
WHERE date > CURRENT_DATE - 30
GROUP BY db_instance;

-- If peak <20%: downsize 1-2 instance types (m6i.large → m6i.xlarge)
-- If peak >80%: consider read replica to split read traffic
```

**Aurora Serverless v2 vs Provisioned:**

```yaml
Provisioned RDS:
  - m6i.large: $0.42/hour = $306/month
  - Reserved 1-yr: $0.25/hour = $180/month
  - Assume 30% average CPU = $54/month unused capacity

Aurora Serverless v2:
  - Scale: 0.5 to 4 ACUs (1 ACU ≈ 2GB RAM)
  - Pricing: $0.06/ACU-hour (peak) + $0.006/ACU-hour (idle)
  - Avg load: 1 ACU = $0.06 × 730 × 1 = $43.80/month
  - Savings: $136/month vs provisioned

Recommendation:
  - Predictable steady load: Provisioned + Reserved (40% discount)
  - Bursty/variable: Serverless v2 (save 50-70% vs provisioned)
  - Dev/test: Aurora Serverless v2 + auto-pause after 5min idle
```

**Read Replicas (Only When Needed):**

```
WRONG:
  - Create read replicas for every 10% CPU increase
  - Cost: 2× database expense immediately

RIGHT:
  1. Optimize queries (indexes, query plan)
  2. Add read cache (Redis/ElastiCache)
  3. Only add read replica if queries still >80% CPU
  4. Read replicas for read-heavy (>90% reads), not write-heavy workloads

Cost comparison:
  Primary RDS m6i.xlarge: $600/month
  Add 1 read replica: $600 + $600 = $1,200/month
  vs ElastiCache t4g.small: $40/month (99% hit rate reduces DB load)
```

### DynamoDB / Firestore Optimization

**DynamoDB Billing Modes:**

```yaml
Provisioned Mode:
  - Fixed RCU/WCU capacity (pay always, even when idle)
  - Useful: predictable traffic, can burst with autoscaling
  - Example: 100 RCU + 50 WCU = $50 + $25 = $75/month

On-Demand Mode:
  - Pay per request: $1.25 per million RCU, $6.25 per million WCU
  - Example: 100M RCU + 30M WCU = $125 + $187.50 = $312.50/month
  - Useful: variable traffic, spiky workloads, new services

Comparison:
  - Steady 100 RCU/month → Provisioned ($75/month)
  - Spiky 10x variance → On-Demand (autoscale cost, reduce overprovisioning)
  - Break-even: calculate monthly cost for both modes
```

**Firestore Cost Optimization:**

```yaml
Billing:
  Reads: $0.06 per 100K reads
  Writes: $0.18 per 100K writes
  Deletes: $0.02 per 100K deletes
  Storage: $0.18 per GB/month

Cost reduction:
  1. Batch writes (500K writes: 5 ops vs 500K ops = 100x cost reduction)
  2. Denormalize frequently accessed data (avoid N+1 reads)
  3. Archive old collections to Cloud Storage ($0.020/GB/month)

Example:
  Before: 1M reads + 100K writes/month = $60 + $18 = $78/month
  After batching + denormalization: 500K reads + 50K writes = $30 + $9 = $39/month
  Annual savings: $468
```

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

```
Scenario: 3 AZs, 1 NAT gateway per AZ = 3 × $32/month + $0.45/GB processed

Example: 100GB processed/month
  - NAT cost: $96 + (100 × $0.45) = $141/month

Optimization:
  1. Consolidate to 1 NAT (lose AZ failover, save $64/month)
  2. Use NAT instance (EC2 t3.nano $3 + traffic cost)
  3. Use VPC endpoints for S3/DynamoDB (free, eliminates NAT traffic)
     - Measure: 50% of traffic to S3 → VPC endpoint saves $22.50/month
```

**VPC Endpoint Cost (AWS):**

```yaml
Gateway Endpoint (S3, DynamoDB):
  - Cost: Free
  - Use: All S3/DynamoDB access goes through endpoint (free)
  - Setup: 5 minutes

Interface Endpoint (other AWS services):
  - Cost: $7.20/endpoint/month + $0.01/million requests
  - Use: EC2, SNS, SQS, Secrets Manager, etc.
  - ROI: Break-even at $400/month NAT egress savings

Recommendation:
  - S3/DynamoDB: Always use gateway endpoint (free)
  - Other services: Use endpoint if >$50/month NAT savings
```

## FinOps Process

### Monthly Cost Review Workflow

```
1. Pull cost report (Cost Explorer / Cloud Billing)
2. Group by team, service, environment
3. Identify top 5 cost drivers
   - Is this expected? Any anomalies?
   - Compare month-over-month
4. Set optimization targets
   - Example: 10% reduction in compute for dev environment
5. Assign ownership and track progress
```

### Anomaly Detection & Alerts

**AWS Budgets:**

```
Budget: $10,000/month
Alert 1: Notify when >80% ($8,000 spent) - early warning
Alert 2: Notify when >100% ($10,000 spent) - hard limit
Alert 3: Notify when >125% ($12,500 spent) - escalate

Budget Rules (Auto-response):
  - Stop untagged instances if spend >threshold
  - Disable auto-scaling if trend > forecast
```

**GCP Budget Alerts:**

```bash
gcloud billing budgets create \
  --billing-account=ACCOUNT_ID \
  --display-name="prod-monthly-budget" \
  --budget-amount=15000 \
  --threshold-rule percent=50,behavior=ALERT \
  --threshold-rule percent=100,behavior=ALERT
```

**CloudWatch Cost Anomaly Detection (ML-based):**

```
Automatically detects spending spikes:
  - Baseline: Average spend + historical variance
  - Alert: Spend deviates >2σ (95% confidence)
  - Eliminates false positives (predictable seasonal spikes)
```

## Anti-Patterns

### Cost Anti-Pattern 1: Over-Provisioning Without Monitoring

```
WRONG:
  - EC2 m6i.4xlarge (16 CPU, 64GB) for app averaging 10% CPU
  - Leftover capacity wasted, 90% of cost unused
  - Multiply by 50 instances = $180K wasted annually

RIGHT:
  - Monitor CPU, memory, network for 2 weeks
  - Right-size to m6i.large (2 CPU, 8GB)
  - Review quarterly, downsize if still <20% usage
  - Use auto-scaling to handle spike without permanent overprovisioning
```

### Cost Anti-Pattern 2: Ignoring Data Transfer Costs

```
WRONG:
  - Replicate 500GB database across 3 regions quarterly (testing)
  - Cross-region transfer: 500GB × $0.02 = $10K per copy × 4/year = $40K

RIGHT:
  - Use database snapshots (1 copy, stored in S3)
  - Restore from snapshot to test region (free within region)
  - Delete after testing (1-day lifecycle)
  - Cost: $3.60 (1 snapshot in S3) + $20 (test instance, 1 day)
```

### Cost Anti-Pattern 3: Multiple NAT Gateways Without Traffic Analysis

```
WRONG:
  - NAT gateway per AZ (HA assumption): 3 × $32 + data costs = $300+/month
  - Most traffic in 1 AZ; others idle

RIGHT:
  - Analyze traffic per AZ (VPC Flow Logs)
  - If <10% traffic in AZ-c: remove NAT gateway there
  - Consolidate to 2 NAT gateways: save $32/month
  - Use read replicas / cross-region to reduce NAT traffic
```

### Cost Anti-Pattern 4: Reserved Instances for Unpredictable Workloads

```
WRONG:
  - Buy 1-year RI for dev environment (developers spin up/down)
  - 60% of RI unused, no refunds

RIGHT:
  - On-demand for dev (flexibility > savings)
  - RI for stable prod baseline (60% discount)
  - Savings Plans for flexible instance types (30% discount)
  - Spot for non-critical batch workloads (70% discount)
```

### Cost Anti-Pattern 5: Orphaned Resources

```
WRONG:
  - Terminate EC2 instance but leave EBS volume (persists)
  - Delete RDS instance but forget read replicas
  - Stop EC2 but forget attached Elastic IP ($3.60/month charge)

RIGHT:
  - Script to find unattached resources monthly
    aws ec2 describe-volumes --filter Name=status,Values=available
  - Tag resources with "delete-date" and auto-cleanup after 30 days
  - Audit stopped instances monthly; terminate if not needed
```

## Agent Support

- Delegate cluster cost optimization to **kubernetes-architect** for right-sizing nodes, Spot strategies, and pod density
- Coordinate with **cloud-architect** for multi-region cost implications and reservation strategies
- Consult **sql-expert** for database indexing and query optimization to reduce compute costs

## Skill References

- Reference `deployment-patterns` skill for CI/CD cost reduction (spot runners, container reuse)
- Use cloud provider CLI guides above as operational checklist
