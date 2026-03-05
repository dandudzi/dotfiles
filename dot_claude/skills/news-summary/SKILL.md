---
name: news-summary
description: >
  Use this skill when the user asks for news updates, a daily briefing, morning news,
  what's happening in the world today, or a news summary. Also use when the user wants
  headlines by topic (tech, business, world, US, etc.).
  Fetches live headlines from trusted international RSS feeds (BBC, Reuters, NPR, Al Jazeera,
  The Guardian, AP) and produces a clean text summary. Always use this skill when
  the user mentions "news", "headlines", "briefing", or "what's going on today".
  Also triggers for topic-specific requests like "tech news", "business headlines",
  "what's happening in the US today", or "world news".
---

# News Summary

## Overview

Fetch and summarize live headlines from trusted international RSS feeds. Produces a clean,
grouped text briefing with source dates. Falls back to WebSearch if feeds are unavailable,
and saves a diagnostic report if both paths fail.

---

## RSS Feed Sources

| Source          | Perspective       | Feed URL                                           |
| --------------- | ----------------- | -------------------------------------------------- |
| BBC World       | Western / UK      | `https://feeds.bbci.co.uk/news/world/rss.xml`      |
| BBC Top Stories | Western / UK      | `https://feeds.bbci.co.uk/news/rss.xml`            |
| BBC Business    | Finance           | `https://feeds.bbci.co.uk/news/business/rss.xml`   |
| BBC Technology  | Tech              | `https://feeds.bbci.co.uk/news/technology/rss.xml` |
| Reuters         | Western / Global  | `https://feeds.reuters.com/reuters/topNews`        |
| NPR             | US perspective    | `https://feeds.npr.org/1001/rss.xml`               |
| Al Jazeera      | Global South      | `https://www.aljazeera.com/xml/rss/all.xml`        |
| The Guardian    | UK / Progressive  | `https://www.theguardian.com/world/rss`            |
| AP News         | US / Wire service | `https://rsshub.app/apnews/topics/ap-top-news` ⚠️  |

> ⚠️ **AP News** routes through the community-run `rsshub.app` proxy and is the most likely
> feed to fail. If it returns zero results, skip it silently and use the other 8 sources.

Use **BBC World** as the primary source. Supplement with Al Jazeera for global perspective,
The Guardian and Reuters for breadth. BBC topic feeds (Business, Technology) for category briefings.

---

## Fetching and Parsing

Use Python for reliable XML parsing — it handles edge cases that `grep/sed` miss (CDATA,
special characters, encoding issues). The script collects errors per source and extracts
publication dates from each story so the briefing shows how fresh each item is.

```bash
python3 - <<'EOF'
import urllib.request
import xml.etree.ElementTree as ET
import sys
import json
from datetime import datetime

feeds = {
    "BBC World":        "https://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Top Stories":  "https://feeds.bbci.co.uk/news/rss.xml",
    "BBC Business":     "https://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC Technology":   "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Reuters":          "https://feeds.reuters.com/reuters/topNews",
    "NPR":              "https://feeds.npr.org/1001/rss.xml",
    "Al Jazeera":       "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian":     "https://www.theguardian.com/world/rss",
    "AP News":          "https://rsshub.app/apnews/topics/ap-top-news",
}

seen_titles = set()
stories = []
errors = {}

def parse_pubdate(pub_str):
    """Parse RSS pubDate to a short 'Mon DD' label. Returns empty string on failure."""
    if not pub_str:
        return ""
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            return datetime.strptime(pub_str.strip(), fmt).strftime("%b %d")
        except ValueError:
            continue
    return ""

for source, url in feeds.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()
            for item in root.iter("item"):
                title_el = item.find("title")
                desc_el  = item.find("description")
                link_el  = item.find("link")
                pub_el   = item.find("pubDate")
                title = (title_el.text or "").strip() if title_el is not None else ""
                desc  = (desc_el.text  or "").strip() if desc_el  is not None else ""
                link  = (link_el.text  or "").strip() if link_el  is not None else ""
                pub   = parse_pubdate((pub_el.text or "") if pub_el is not None else "")
                key = title.lower()[:60]
                if title and key not in seen_titles:
                    seen_titles.add(key)
                    stories.append({"source": source, "title": title,
                                    "desc": desc[:200], "link": link, "date": pub})
    except Exception as e:
        errors[source] = str(e)
        print(f"[{source}] failed: {e}", file=sys.stderr)

for s in stories[:30]:
    date_label = f" [{s['date']}]" if s['date'] else " [date unknown]"
    print(f"[{s['source']}]{date_label} {s['title']}")
    if s['desc']:
        print(f"  {s['desc']}")
    print()

print("__ERRORS__:" + json.dumps(errors))
EOF
```

---

## Fallback: WebSearch

If **any** RSS feed fails, note the error and continue with the remaining feeds. If **all**
RSS feeds fail (zero stories collected), switch to WebSearch automatically.

Get today's date first, then run these searches:

```bash
TODAY=$(date +"%B %-d %Y")
```

```
top world news headlines today $TODAY
top business and finance news today $TODAY
top technology news today $TODAY
```

For a **US-specific** or **topic-specific** briefing, substitute the topic:

```
top US news headlines today $TODAY
top [topic] news today $TODAY
```

Use the results exactly as you would use RSS stories: group by category, deduplicate by
topic, write 1–2 sentence summaries, attribute each story to its source. The output format
stays the same — the user should not notice which path was taken. Story dates will not be
available from WebSearch results; omit the date label for those items.

---

## Total Failure: Diagnose and Document

If **both** RSS and WebSearch return nothing useful (empty results, all blocked, or
unrecoverable errors), do not silently stop. Instead:

1. **Diagnose** — review every error message collected. Note whether the failure looks like
   a network block (403, tunnel error, connection refused), a DNS issue, a timeout, or
   something else. Make a clear, plain-language diagnosis.

2. **Save a dated error report** — create the timestamped `.md` file as usual, but populate
   it with the diagnostic instead of news stories:

```
📰 News Briefing — [Day, Date]

⚠️ Unable to fetch news today

## What was tried
- RSS feeds: [list each feed URL and its exact error]
- WebSearch: [what was searched and what came back, or why it failed]

## Likely cause
[Plain-language diagnosis — e.g., "The network proxy is blocking outbound HTTP requests
to external news domains (403 Forbidden). This is an environment-level restriction, not
a problem with the feeds themselves."]

## Suggested fix
[One or two concrete suggestions — e.g., "Try running this task from a different network
environment, or configure the proxy to allow feeds.bbci.co.uk and feeds.npr.org."]

---
Generated: [timestamp]
```

3. **Present the file link** to the user so they know a record was saved and can see what went wrong.

---

## Workflow

### 1. Standard Briefing

1. Run the fetch script above to pull headlines.
2. Group stories thematically (World, US, Business, Tech, etc.).
3. Deduplicate — skip stories where the same event already appears under another source.
4. Write a concise summary (5–8 top stories). Keep each item to 1–2 sentences.
5. Include the story date label where available (e.g., `[Mar 04]`). Mark items without
   a date as `[date unknown]` so the user can gauge freshness.
6. Format using the template below.
7. Save the summary to the user's workspace folder as a `.md` file named with the current
   date and time, e.g. `news-summary-2026-03-04_09-30.md`:

   ```bash
   date +"%Y-%m-%d_%H-%M"
   ```

8. Present the saved file link to the user.

### 2. Quick Briefing (Top 5)

When the user is in a hurry or explicitly asks for a "quick" or "short" briefing:

- Limit to the 5 most important stories
- One sentence each, no category headers
- Still save to a timestamped file as above

### 3. Topic-Specific Briefing

When the user asks for a specific topic (e.g., "tech news", "US headlines", "business news"):

- For RSS: prioritize the relevant topic feed (BBC Technology, BBC Business, NPR for US)
  and pull from 1–2 supporting sources for breadth
- For WebSearch fallback: use the topic-substituted query form above
- Surface the requested category first and expand it with more items (up to 8)
- Still group any off-topic items found under their own headers below

---

## Output Format

Always use this structure for the text summary:

```
📰 News Briefing — [Day, Date]

🌍 WORLD
• [Headline 1] — [1–2 sentence summary.] [Mar 04] (Source)
• [Headline 2] — [1–2 sentence summary.] [date unknown] (Source)

🇺🇸 US
• [Headline] — [Summary.] [Mar 04] (Source)

💼 BUSINESS
• [Headline] — [Summary.] [Mar 03] (Source)

💻 TECH
• [Headline] — [Summary.] [Mar 04] (Source)

---
Sources: BBC World, Al Jazeera, NPR, The Guardian, Reuters
```

Omit categories that have no notable news. If the user asked for a specific region or
topic, surface that category first and expand it.

---

## Best Practices

- **Balance perspectives**: pair a Western source (BBC/Reuters) with a Global South one (Al Jazeera).
- **Prioritise breaking news**: if something is in multiple feeds, it's probably important.
- **Cite sources**: always note where each story came from.
- **Show dates**: include the `[Mon DD]` date label on each story so users can immediately
  tell how fresh it is. Mark items as `[date unknown]` when no date is available.
- **Be concise**: the value is in the digest, not the full article. 5–8 stories is ideal.
- **Graceful degradation**: if a feed fails, skip it and use the others. If all fail,
  fall back to WebSearch with the real date injected into the query. If that also fails,
  save an error report.
- **Watch the AP News proxy**: `rsshub.app` is a community proxy and the most fragile
  source. Treat its failures as expected and don't let them block the rest of the output.
