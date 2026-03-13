# takopi-memory Plugin Spec

## Goal

Provide persistent, project-scoped memory for Takopi so agents can recall prior
decisions, runbooks, architecture notes, and curated facts without the user
re-pasting context every session.

## Non-Goals

- General web crawling
- Opaque long-term chat logs with no provenance
- Fully autonomous memory writes with no review surface

## Product Shape

The plugin should support two storage modes behind one interface:

1. `markdown`
   Source of truth is markdown files in a configured knowledge directory.
2. `hybrid`
   Markdown remains canonical, but the plugin also builds a local retrieval
   index for semantic search.

Hard cutover: do not support parallel legacy memory formats.

## User Experience

### Primary Commands

- `/memory search <query>`
- `/memory add <title>` with body from the triggering message or stdin
- `/memory show <memory-id>`
- `/memory update <memory-id>`
- `/memory forget <memory-id>`
- `/memory rebuild-index`

### Expected Behavior

- Search returns short answers plus citations to the underlying memory entries.
- Add/update writes markdown files with frontmatter, then refreshes the index.
- Forget archives or deletes the canonical markdown entry and drops it from the
  index immediately.
- Search can be scoped by project, tags, or path.

## Canonical Storage

Store entries under a dedicated folder such as:

```text
.takopi/memory/
  architecture/
  decisions/
  runbooks/
  glossary/
```

Each entry is a markdown file with frontmatter:

```yaml
id: mem_20260313_abc123
title: Slack routing rules
project: takopi-slack
tags: [slack, routing]
updated_at: 2026-03-13T10:30:00Z
source:
  kind: manual
  author: richard
```

The body contains the actual knowledge and optional sections such as
`Context`, `Decision`, `Implications`, and `References`.

## Retrieval Architecture

### MVP

- Chunk markdown files by heading/section.
- Build a local SQLite or JSONL index with:
  - `memory_id`
  - `path`
  - `title`
  - `project`
  - `tags`
  - `section`
  - `content`
- Retrieve with hybrid scoring:
  - exact path/title/tag matches
  - keyword search
  - optional embedding similarity when configured

### Ranking Rules

- Prefer entries from the active project.
- Prefer exact tag/title hits over semantic-only matches.
- Never answer without citing at least one memory entry.
- Deduplicate chunks from the same memory file before final output.

## Write Path

### Manual Capture

- User invokes `/memory add` or `/memory update`.
- Plugin writes a markdown file and updates the retrieval index.

### Assisted Capture

- Agent proposes a memory save after a run that produced a durable decision.
- User confirms before the write.

## Config

```toml
[plugins.memory]
root_dir = ".takopi/memory"
mode = "hybrid"
default_project = "takopi-slack"
embedding_provider = "openai"
embedding_model = "text-embedding-3-large"
max_results = 8
auto_suggest_saves = true
```

If `mode = "markdown"`, semantic embeddings are disabled and search falls back
to lexical ranking only.

## Safety

- Canonical data must remain human-readable markdown.
- Every result must include source paths.
- Writes should be append-or-rewrite through the canonical markdown file only.
- No silent memory mutation from background runs.

## Implementation Phases

### Phase 1

- Markdown-backed CRUD
- Lexical search
- Citations

### Phase 2

- Embedding index
- Hybrid ranking
- Auto-suggest memory capture

### Phase 3

- TTL / stale memory detection
- Project-level memory packs
- Optional sync to external stores

## Open Questions

- Whether memory writes should land inside the repo or under `~/.takopi`
- Whether embeddings should be required or optional by deployment
- Whether memory entries should support explicit ACLs per project
