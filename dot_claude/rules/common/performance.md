# Performance Optimization

## Model Selection Strategy

**Haiku 4.5** (90% of Sonnet capability, 3x cost savings):
- Technology expert agents (css-expert, docker-expert, sql-expert, etc.)
- Pair programming and code generation
- Worker agents in multi-agent systems

**Sonnet 4.6** (Best coding model):
- code-reviewer, java-reviewer, python-reviewer (need nuanced judgement)
- Main development work and orchestrating multi-agent workflows
- Complex coding tasks

**Opus 4.6** (Deepest reasoning):
- architect agent (complex architectural decisions)
- Maximum reasoning requirements
- Research and analysis tasks

## Context Window Management

Avoid last 20% of context window for:
- Large-scale refactoring
- Feature implementation spanning multiple files
- Debugging complex interactions

Lower context sensitivity tasks:
- Single-file edits
- Independent utility creation
- Documentation updates
- Simple bug fixes

## Extended Thinking + Plan Mode

Extended thinking is enabled by default. Budget varies by model: up to 128K tokens (Opus 4.6), up to 64K tokens (Sonnet 4.6). Default budget cap is 10K tokens; override with `export MAX_THINKING_TOKENS=10000`.

Control extended thinking via:
- **Toggle**: Option+T (macOS) / Alt+T (Windows/Linux)
- **Config**: Set `alwaysThinkingEnabled` in `~/.claude/settings.json`
- **Budget cap**: `export MAX_THINKING_TOKENS=<tokens>` (min 1,024)
- **Verbose mode**: Ctrl+O to see thinking output

For complex tasks requiring deep reasoning:
1. Ensure extended thinking is enabled (on by default)
2. Enable **Plan Mode** for structured approach
3. Use multiple critique rounds for thorough analysis
4. Use split role sub-agents for diverse perspectives

## Build Troubleshooting

If build fails:
1. Use **build-error-resolver** agent
2. Analyze error messages
3. Fix incrementally
4. Verify after each fix
