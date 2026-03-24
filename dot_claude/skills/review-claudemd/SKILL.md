---
name: review-claudemd
description: Review recent conversations to find improvements for CLAUDE.md files.
model: sonnet
---

# Review CLAUDE.md from conversation history

Analyze recent conversations to improve both global (~/.claude/CLAUDE.md) and local (project) CLAUDE.md files.

## Step 1: Find conversation history

The project's conversation history is in `~/.claude/projects/`. The folder name is the project path with slashes replaced by dashes.

```bash
# Find the project folder (replace / with -)
PROJECT_PATH=$(pwd | sed 's|/|-|g' | sed 's|^-||')
CONVO_DIR=~/.claude/projects/-${PROJECT_PATH}
ls -lt "$CONVO_DIR"/*.jsonl | head -20
```

## Step 2: Extract recent conversations

Extract the 15-20 most recent conversations (excluding the current one) to a temp directory:

```bash
SCRATCH=/tmp/claudemd-review-$(date +%s)
mkdir -p "$SCRATCH"

for f in $(ls -t "$CONVO_DIR"/*.jsonl | head -20); do
  basename=$(basename "$f" .jsonl)
  # Skip current conversation if known
  cat "$f" | jq -r '
    if .type == "user" then
      "USER: " + (.message.content // "")
    elif .type == "assistant" then
      "ASSISTANT: " + ((.message.content // []) | map(select(.type == "text") | .text) | join("\n"))
    else
      empty
    end
  ' 2>/dev/null | grep -v "^ASSISTANT: $" > "$SCRATCH/${basename}.txt"
done

ls -lhS "$SCRATCH"
```

## Step 3: Launch parallel analysis agents

Use the Agent tool to spawn parallel subagents for conversation analysis. Batch conversations by size and give each agent a clear prompt:

```
Agent(
  description="Analyze conversations for CLAUDE.md improvements",
  prompt="Read these files, then analyze conversations against both CLAUDE.md files...",
  subagent_type="general-purpose"
)
```

Each agent should read:
- Global CLAUDE.md: `~/.claude/CLAUDE.md`
- Local CLAUDE.md: `./CLAUDE.md` (if exists)
- Batch of conversation files

Analysis targets:
1. Instructions that exist but were violated (need reinforcement or rewording)
2. Patterns that should be added to LOCAL CLAUDE.md (project-specific)
3. Patterns that should be added to GLOBAL CLAUDE.md (applies everywhere)
4. Anything in either file that seems outdated or unnecessary

Batch conversations by size:
- Large (>100KB): 1-2 per agent
- Medium (10-100KB): 3-5 per agent
- Small (<10KB): 5-10 per agent

## Step 4: Aggregate findings

Combine results from all agents into a summary with these sections:

1. **Instructions violated** - existing rules that weren't followed (need stronger wording)
2. **Suggested additions - LOCAL** - project-specific patterns
3. **Suggested additions - GLOBAL** - patterns that apply everywhere
4. **Potentially outdated** - items that may no longer be relevant

Present as tables or bullet points. Ask user if they want edits drafted.
