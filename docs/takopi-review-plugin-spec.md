# takopi-review Plugin Spec

## Goal

Create a review orchestration plugin that runs multiple reviewer agents
independently, consolidates their findings, and optionally implements accepted
fixes in the workspace.

Initial reviewer set:

- Claude
- Codex
- Devin

## Non-Goals

- Blindly applying every agent suggestion
- Posting duplicate review comments from each reviewer directly to GitHub
- Long-lived reviewer state shared across runs

## Product Shape

The plugin runs in four stages:

1. Collect review context
2. Run reviewer agents in parallel
3. Meta-review and deduplicate findings
4. Apply selected fixes and generate a final report

Hard cutover: findings should normalize into one schema; do not preserve
provider-specific output formats downstream.

## Trigger Modes

- `/review diff`
- `/review pr <number|url>`
- `/review commit <sha>`
- `/review fix`

## Inputs

- Git diff or PR ref
- Repo root and current branch
- Optional focus areas such as `security`, `performance`, `tests`
- Reviewer credentials / CLI availability

## Normalized Finding Schema

Each reviewer output must be converted into:

```json
{
  "reviewer": "claude",
  "title": "Missing authorization check",
  "priority": 1,
  "confidence": 0.84,
  "file": "src/example.py",
  "start_line": 42,
  "end_line": 45,
  "summary": "Route allows any Slack user to trigger destructive actions.",
  "suggested_fix": "Check allowed_user_ids before dispatch."
}
```

## Review Flow

### Stage 1: Context Collection

- Resolve the review target.
- Capture the diff, changed files, test surface, and repo instructions.
- Build one reviewer bundle shared across all providers.

### Stage 2: Parallel Reviews

- Launch Claude, Codex, and Devin with the same review bundle.
- Run each in an isolated worktree or temp branch to avoid state bleed.
- Enforce per-reviewer timeout and cost ceilings.

### Stage 3: Meta-Review

- Merge all findings into the normalized schema.
- Group duplicates by file/line/semantic similarity.
- Rank by:
  - severity
  - reviewer agreement
  - confidence
  - user-requested focus areas
- Emit one consolidated review report.

The meta-reviewer should explicitly mark findings as:

- `accepted`
- `needs-human-triage`
- `rejected`

## Fix Flow

`/review fix` operates only on `accepted` findings.

### Fix Strategy

- Choose one implementation agent, defaulting to Codex.
- Apply fixes in the main workspace or a dedicated fix worktree.
- Run targeted verification after each fix batch.
- Re-run the meta-review on touched areas when feasible.

## Outputs

### Review Report

- Consolidated findings table
- Agreement matrix by reviewer
- Recommended fix order
- Testing gaps

### Fix Report

- Findings addressed
- Files changed
- Verification results
- Residual open findings

## Config

```toml
[plugins.review]
default_fixer = "codex"
reviewers = ["claude", "codex", "devin"]
timeout_s = 900
max_parallel_reviews = 3
post_github_comments = false
auto_fix = false
```

## Safety

- Never auto-push fixes.
- Never auto-merge.
- Keep reviewer raw output available for audit.
- Require explicit user action before posting external comments or applying
  fixes when findings include low-confidence or conflicting conclusions.

## Implementation Notes

- Reviewer adapters should be thin wrappers around each provider CLI/API.
- Consolidation logic should live in a provider-agnostic core package.
- Fix application should reuse existing Takopi command execution infrastructure
  instead of shelling out ad hoc.

## Implementation Phases

### Phase 1

- Diff-based review
- Claude/Codex adapters
- Consolidated markdown report

### Phase 2

- Devin adapter
- Duplicate clustering
- `/review fix` for accepted findings

### Phase 3

- GitHub comment sync
- Historical reviewer quality tracking
- Reviewer selection by repo or language

## Open Questions

- Whether Devin should run as a synchronous reviewer or an async delegated job
- Whether fixes should require unanimous agreement or majority agreement
- Whether the meta-reviewer should be a distinct agent or deterministic logic
