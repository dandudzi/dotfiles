---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

## its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Keep final file review as short and clear. If user want more context attach reference to proof.

## The Process of research should prove each claim.

```
Doubt cycle:
1: DIVIDE - split question/topic into smaller claims
2: CLAIM — write the claim + why-it-matters
3: REASEARCH - find source for the claim
4: DOUBT — check adversarial prompt
5: RECONCILE FACTS — record findings, update main topic and add new claims
```

### Step 1: DIVIDE

Lay down structure for research using below template

```
# Main topic

Here decsripe in one sentence problem being researched.

## Detalis

More details if user provided

## Final conclusion

Final output of the investigation.

## Reference to facts

1. List of references to most important facts 

## Claims

### Claim name

Descritption: Descritption of the claim why it matter.
Output: Final claim stance

#### Facts

1. Finding for claim. [reference to claim]


```

### Step 2: CLAIM — Surface what stands

Name the decision in two or three lines, and add new claim do the list of claims.

### Step 3: RESEARCH 

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.

### Step 4: DOUBT

Spawn adversarial subagent that will assume you are overconfident. It looks for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling

Do not hand the reviewer your conclusion biases. The reviewer must independently determine whether the claim and facts are true.

### Step 5: RECONCILE FACTS

The reviewer's output is data, not verdict. **You are still the orchestrator.**
A fresh reviewer can be wrong because it lacks context. Don't defer just because it's "fresh."

1. Record any finding and final decision for claim.
2. Check if new claim changes of research topic.
3. Check if research require more claims to discover. Add new one or pick not finished one.
4. Assess if next iteration is required. More than 10 claims means that question should be break down further hence stop and ask user for next commands.
