# Gap Analysis

Audit date: 2026-07-11

Scope: read-only inspection of the live Codex 0.144.1 setup, shared agent configuration, installed plugins/skills, rules, MCP wrappers and safe aggregate usage traces. Secret values and prompt contents were excluded.

## Executive priority

| Priority | Finding | Severity | Confidence | Discussion decision |
|---|---|---:|---:|---|
| 1 | A Context7 credential is embedded as a static HTTP header in `~/.codex/config.toml`. | Deal-breaker | High | Rotate it, move it to an environment-backed header, and keep only the environment-variable name in config. |
| 2 | `/Users/daniel` is marked trusted, in addition to about two dozen narrower paths. | High | High on local state; Medium on descendant-resolution semantics | Remove the home-wide trust entry unless broad trust is deliberate; trust individual repositories instead. |
| 3 | The active `~/.codex/rules/default.rules` policy needed its installation status and validation limitations reconciled. | Resolved documentation gap | High | Header and preview-tester notes were repaired on 2026-07-11; retain inline tests and re-run the official tester when the packaged CLI exposes it. |
| 4 | Write-capable MCPs have no explicit least-privilege allowlist or approval policy. | High | High | Add explicit `enabled_tools` and `default_tools_approval_mode`/per-tool overrides, especially for Serena and Linear. |
| 5 | Most enabled MCPs and artifact plugins show no confirmed use in 311 indexed rollouts. | Medium | High for recorded tool calls; Medium for implicit skill use | Disable or profile-gate unused capabilities; keep Exa and Context7 enabled. |

## 1. Static MCP credential in version-shaped configuration

- Evidence: `[mcp_servers.context7.http_headers]` contains a credential value directly in `~/.codex/config.toml`. The value was not copied or displayed. The file mode is `0600`, which limits local exposure but does not prevent accidental backup, dotfile capture, logging, or screen sharing.
- Official baseline: HTTP MCPs support `env_http_headers`, mapping a header name to an environment-variable name; bearer tokens likewise support environment-backed configuration.
- Severity: **deal-breaker**.
- Confidence: **High**.
- Benefit: removes a live secret from a routinely edited configuration file and makes rotation/auditing clearer.
- Cost/risk: requires setting the environment variable where both the app and CLI can see it; rotation may briefly interrupt Context7.
- Decision: rotate first, then replace the static header with an environment-backed header. Confirm that the Codex desktop process inherits the variable before deleting the old value.

## 2. Home-directory-wide project trust weakens the trust gate

- Evidence: `~/.codex/config.toml` marks `/Users/daniel` trusted and also records roughly two dozen narrower trusted projects.
- Official baseline: trusted projects may load project-local `.codex/config.toml`, hooks, and rules; untrusted projects bypass those layers. The official docs do not explicitly document the exact parent/descendant matching algorithm, so the practical inheritance behavior should be tested before claiming every descendant is automatically trusted.
- Severity: **High** because the entry is broader than necessary and potentially neutralizes the main project-local configuration trust boundary.
- Confidence: **High** that the broad entry exists; **Medium** on its exact descendant effect.
- Benefit: repository-by-repository trust contains cloned or downloaded projects with hostile `.codex` content.
- Cost/risk: more first-open trust prompts and maintenance.
- Decision: remove the home-wide entry unless it is intentional and verified safe; retain explicit trusted repositories.

## 3. Active execution policy status and validation documentation

- Original evidence: `~/.codex/rules/default.rules` is an active symlink to `~/.config/agents/codex/rules/default.rules`, while the source header previously said “review draft” and “intentionally not installed”. The file also documented `codex execpolicy check`, but the packaged 0.144.1 CLI does not expose that preview subcommand even though current official documentation still prescribes it.
- Resolution on 2026-07-11: the header now identifies the policy as active, records the live symlink, and explains that inline `match`/`not_match` tests plus a clean fresh-session load are the available validation gates until the documented preview tester is included in the packaged binary. The narrow tester allow rules remain so the official command will work when available.
- Runtime evidence: Codex Doctor loads the main configuration successfully, and logs contain execution-policy activity without an observed error-level entry for `default.rules`; this is not proof that all rules match as intended.
- Severity: **Resolved documentation gap**; the deferred full-command enforcement limitation remains documented and is not a parser failure.
- Confidence: **High**.
- Benefit: an explicitly reviewed, version-tested policy is a strong complement to sandboxing and approvals.
- Cost/risk: a full rule audit is non-trivial; overly broad prefix matches can prompt too much or protect less than expected.
- Decision: retain the active policy and its inline tests. Re-run the official `codex execpolicy check` matrix when the installed distribution exposes that documented preview command; continue treating prefix rules as escalation policy rather than a complete security boundary.

## 4. MCP least privilege is not explicit

- Evidence: eight MCP servers are configured (seven enabled, `computer-use` disabled). None of the visible server tables sets `enabled_tools`, `disabled_tools`, `default_tools_approval_mode`, or per-tool approval overrides. Serena exposes symbol replacement/deletion and other write-capable tools; Linear can mutate workspace data. Playwright can act on browser state.
- Official baseline: Codex supports server allow/deny lists and server/per-tool approval modes. Because the docs lookup did not establish the omitted-value default conclusively, this audit does not claim the tools automatically bypass approval; it flags reliance on metadata/defaults rather than an explicit policy.
- Severity: **High** for write-capable MCPs; **Medium** for read-only search/docs MCPs.
- Confidence: **High**.
- Benefit: reduces accidental external writes and limits prompt-injection blast radius.
- Cost/risk: allowlists require maintenance when servers rename or add tools.
- Decision: set write-capable servers to `prompt` or `writes`, allowlist the exact tools used, and explicitly approve genuinely read-only search tools.

## 5. Always-on capability surface is much larger than observed use

- Evidence from 311 indexed rollouts (aggregate function-call names only): Exa search/fetch appeared 92 times, Context7 resolve/query 87 times, while Serena, Playwright, Mermaid, and Linear had zero recorded function calls. The installed artifact plugin skills had zero confirmed `SKILL.md` loads for Documents, PDF, Spreadsheets, Presentations, Template Creator, and Visualize; Browser had one. These counts can miss UI-only use and implicit behavior, but they reliably show no recorded tool calls for the named MCPs.
- Seven plugins are installed and enabled: Documents, PDF, Spreadsheets, Presentations, Template Creator, Visualize, and Browser.
- Severity: **Medium** (startup time, tool-selection noise, trust surface, and context overhead rather than a correctness failure).
- Confidence: **High** for direct calls; **Medium** for total user value.
- Benefit: faster startup and a smaller tool/skill decision surface.
- Cost/risk: disabled capabilities must be re-enabled or selected via a profile when needed.
- Decision: keep Exa and Context7 global. Put code-navigation/browser/rendering MCPs and artifact plugins into task profiles, or disable until needed. Do not remove them solely from this aggregate without asking the user about UI workflows.

## 6. Shared MCP intent and active transport have drifted

- Evidence: `agents/mcp.md` documents Context7 as local stdio via `npx`; active Codex config uses remote HTTP. The shared intent correctly says secrets should not be stored there, but it no longer describes the deployed transport.
- Severity: **Medium**.
- Confidence: **High**.
- Benefit: accurate intent makes Codex/Claude/OpenCode wrapper audits reproducible.
- Cost/risk: none beyond deciding which transport is canonical.
- Decision: after the credential fix, update the intent document to record the chosen non-secret remote or local transport.

## 7. Notifications likely fire through two always-on channels

- Evidence: an external `notify` command forwards every completed turn to the Computer Use client and marks the tmux pane. Separately, TUI notifications include `agent-turn-complete`, use BEL, and have condition `always`.
- Severity: **Low/Medium** usability issue.
- Confidence: **High** that both are configured; **Medium** that the desktop experience is perceived as duplicate.
- Benefit: choosing one completion channel reduces duplicate alerts while keeping approval requests visible.
- Cost/risk: disabling the wrong channel can hide background completion.
- Decision: keep the external tmux/desktop completion flow and consider restricting TUI notifications to `approval-requested`/plan prompts, or change the TUI condition to `unfocused`.

## 8. No lifecycle hooks despite a stated mechanical-enforcement gap

- Evidence: hooks are supported/enabled by the runtime, but there is no `~/.codex/hooks.json`, no inline `[hooks]` table, and `agents/hooks` contains only a placeholder. The active rule file itself records a deferred full-command enforcement hook.
- Severity: **Medium**.
- Confidence: **High**.
- Benefit: a narrowly scoped PreToolUse hook could enforce command-wrapper normalization and redact secret-path operations mechanically rather than relying only on model compliance.
- Cost/risk: hooks can block legitimate commands, add latency, and are not a universal security boundary; they require trust and careful testing.
- Decision: prototype a small audit-only hook first, collect violations, then decide whether to make it blocking.

## 9. Local history and rollout retention are uncapped and never archived

- Evidence: `history.jsonl` contains 636 entries; Codex Doctor reports 311 active rollout files using about 214.72 MB and zero archived rollouts. No `[history]` cap is configured. Logs databases are also large (`logs_2.sqlite` plus WAL were roughly 517 MB during inspection).
- Official baseline: history defaults to `save-all`; `history.max_bytes` caps the file while keeping newest entries, and `history.persistence = "none"` disables prompt history persistence.
- Severity: **Medium** privacy/disk issue.
- Confidence: **High**.
- Benefit: limits retention of potentially sensitive prompts and reduces unbounded local state.
- Cost/risk: less searchable/resumable history.
- Decision: set a deliberate `history.max_bytes`, archive valuable threads, and establish a retention policy for rollouts/logs rather than deleting ad hoc.

## 10. File-backed ChatGPT tokens are protected by mode bits but not the OS keychain

- Evidence: Codex Doctor reports file credential storage and ChatGPT tokens in `~/.codex/auth.json`; permissions are `0600`. No token was read.
- Official baseline: `cli_auth_credentials_store` supports `file`, `keyring`, or `auto`.
- Severity: **Medium** on a shared/high-risk machine; **Low** on a well-protected single-user Mac.
- Confidence: **High**.
- Benefit: keychain storage reduces exposure through filesystem copies and local file-reading mistakes.
- Cost/risk: migration/login friction and possible automation incompatibility.
- Decision: prefer `keyring` or `auto` for interactive desktop/CLI use unless a file store is intentionally required.

## 11. Heavy subagent usage has no stable custom-agent configuration

- Evidence: 216 of 311 indexed threads are `subagent:thread_spawn`, yet the live config contains no `[agents]` roles and the shared `agents/agents` directory contains only a placeholder. The user is clearly using subagents, but relies on per-prompt role text/default identities.
- Severity: **Medium** productivity/consistency gap.
- Confidence: **High**.
- Benefit: reusable researcher, reviewer, verifier, and implementation roles can standardize model/reasoning/tool scope and reduce orchestration prompt repetition.
- Cost/risk: role proliferation can make routing opaque and increase token use.
- Decision: define only 2–4 proven recurring roles, based on actual past tasks, and measure whether they improve outcomes.

## 12. No profiles and no custom TUI keymap despite divergent workloads

- Evidence: the default model and plan effort are both high, there are no profile files/tables, Vim mode is enabled, and no `[tui.keymap.*]` customization is present. Recorded workloads span CLI, VS Code, research, review guardians, and very large multi-agent runs.
- Severity: **Low/Medium** productivity and cost-control gap.
- Confidence: **High** on config; **Medium** on expected benefit.
- Benefit: `quick`, `research`, and `review` profiles could vary model/effort, MCP/plugin surface, notifications, and history. A small keymap can expose transcript, external editor, agent navigation, and other frequent actions without memorizing defaults.
- Cost/risk: more modes to remember; custom bindings can diverge from documentation.
- Decision: discuss which three workflows recur most, create profiles only for those, and customize keys only after observing real friction. Use `/keymap` to inspect effective bindings before changing anything.

## Confirmed strengths (do not “fix”)

- Codex CLI is current according to its local version metadata: 0.144.1.
- Main config and auth files are mode `0600`; the notification script is executable.
- Exa and Context7 are heavily used and justified as global research tools.
- Sandbox history is overwhelmingly `on-request`; automatic review/guardian threads explain the small `never` subset.
- The current setup already uses multi-agent orchestration heavily; recommendations should improve role consistency and cost control, not merely enable the feature.
- The external notification script is thoughtfully tmux-aware and preserves the completion payload contract.

## Diagnostic caveat

`codex doctor` reported failed DNS/reachability for ChatGPT, WebSocket, MCP HTTP endpoints, and the Homebrew version probe during this sandboxed audit. The active Codex session and remote MCP calls worked, and the manual helper reached the official host after escalation but failed its integrity-header check. Treat Doctor's reachability result as **unconfirmed environmental evidence**, not a local setup defect, until reproduced in the user's normal terminal outside the agent sandbox.
