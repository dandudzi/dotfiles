---
name: anthropic-updates
description: >
  Use this skill when the user asks about Claude updates, Anthropic news, what's new with Claude,
  Claude Code changelog, latest Claude features, Anthropic announcements, or any recent changes
  to Claude products. Also use when the user mentions "Claude updates", "what's new", "changelog",
  "release notes", "Anthropic news", "Claude Code updates", or asks "what did Anthropic ship lately".
  Fetches live data from official Anthropic sources and produces a structured markdown briefing.
  Always use this skill when the user wants to know about recent Anthropic or Claude developments,
  even if they don't explicitly say "news" — e.g. "anything new with Claude Code?" or
  "has Anthropic released anything recently?" should trigger this skill.
---

# Anthropic Updates

## Overview

Fetch and summarize the latest updates from official Anthropic channels. Produces a clean,
categorized markdown briefing covering product launches, Claude Code releases, engineering
deep-dives, research publications, and operational status.

---

## Sources

### Core Sources (Official Anthropic)

| Source                      | Category                       | URL                                                           | Update frequency    |
| --------------------------- | ------------------------------ | ------------------------------------------------------------- | ------------------- |
| Anthropic Newsroom          | Announcements, product, policy | `https://www.anthropic.com/news`                              | Several times/week  |
| Anthropic Engineering Blog  | Technical deep-dives           | `https://www.anthropic.com/engineering`                       | ~2–3 times/month    |
| Anthropic Research          | Papers, safety findings        | `https://www.anthropic.com/research`                          | ~2–4 times/month    |
| Alignment Science Blog      | Alignment, interpretability    | `https://alignment.anthropic.com`                             | ~1–2 times/month    |
| Claude Blog                 | Product how-tos, features      | `https://claude.com/blog`                                     | Several times/month |
| Transparency Hub            | Model cards, RSP updates       | `https://www.anthropic.com/transparency`                      | Irregular           |
| Claude Developer Newsletter | Monthly dev roundup            | `https://docs.anthropic.com/en/developer-newsletter/overview` | Monthly             |
| Claude Code GitHub Releases | CLI versions, changelogs       | `https://github.com/anthropics/claude-code/releases`          | Multiple times/week |
| Docs Release Notes          | API, SDK, Apps changes         | `https://docs.anthropic.com/en/release-notes/overview`        | Several times/month |
| Status Page                 | Incidents, degradations        | `https://status.claude.com`                                   | As needed           |

### External Coverage (via WebSearch)

After processing official sources, use **WebSearch** to find third-party press about Anthropic/Claude
from the last 3 days. This captures TechCrunch, The Verge, Ars Technica, community blogs,
and competitor context that official channels never publish. Keep these in a separate section.

---

## Fetching and Parsing

Most Anthropic sources lack RSS feeds, so the skill scrapes HTML pages directly.
Use Python for reliable parsing — it handles encoding issues and varied page structures
better than shell tools.

The GitHub Releases API and the status page RSS are the only structured feeds.

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

---

## Workflow

### 1. Full Briefing

1. Run the fetch script above to pull data from all sources. The script automatically:
   - **Filters by date**: extracts publication dates from listing page context and drops anything older than 3 days (items without a detectable date are kept — they may still be recent)
   - **Resolves changelog-only releases**: fetches `CHANGELOG.md` from the Claude Code repo and replaces placeholder descriptions with real change details
2. **External / non-official coverage**: The Python script only fetches official sources. After processing them, run **two WebSearch queries**:
   - `"Anthropic" OR "Claude" news -site:anthropic.com -site:claude.com` — third-party press, community blogs, and competitor context
   - `site:anthropicnews.com` — dedicated Anthropic news aggregator (JS-rendered, can only be reached via WebSearch)
   Combine results, deduplicate, and include in the **External Coverage** section.
3. Group stories by category:
   - **Claude Code** — GitHub releases, version changes
   - **Product & Apps** — Claude Blog, Newsroom product announcements, Docs release notes for Apps
   - **API & SDK** — Docs release notes for API/SDK changes
   - **Engineering** — Engineering Blog deep-dives
   - **Research & Alignment** — Research publications, Alignment Science Blog
   - **Transparency & Policy** — Transparency Hub, RSP updates, policy announcements
   - **Developer Newsletter** — Monthly newsletter highlights
   - **Status** — Recent incidents or ongoing issues
   - **External Coverage** — Third-party press (TechCrunch, The Verge, etc.), community blogs, competitor context (from WebSearch)
4. Deduplicate — if the same announcement appears in Newsroom and Claude Blog, keep the Newsroom version.
5. Write a concise summary. Keep each item to 1–2 sentences. Limit to the 15–20 most notable items across all categories.
6. Format using the template below.
7. Save the summary to the user's workspace as a timestamped `.md` file:

   ```bash
   date +"%Y-%m-%d_%H-%M"
   ```

   File name: `anthropic-updates-YYYY-MM-DD_HH-MM.md`
8. Present the saved file link to the user.

### 2. Quick Check (Top 5)

When the user asks "anything new?" or wants a quick update:

- Limit to the 5 most recent/important items
- One sentence each, no category headers
- Prioritize: Claude Code releases > product launches > API changes > everything else
- Still save to a timestamped file

### 3. Claude Code Only

When the user specifically asks about Claude Code updates:

- Fetch only the GitHub Releases source (source #8)
- Show the last 5–10 releases with version numbers, dates, and key changes
- Include links to full release notes

---

## Output Format

Always use this structure for the full briefing:

```
🔄 Anthropic Updates — [Day, Date]

⌨️ CLAUDE CODE
• [version] — [key changes summary] (date)
• [version] — [key changes summary] (date)

🚀 PRODUCT & APPS
• [headline] — [1–2 sentence summary.] (Source)

🔌 API & SDK
• [change] — [summary.] (Docs Release Notes)

🔧 ENGINEERING
• [title] — [summary.] (Engineering Blog)

🔬 RESEARCH & ALIGNMENT
• [title] — [summary.] (Source)

🛡️ TRANSPARENCY & POLICY
• [title] — [summary.] (Source)

📬 DEVELOPER NEWSLETTER
• [month] — [key highlights.] (Developer Newsletter)

⚠️ STATUS
• [incident title] — [current state.] (Status Page)

---

📰 EXTERNAL COVERAGE (via WebSearch)
• [headline] — [summary.] (Original source)

---
Sources: Anthropic Newsroom, Engineering Blog, Research, Alignment Science,
Claude Blog, Transparency Hub, Developer Newsletter, Claude Code GitHub,
Docs Release Notes, Status Page, WebSearch
```

Omit categories that have no items. If the user asked about a specific topic (e.g. "Claude Code"),
surface that category first and expand it with more detail.

---

## Best Practices

- **Hard 3-day cutoff**: the Python script enforces this automatically — it extracts dates from listing page context and drops anything older than 3 days. Items without a detectable date are kept (they may be recent). If a quiet day yields few items, that's fine — a short briefing is better than padding with stale content.
- **Changelog-only releases resolved automatically**: the script fetches `CHANGELOG.md` from the Claude Code repo and replaces placeholder descriptions. If the script still outputs `[CHANGELOG_ONLY]` (e.g., CHANGELOG.md fetch failed), use WebFetch on `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` to get the details manually.
- **External coverage via WebSearch**: since unofficial aggregator sites are JS-rendered and can't be scraped, use WebSearch to find third-party press about Anthropic/Claude from the last 3 days. Always keep external items in their own section at the bottom.
- **Cite sources**: always note where each item came from.
- **Be concise**: the value is in the digest, not full articles. 15–20 items max for a full briefing.
- **Graceful degradation**: if a source fails, skip it silently and use the others.
  Print failures to stderr so they're visible for debugging but don't break the output.
- **Dedup across sources**: the same announcement often appears on both the Newsroom and
  Claude Blog. Keep the more detailed version and drop the duplicate.
- **HTML scraping is fragile**: if Anthropic redesigns a page, the regex patterns may break.
  When a source returns zero results unexpectedly, note it in the output so the user knows.
