---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Hooks

> This file extends [common/hooks.md](../common/hooks.md) with TypeScript/JavaScript specific content.

## PostToolUse Hooks

Configure in `~/.claude/settings.json`:

- **Prettier**: Auto-format JS/TS files after edit
- **TypeScript check**: Run `tsc` after editing `.ts`/`.tsx` files
- **console.log warning**: Warn about `console.log` in edited files

### Alternative Formatters/Linters

| Tool | Description | When to Use |
|------|-------------|-------------|
| **Prettier** | Standard formatter | Default for most projects |
| **Biome v2** | Unified formatter + linter (97% Prettier-compatible, 25-35x faster, 459 lint rules) | New projects wanting a single tool; replaces Prettier + ESLint together |
| **ESLint** | Standard linter | Projects with complex lint configs |
| **Oxlint** | Rust-based linter, ESLint-compatible rules (OXC project) | Fast linting alongside Prettier; not a full ESLint replacement yet |

To use Biome instead of Prettier: `npx @biomejs/biome format --write <file>`

## Stop Hooks

- **console.log audit**: Check all modified files for `console.log` before session ends

## Agent Support

- **vitest-expert** — Vitest-specific configuration and patterns
- **playwright-expert** — Playwright E2E test automation
