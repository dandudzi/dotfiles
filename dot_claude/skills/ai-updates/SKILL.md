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

### Bonus Source (Community Aggregator)

| Source            | Category                                                   | URL                         | Notes                                                             |
| ----------------- | ---------------------------------------------------------- | --------------------------- | ----------------------------------------------------------------- |
| AnthropicNews.com | Third-party press, competitor news, community blogs, video | `https://anthropicnews.com` | Unofficial. Adds external coverage not found in official sources. |

Use the **core sources** as primary. AnthropicNews.com is a supplementary source that captures
third-party press coverage (TechCrunch, The Verge, etc.), OpenAI/competitor context, community
blog posts, and video content that official channels never publish.

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
from html.parser import HTMLParser

headers = {"User-Agent": "Mozilla/5.0 (compatible; AnthropicUpdatesSkill/1.0)"}
seen_titles = set()
stories = []


def add_story(source, category, title, desc="", link="", date=""):
    """Add a story with deduplication by normalized title."""
    key = re.sub(r'\s+', ' ', title.lower().strip())[:80]
    if title and key not in seen_titles:
        seen_titles.add(key)
        stories.append({
            "source": source,
            "category": category,
            "title": title.strip(),
            "desc": desc.strip()[:300],
            "link": link.strip(),
            "date": date.strip()
        })


def fetch_url(url):
    """Fetch a URL and return the response body as a string."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ------------------------------------------------------------------
# 1. Anthropic Newsroom (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://www.anthropic.com/news")
    # Look for article links with titles — pattern: links containing /news/ path
    for m in re.finditer(
        r'<a[^>]*href="(/news/[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
    ):
        block = m.group(0)
        # Extract visible text as title
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://www.anthropic.com" + m.group(1)
        if title_text and len(title_text) > 10 and "/news/" in m.group(1):
            add_story("Anthropic Newsroom", "announcements", title_text, link=link)
except Exception as e:
    print(f"[Anthropic Newsroom] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 2. Anthropic Engineering Blog (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://www.anthropic.com/engineering")
    for m in re.finditer(
        r'<a[^>]*href="(/engineering/[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://www.anthropic.com" + m.group(1)
        if title_text and len(title_text) > 10:
            add_story("Engineering Blog", "engineering", title_text, link=link)
except Exception as e:
    print(f"[Engineering Blog] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 3. Anthropic Research (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://www.anthropic.com/research")
    for m in re.finditer(
        r'<a[^>]*href="(/research/[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://www.anthropic.com" + m.group(1)
        if title_text and len(title_text) > 10:
            add_story("Anthropic Research", "research", title_text, link=link)
except Exception as e:
    print(f"[Anthropic Research] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 4. Alignment Science Blog (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://alignment.anthropic.com")
    # This blog uses a different structure — look for post links
    for m in re.finditer(
        r'<a[^>]*href="(https://alignment\.anthropic\.com/[^"]+)"[^>]*>.*?</a>',
        html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = m.group(1)
        if title_text and len(title_text) > 10 and link != "https://alignment.anthropic.com/":
            add_story("Alignment Science", "alignment", title_text, link=link)
except Exception as e:
    print(f"[Alignment Science] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 5. Claude Blog (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://claude.com/blog")
    for m in re.finditer(
        r'<a[^>]*href="(/blog/[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://claude.com" + m.group(1)
        if title_text and len(title_text) > 10:
            add_story("Claude Blog", "product", title_text, link=link)
except Exception as e:
    print(f"[Claude Blog] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 6. Transparency Hub (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://www.anthropic.com/transparency")
    for m in re.finditer(
        r'<a[^>]*href="(/transparency/[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://www.anthropic.com" + m.group(1)
        if title_text and len(title_text) > 10:
            add_story("Transparency Hub", "transparency", title_text, link=link)
except Exception as e:
    print(f"[Transparency Hub] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 7. Claude Developer Newsletter (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://docs.anthropic.com/en/developer-newsletter/overview")
    for m in re.finditer(
        r'<a[^>]*href="(/en/developer-newsletter/[^"]+)"[^>]*>.*?</a>',
        html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://docs.anthropic.com" + m.group(1)
        if title_text and len(title_text) > 5 and "overview" not in m.group(1):
            add_story("Developer Newsletter", "newsletter", title_text, link=link)
except Exception as e:
    print(f"[Developer Newsletter] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 8. Claude Code GitHub Releases (JSON API)
# ------------------------------------------------------------------
try:
    api_url = "https://api.github.com/repos/anthropics/claude-code/releases?per_page=10"
    req = urllib.request.Request(api_url, headers={
        "User-Agent": headers["User-Agent"],
        "Accept": "application/vnd.github.v3+json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        releases = json.loads(resp.read().decode("utf-8"))
    for rel in releases:
        name = rel.get("name") or rel.get("tag_name", "")
        body = rel.get("body", "")[:300]
        link = rel.get("html_url", "")
        date = rel.get("published_at", "")[:10]
        add_story("Claude Code GitHub", "claude-code", name, desc=body, link=link, date=date)
except Exception as e:
    print(f"[Claude Code GitHub] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 9. Docs Release Notes (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://docs.anthropic.com/en/release-notes/overview")
    for m in re.finditer(
        r'<a[^>]*href="(/en/release-notes/[^"]+)"[^>]*>.*?</a>',
        html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = "https://docs.anthropic.com" + m.group(1)
        if title_text and len(title_text) > 5 and "overview" not in m.group(1):
            add_story("Docs Release Notes", "release-notes", title_text, link=link)
except Exception as e:
    print(f"[Docs Release Notes] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# 10. Status Page (RSS feed)
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
        date = (pub_el.text or "").strip() if pub_el is not None else ""
        if title:
            add_story("Status Page", "status", title, desc=desc, link=link, date=date)
except Exception as e:
    print(f"[Status Page] failed: {e}", file=sys.stderr)


# ------------------------------------------------------------------
# BONUS: AnthropicNews.com (HTML scrape)
# ------------------------------------------------------------------
try:
    html = fetch_url("https://anthropicnews.com")
    for m in re.finditer(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*>.*?</a>', html, re.DOTALL
    ):
        block = m.group(0)
        title_text = re.sub(r'<[^>]+>', '', block).strip()
        link = m.group(1)
        # Skip navigation and internal links
        if (title_text and len(title_text) > 15
                and "anthropicnews.com" not in link
                and not link.endswith(('.css', '.js', '.png', '.svg'))):
            add_story("AnthropicNews.com", "external", title_text, link=link)
except Exception as e:
    print(f"[AnthropicNews.com] failed: {e}", file=sys.stderr)


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

1. Run the fetch script above to pull data from all sources.
2. Group stories by category:
   - **Claude Code** — GitHub releases, version changes
   - **Product & Apps** — Claude Blog, Newsroom product announcements, Docs release notes for Apps
   - **API & SDK** — Docs release notes for API/SDK changes
   - **Engineering** — Engineering Blog deep-dives
   - **Research & Alignment** — Research publications, Alignment Science Blog
   - **Transparency & Policy** — Transparency Hub, RSP updates, policy announcements
   - **Developer Newsletter** — Monthly newsletter highlights
   - **Status** — Recent incidents or ongoing issues
   - **External Coverage** _(from AnthropicNews.com)_ — Third-party press, competitor context, community content
3. Deduplicate — if the same announcement appears in Newsroom and Claude Blog, keep the Newsroom version.
4. Write a concise summary. Keep each item to 1–2 sentences. Limit to the 15–20 most notable items across all categories.
5. Format using the template below.
6. Save the summary to the user's workspace as a timestamped `.md` file:

   ```bash
   date +"%Y-%m-%d_%H-%M"
   ```

   File name: `anthropic-updates-YYYY-MM-DD_HH-MM.md`
7. Present the saved file link to the user.

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

📰 EXTERNAL COVERAGE (via AnthropicNews.com)
• [headline] — [summary.] (Original source)

---
Sources: Anthropic Newsroom, Engineering Blog, Research, Alignment Science,
Claude Blog, Transparency Hub, Developer Newsletter, Claude Code GitHub,
Docs Release Notes, Status Page, AnthropicNews.com
```

Omit categories that have no items. If the user asked about a specific topic (e.g. "Claude Code"),
surface that category first and expand it with more detail.

---

## Best Practices

- **Prioritize recency**: lead with the most recent items. Claude Code releases ship multiple
  times per week — show the latest 3–5, not all of them.
- **Cite sources**: always note where each item came from.
- **Be concise**: the value is in the digest, not full articles. 15–20 items max for a full briefing.
- **Graceful degradation**: if a source fails, skip it silently and use the others.
  Print failures to stderr so they're visible for debugging but don't break the output.
- **Separate official from external**: always keep AnthropicNews.com items in their own section
  at the bottom, clearly marked as external/community coverage.
- **Dedup across sources**: the same announcement often appears on both the Newsroom and
  Claude Blog. Keep the more detailed version and drop the duplicate.
- **HTML scraping is fragile**: if Anthropic redesigns a page, the regex patterns may break.
  When a source returns zero results unexpectedly, note it in the output so the user knows.
