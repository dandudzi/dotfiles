---
name: job-posting-parse
description: Parse a LinkedIn URL, company careers-page URL, or pasted job posting into a complete, source-preserving structured packet. Use before storing, researching, comparing a CV, or recommending related roles.
---

# Parse a job posting

Extract evidence without initiating an application. Accept LinkedIn, a company careers page, or pasted text.

## Collect safely

Read the supplied page and expand in-page description controls where needed. Record visible source URLs, posting IDs, and timestamps. Follow a directly visible canonical careers-page link only when it is clearly a job-detail page.

Do not click Apply merely to scrape, begin an application, submit a form, or cross a login wall. If a required description is unavailable, request pasted text and mark the packet incomplete rather than inferring responsibilities.

For pasted content, preserve the supplied text verbatim and label facts that are absent or ambiguous. For a company URL, prefer the employer's job-detail page over a search-result summary.

## Return one posting packet

Return structured data to the caller; do not create a vault note. Use this shape, with `null`, `[]`, or `unknown` for missing data:

```yaml
source:
  kind: linkedin | company | pasted
  url: ""
  canonical-job-url: ""
  captured-at: "YYYY-MM-DD"
source-job-id: ""
company: ""
job-title: ""
seniority: ""
location: ""
work-type: ""
contract-type: ""
salary:
  min: null
  max: null
  currency: ""
  period: ""
found-via: ""
posting-status: active | closed | unknown
posted-at: ""
apply-method: ""
requirements:
  required: []
  preferred: []
responsibilities: []
benefits: []
technology: []
description:
  overview: ""
  complete-captured-description: ""
related-opportunities: []
evidence:
  - claim: ""
    source-url: ""
    captured-at: ""
gaps: []
```

Normalize the canonical job URL by removing tracking parameters only when doing so preserves the job identity. Capture a source job ID from a URL or page only when explicit. Deduplicate related opportunities by canonical URL or source job ID, and retain each opportunity's company, title, location, URL, and source.
