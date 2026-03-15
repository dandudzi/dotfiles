---
name: multi-agent-patterns
description: >
  Orchestration patterns, failure modes, and token economics for multi-agent
  Claude Code systems. Use when designing agent workflows, debugging coordination
  failures, or optimising parallel task execution.
---

# Multi-Agent Patterns

## When to Activate

Trigger on: "multi-agent", "orchestrate agents", "agent coordination", "parallel agents", "supervisor pattern", "swarm", "agent handoff", "agent workflow".

## Architecture Patterns

### Supervisor / Orchestrator Pattern

The orchestrator holds state and delegates tasks via `forward_message`. Prevents the telephone-game problem where each agent re-interprets instructions.

```
Orchestrator
├── forward_message → Agent A (task slice 1)
├── forward_message → Agent B (task slice 2)
└── collect results → synthesise
```

Key techniques:
- Output schema constraints on sub-agent responses (structured JSON) — reduces hallucination drift
- Checkpoint after each agent: verify output matches expected schema before forwarding
- Supervisor bottleneck mitigation: fan-out to ≤8 concurrent agents; batch beyond that

### Peer-to-Peer / Swarm Pattern

Agents hand off to each other without a central coordinator. Use for pipelines where each step depends on the previous output.

```
Agent A → (output + context) → Agent B → (output + context) → Agent C
```

Rules:
- Pass **explicit state** in every handoff — never rely on shared memory
- Include original task + prior decisions in each handoff payload
- Define termination condition upfront (otherwise agents loop indefinitely)

### Hierarchical Pattern

Three-tier: strategy (Opus) → planning (Sonnet) → execution (Haiku).

```
Strategy agent (Opus)   — "What should we build?"
    ↓ architecture spec
Planning agent (Sonnet) — "How do we build it?"
    ↓ task list + file plan
Execution agents (Haiku) — "Build it"
```

Use for large-scale projects (10+ files, multi-feature). Overkill for single-file tasks.

## Context Isolation Principles

Sub-agents **partition context**, not organisational roles. The primary benefit is that each agent starts with a clean context window focused on its slice of work.

**Why telephone-game fails**: When Agent A passes its full response to Agent B, and B passes both to C, context compounds geometrically. By message 4, most context is prior agent commentary, not task-relevant content.

**Fix**: Each handoff should contain:
1. The original task spec (immutable)
2. Decisions made (compact, structured)
3. The agent's specific output
4. NOT: prior agents' reasoning or intermediate work

## Token Economics

Production baseline: multi-agent systems consume **~15× tokens** compared to single-agent approaches for equivalent tasks.

| Pattern | Token multiplier | Use when |
|---------|-----------------|----------|
| Single agent | 1× | Tasks fitting in one context |
| Supervisor + 3 workers | 5-8× | Independent parallel sub-tasks |
| Hierarchical (3 tiers) | 12-20× | Large-scale projects, diverse expertise |
| Full swarm (5+ agents) | 20-40× | Maximum parallelism, time-critical |

**When NOT to use multi-agent**:
- Task fits comfortably in one context window
- Sub-tasks are tightly interdependent (sequential reads/writes to same files)
- Token budget is constrained
- Simpler tool use (search, read, write) can solve the problem

## Failure Mode Catalog

### Divergence
Sub-agents produce inconsistent outputs that can't be merged.
- Prevention: Define shared output schema upfront; validate each response before combining
- Detection: Structural diff of agent outputs before synthesis

### Error Propagation
One agent's mistake silently corrupts downstream agents.
- Prevention: Schema validation at each handoff; include confidence signals in outputs
- Detection: Checkpoint verification after each agent completes

### Consensus Hallucination
Multiple agents independently "agree" on a wrong answer.
- Prevention: Assign adversarial roles — one agent argues against; weighted voting requires dissent
- Patterns: Debate protocol (pro/con agents), red team agent, independent validation agent

### Supervisor Bottleneck
Orchestrator serialises work that could be parallel.
- Fix: Fan-out pattern — dispatch all independent tasks simultaneously, collect results
- Anti-pattern: Awaiting Agent A's result to decide whether to start Agent B (when B doesn't depend on A)

### Coordination Overhead
More time spent coordinating than doing work.
- Symptom: 5+ messages just to agree on task scope
- Fix: Front-load all context into initial agent prompt; minimise back-and-forth

## Handoff Protocols

### Minimal Handoff Schema
```json
{
  "task": "original task specification (unchanged)",
  "decisions": ["list of committed decisions from prior agents"],
  "output": { "structured output from this agent" },
  "next_agent_instructions": "what the next agent should do with this"
}
```

### Checkpoint Pattern
After each agent completes, orchestrator verifies:
- [ ] Output matches expected schema
- [ ] No required fields are null/missing
- [ ] Confidence signal is above threshold (if applicable)
- [ ] No error markers in output

## Agent Selection Matrix

| Task Type | Pattern | Orchestrator Model | Worker Model |
|-----------|---------|-------------------|--------------|
| Independent research tasks | Supervisor + workers | Sonnet | Haiku |
| Sequential pipeline | Peer-to-peer | N/A | Haiku/Sonnet |
| Complex architectural work | Hierarchical | Opus | Sonnet + Haiku |
| Parallel file writes | Supervisor + workers | Sonnet | Haiku |
| Adversarial review | Supervisor + debate | Sonnet | Sonnet |

## Anti-Patterns

❌ WRONG — Passing full agent history in handoffs:
```
Agent B prompt: "Here is everything Agent A said: [10,000 tokens of reasoning]..."
```

✅ RIGHT — Structured handoff with only essential information:
```
Agent B prompt: "Task: X. Agent A decided: [Y, Z]. Your job: implement Z."
```

---

❌ WRONG — Sequential dispatch when tasks are independent:
```
wait for agent_security()
wait for agent_performance()  # doesn't need security results
wait for agent_docs()
```

✅ RIGHT — Parallel dispatch:
```
[agent_security(), agent_performance(), agent_docs()]  # all at once
```

## Agent Support

- Use `architect` agent for designing multi-agent system architecture
- Use `ai-engineer` agent for LLM app integration and agentic systems

## Skill References

- `microservices-patterns` — service boundary patterns (analogous to agent boundary design)
- `saga-orchestration` — distributed coordination patterns that apply to agent workflows
