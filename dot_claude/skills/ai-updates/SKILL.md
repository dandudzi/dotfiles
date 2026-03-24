---
name: ai-updates
description: Fetch live Anthropic updates when user asks about Claude news, releases, features, or announcements.
model: haiku
---

# Anthropic Updates

## When to Activate

- User asks about Claude updates, Anthropic news, or latest features
- User mentions "what's new", "changelog", or "release notes"
- User asks "anything new with Claude Code?" or similar

## Sources

| Source                      | URL                                                           |
| --------------------------- | ------------------------------------------------------------- |
| Anthropic Newsroom          | `https://www.anthropic.com/news`                              |
| Engineering Blog            | `https://www.anthropic.com/engineering`                       |
| Anthropic Research          | `https://www.anthropic.com/research`                          |
| Alignment Science           | `https://alignment.anthropic.com`                             |
| Claude Blog                 | `https://claude.com/blog`                                     |
| Transparency Hub            | `https://www.anthropic.com/transparency`                      |
| Developer Newsletter        | `https://docs.anthropic.com/en/developer-newsletter/overview` |
| Claude Code Releases        | `https://github.com/anthropics/claude-code/releases`          |
| Docs Release Notes          | `https://docs.anthropic.com/en/release-notes/overview`        |
| Status Page                 | `https://status.claude.com`                                   |

After official sources, use WebSearch for third-party coverage (TechCrunch, The Verge, community blogs).

## Fetching and Parsing

Use Python for HTML scraping. GitHub Releases API and Status RSS are structured feeds.

```bash
python3 - <<'PYEOF'
import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import sys
from datetime import datetime, timedelta, timezone

headers = {"User-Agent": "Mozilla/5.0 (compatible; AnthropicUpdatesSkill/1.0)"}
seen_titles = set()
stories = []
CUTOFF = datetime.now(timezone.utc) - timedelta(days=3)
TIMEOUT = 30

# English month patterns for date extraction from listing pages
_MONTH_RE = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
_DATE_PATTERNS = [
    re.compile(r'(\d{4}-\d{2}-\d{2})'),
    re.compile(r'(' + _MONTH_RE + r'\s+\d{1,2},?\s+\d{4})', re.I),
]


def parse_date(date_str):
    """Try to parse a date string into a datetime. Returns None on failure."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d",
                "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(date_str.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        pass
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def extract_date_from_context(html, pos, window=500):
    """Extract the nearest date from HTML context around a match position."""
    start = max(0, pos - window)
    end = min(len(html), pos + window)
    ctx = html[start:end]
    for pat in _DATE_PATTERNS:
        m = pat.search(ctx)
        if m:
            return parse_date(m.group(1))
    return None


def add_story(source, category, title, desc="", link="", date="", dt=None):
    """Add a story with deduplication by normalized title."""
    key = re.sub(r'\s+', ' ', title.lower().strip())[:80]
    if title and key not in seen_titles:
        seen_titles.add(key)
        stories.append({
            "source": source, "category": category,
            "title": title.strip(), "desc": desc.strip()[:600],
            "link": link.strip(), "date": date.strip() if date else "",
            "_dt": dt,
        })


def fetch_url(url, timeout=TIMEOUT):
    """Fetch a URL and return the response body as a string."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


# Helper: scrape a listing page, extract articles with dates, filter by CUTOFF
def scrape_listing(url, source, category, path_pattern, base_url="",
                    min_title=10, exclude_urls=None, exclude_paths=None,
                    drop_undated=True):
    """Scrape articles from a listing page, extract dates from context, skip old items.
    If drop_undated=True (default), items with no detectable date are dropped."""
    try:
        html = fetch_url(url)
        regex = re.compile(r'<a[^>]*href="(' + path_pattern + r')"[^>]*>.*?</a>', re.DOTALL)
        for m in regex.finditer(html):
            block = m.group(0)
            # Extract text, collapse whitespace, cap length to avoid embedded metadata
            title_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', block)).strip()[:150]
            raw_href = m.group(1)
            link = base_url + raw_href if base_url else raw_href
            if not title_text or len(title_text) < min_title:
                continue
            if exclude_urls and link.rstrip("/") in {u.rstrip("/") for u in exclude_urls}:
                continue
            if exclude_paths and any(ep in raw_href for ep in exclude_paths):
                continue
            dt = extract_date_from_context(html, m.start())
            if dt and dt < CUTOFF:
                continue  # older than 3 days, skip
            if dt is None and drop_undated:
                continue  # no date found, likely old or nav item
            date_str = dt.strftime("%Y-%m-%d") if dt else ""
            add_story(source, category, title_text, link=link, date=date_str, dt=dt)
    except Exception as e:
        print(f"[{source}] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 1-7. HTML-scraped sources (with listing-page date extraction)
# ------------------------------------------------------------------
scrape_listing("https://www.anthropic.com/news",
    "Anthropic Newsroom", "announcements", r'/news/[^"]+', "https://www.anthropic.com")

scrape_listing("https://www.anthropic.com/engineering",
    "Engineering Blog", "engineering", r'/engineering/[^"]+', "https://www.anthropic.com")

scrape_listing("https://www.anthropic.com/research",
    "Anthropic Research", "research", r'/research/[^"]+', "https://www.anthropic.com",
    exclude_paths=["/research/team/"])

scrape_listing("https://alignment.anthropic.com",
    "Alignment Science", "alignment", r'https://alignment\.anthropic\.com/[^"]+',
    exclude_urls={"https://alignment.anthropic.com", "https://alignment.anthropic.com/"})

scrape_listing("https://claude.com/blog",
    "Claude Blog", "product", r'/blog/[^"]+', "https://claude.com")

scrape_listing("https://www.anthropic.com/transparency",
    "Transparency Hub", "transparency", r'/transparency/[^"]+', "https://www.anthropic.com")

scrape_listing("https://docs.anthropic.com/en/developer-newsletter/overview",
    "Developer Newsletter", "newsletter", r'/en/developer-newsletter/[^"]+',
    "https://docs.anthropic.com", min_title=5, exclude_paths=["overview"])


# ------------------------------------------------------------------
# 8. Claude Code GitHub Releases (JSON API)
# ------------------------------------------------------------------
try:
    api_url = "https://api.github.com/repos/anthropics/claude-code/releases?per_page=10"
    req = urllib.request.Request(api_url, headers={
        "User-Agent": headers["User-Agent"],
        "Accept": "application/vnd.github.v3+json"
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    for rel in releases:
        pub_date = rel.get("published_at", "")
        dt = parse_date(pub_date)
        if dt and dt < CUTOFF:
            continue
        name = rel.get("name") or rel.get("tag_name", "")
        body = (rel.get("body") or "").strip()
        link = rel.get("html_url", "")
        date = pub_date[:10]
        is_changelog_only = (
            not body
            or len(body) < 40
            or re.match(r'^(changelog|bump|version)\s*(update|bump)?\.?$', body, re.I)
        )
        if is_changelog_only:
            body = "[CHANGELOG_ONLY]"
        else:
            body = body[:600]
        add_story("Claude Code GitHub", "claude-code", name, desc=body, link=link, date=date, dt=dt)
except Exception as e:
    print(f"[Claude Code GitHub] failed: {e}", file=sys.stderr)


scrape_listing("https://docs.anthropic.com/en/release-notes/overview",
    "Docs Release Notes", "release-notes", r'/en/release-notes/[^"]+',
    "https://docs.anthropic.com", min_title=5, exclude_paths=["overview"])


# ------------------------------------------------------------------
# 10. Status Page (RSS feed) — last 3 days only
# ------------------------------------------------------------------
try:
    xml_text = fetch_url("https://status.claude.com/history.rss")
    root = ET.fromstring(xml_text)
    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pub_el = item.find("pubDate")
        title = (title_el.text or "").strip() if title_el is not None else ""
        link = (link_el.text or "").strip() if link_el is not None else ""
        desc = (desc_el.text or "").strip()[:300] if desc_el is not None else ""
        date_str = (pub_el.text or "").strip() if pub_el is not None else ""
        dt = parse_date(date_str)
        if dt and dt < CUTOFF:
            continue
        if title:
            add_story("Status Page", "status", title, desc=desc, link=link, date=date_str, dt=dt)
except Exception as e:
    print(f"[Status Page] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# Resolve changelog-only releases from CHANGELOG.md
# ------------------------------------------------------------------
changelog_stories = [s for s in stories if s.get("desc", "") == "[CHANGELOG_ONLY]"]
if changelog_stories:
    try:
        changelog_md = fetch_url(
            "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
            timeout=15
        )
        for s in changelog_stories:
            version = s["title"].lstrip("v").strip()
            pattern = r'##\s*\[?' + re.escape(version) + r'\]?[^\n]*\n(.*?)(?=\n## |\Z)'
            m = re.search(pattern, changelog_md, re.DOTALL)
            if m:
                s["desc"] = m.group(1).strip()[:600]
            else:
                s["desc"] = "Details not found in CHANGELOG.md"
    except Exception as e:
        print(f"[CHANGELOG.md] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------
for s in stories[:50]:
    date_str = f" ({s['date']})" if s['date'] else ""
    print(f"[{s['source']}|{s['category']}]{date_str} {s['title']}")
    if s['desc']:
        print(f"  {s['desc'][:200]}")
    if s['link']:
        print(f"  {s['link']}")
    print()
PYEOF
```

## Workflow

**Full Briefing:**
1. Run Python script above (filters to 3 days, dedupes, resolves changelog)
2. Add WebSearch results for external coverage (TechCrunch, community blogs)
3. Group by category and deduplicate across sources
4. Keep items to 1–2 sentences, max 15–20 items
5. Save as `anthropic-updates-YYYY-MM-DD_HH-MM.md`

**Quick Check:** Top 5 items, one sentence each (prioritize Claude Code > product > API)

**Claude Code Only:** Last 5–10 releases with versions and key changes from GitHub API

## Output Format

```
Anthropic Updates — [Date]

CLAUDE CODE
• [version] — [key changes] (date)

PRODUCT & APPS
• [headline] — [1–2 sentence summary] (Source)

API & SDK
• [change] — [summary] (Release Notes)

ENGINEERING
• [title] — [summary] (Engineering Blog)

RESEARCH & ALIGNMENT
• [title] — [summary] (Source)

EXTERNAL COVERAGE
• [headline] — [summary] (Original source)
```

Omit empty categories. If user asked about specific topic, expand that section first.

## Best Practices

- **3-day cutoff enforced** by script (items without dates are kept as possibly recent)
- **Changelog resolution**: script fetches CHANGELOG.md automatically; if `[CHANGELOG_ONLY]` appears, use WebFetch manually
- **External coverage**: use WebSearch for JS-rendered aggregators (can't be scraped)
- **Cite sources** for each item
- **Concise**: 15–20 items max, 1–2 sentences each
- **Dedup**: keep more detailed version when same item appears in multiple sources
- **Error handling**: skip failed sources silently; note zero results to user
