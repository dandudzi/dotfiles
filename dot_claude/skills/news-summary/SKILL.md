---
name: news-summary
description: >
  Use this skill when the user asks for news updates, a daily briefing, morning news,
  what's happening in the world today, or a news summary. Also use when the user wants
  headlines by topic (tech, business, world, etc.).
  Fetches live headlines from trusted international RSS feeds (BBC, Reuters, NPR, Al Jazeera,
  The Guardian, AP) and produces a clean text summary. Always use this skill when
  the user mentions "news", "headlines", "briefing", or "what's going on today".
---

# News Summary

## Overview

Fetch and summarize live headlines from trusted international RSS feeds. Produces a clean,
grouped text briefing.

---

## RSS Feed Sources

| Source          | Perspective       | Feed URL                                                                |
| --------------- | ----------------- | ----------------------------------------------------------------------- |
| BBC World       | Western / UK      | `https://feeds.bbci.co.uk/news/world/rss.xml`                           |
| BBC Top Stories | Western / UK      | `https://feeds.bbci.co.uk/news/rss.xml`                                 |
| BBC Business    | Finance           | `https://feeds.bbci.co.uk/news/business/rss.xml`                        |
| BBC Technology  | Tech              | `https://feeds.bbci.co.uk/news/technology/rss.xml`                      |
| Reuters World   | Western / Global  | `https://www.reutersagency.com/feed/?best-regions=world&post_type=best` |
| NPR             | US perspective    | `https://feeds.npr.org/1001/rss.xml`                                    |
| Al Jazeera      | Global South      | `https://www.aljazeera.com/xml/rss/all.xml`                             |
| The Guardian    | UK / Progressive  | `https://www.theguardian.com/world/rss`                                 |
| AP News         | US / Wire service | `https://rsshub.app/apnews/topics/ap-top-news`                          |

Use **BBC World** as the primary source. Supplement with 1–2 others for perspective and breadth.

---

## Fetching and Parsing

Use Python for reliable XML parsing — it handles edge cases that `grep/sed` miss (CDATA,
special characters, encoding issues).

```bash
python3 - <<'EOF'
import urllib.request
import xml.etree.ElementTree as ET
import sys

feeds = {
    "BBC World":   "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera":  "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR":         "https://feeds.npr.org/1001/rss.xml",
}

seen_titles = set()
stories = []

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
                title = (title_el.text or "").strip() if title_el is not None else ""
                desc  = (desc_el.text  or "").strip() if desc_el  is not None else ""
                link  = (link_el.text  or "").strip() if link_el  is not None else ""
                # Basic deduplication by title
                key = title.lower()[:60]
                if title and key not in seen_titles:
                    seen_titles.add(key)
                    stories.append({"source": source, "title": title,
                                    "desc": desc[:200], "link": link})
    except Exception as e:
        print(f"[{source}] failed: {e}", file=sys.stderr)

for s in stories[:30]:
    print(f"[{s['source']}] {s['title']}")
    if s['desc']:
        print(f"  {s['desc']}")
    print()
EOF
```

---

## Workflow

### 1. Standard Text Briefing

1. Run the fetch script above to pull headlines.
2. Group stories thematically (World, Business, Tech, etc.).
3. Deduplicate — skip stories where the same event already appears under another source.
4. Write a concise summary (5–8 top stories). Keep each item to 1–2 sentences.
5. Format using the template below.
6. Save the summary to the user's workspace folder as a `.md` file named with the current date and time, e.g. `news-summary-2026-03-03_09-30.md`. Use this bash snippet to get the timestamp: `date +"%Y-%m-%d_%H-%M"`.
7. Present the saved file link to the user.

### 2. Quick Briefing (Top 5)

When the user is in a hurry or explicitly asks for a "quick" or "short" briefing:

- Limit to the 5 most important stories
- One sentence each, no category headers
- Still save to a timestamped file as above

---

## Output Format

Always use this structure for the text summary:

```
📰 News Briefing — [Day, Date]

🌍 WORLD
• [Headline 1] — [1–2 sentence summary.] (Source)
• [Headline 2] — [1–2 sentence summary.] (Source)

💼 BUSINESS
• [Headline] — [Summary.] (Source)

💻 TECH
• [Headline] — [Summary.] (Source)

---
Sources: BBC World, Al Jazeera, NPR
```

Omit categories that have no notable news. If the user asked for a specific region or
topic, surface that category first.

---

## Best Practices

- **Balance perspectives**: pair a Western source (BBC/Reuters) with a Global South one (Al Jazeera).
- **Prioritise breaking news**: if something is in multiple feeds, it's probably important.
- **Cite sources**: always note where each story came from.
- **Be concise**: the value is in the digest, not the full article. 5–8 stories is ideal.
- **Graceful degradation**: if a feed fails, skip it silently and use the others.
