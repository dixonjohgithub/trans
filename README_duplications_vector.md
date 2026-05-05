# Intake Platform — Duplicate Detection Build

**Status:** Planning complete; ready to begin implementation
**Repo layout:** Monorepo (`intake_platform/`)
**Framework:** Google ADK
**POC vector store:** ChromaDB (local, persistent)
**Production target:** Company-managed vector database and data pipeline

---

## What This Is

This is the planning bundle for adding a **Duplicate Detection Agent** to the Intake Platform. The Duplicate Detection Agent is the second agent in the intake pipeline, sitting between the already-built Intake Quality Agent and the downstream Classification stage.

The build is split into **two parallel workstreams** with a **locked shared contract** between them. This README orients new readers, explains how the workstreams fit together, and points to the detailed specs.

---

## The Three Documents

Read them in this order:

| # | Document | What it covers | Who reads it |
|---|---|---|---|
| 1 | [`shared-contracts-spec.md`](./shared-contracts-spec.md) | Vector record schema, embedding config, document formatter — the contract both workstreams honor | Everyone, first |
| 2 | [`jira-vectordb-spec.md`](./jira-vectordb-spec.md) | Building, populating, and maintaining the vector DB of Jira issues | Vector DB workstream owner |
| 3 | [`duplicate-detection-agent-spec.md`](./duplicate-detection-agent-spec.md) | The Duplicate Detection Agent itself: detection layers, aggregation, ADK wiring | Agent workstream owner |

The shared contract is read first because it is the **prerequisite to either build starting**. If the contract isn't locked, neither workstream can ship something the other can use.

---

## Why Two Workstreams?

The agent and the index meet at one interface: `VectorStore.query(vector, filters, k)`. As long as both sides honor the shared contract, they can develop in parallel.

**Workstreams, not repos.** "Two workstreams" means two parallel tracks of work in the same monorepo and the same VS Code workspace, not two separate repos. The directory split is in §"Repo Layout" below.

**The vector DB workstream is the longer pole.** Embedding API throughput, Jira pagination, content cleaning, and threshold calibration all take real time. Starting it on day one means a populated index is ready when the agent reaches Layer 3, instead of being the thing that blocks the demo.

**The agent workstream can begin immediately too.** Layers 1 (exact) and 2 (fuzzy) don't need vectors at all. Layer 3 can be developed against a tiny seed corpus of 10–20 hand-indexed issues until the real corpus is ready.

```
Day 0 ─────────────────────────────────────── Convergence ───── Demo
  │                                                  │
  ├─ Lock shared contract                            │
  │                                                  │
  ├─ Workstream A: Vector DB Build ──────────────────┤
  │  • Backfill, sync, validation, calibration       │
  │                                                  │
  ├─ Workstream B: Agent Build ──────────────────────┤
  │  • Layers 1+2, then Layer 3 against seed corpus  │
  │                                                  │
  └─ Workstream B points at A's index ───────────────┘
     (config change, not code change)
```

---

## How They Connect

The shared contract is small and concrete — three files in `shared/contracts/`:

| File | Defines |
|---|---|
| `vector_record.py` | `JiraIssueVectorRecord` Pydantic model — every record's shape |
| `embedding_config.py` | `EMBEDDING_CONFIG` — the locked embedding model, dimensions, task types |
| `document_formatter.py` | `format_document()` — how title + description become embedded text |

Plus two protocols (defined in their own modules but used by both workstreams):

| Module | Protocol |
|---|---|
| `shared/vector_store/base.py` | `VectorStore` — `upsert / query / delete / count` |
| `shared/embeddings/base.py` | `EmbeddingClient` — `embed_documents / embed_query` |

If both sides import from these modules and never roll their own versions, the convergence at the end is a configuration change, not a refactor.

---

## Repo Layout

```
intake_platform/
├── README.md                      # this file
├── docs/
│   ├── shared-contracts-spec.md
│   ├── jira-vectordb-spec.md
│   └── duplicate-detection-agent-spec.md
├── shared/
│   ├── contracts/                 # the locked contract — both sides import this
│   │   ├── vector_record.py
│   │   ├── embedding_config.py
│   │   └── document_formatter.py
│   ├── vector_store/
│   │   ├── base.py                # VectorStore Protocol
│   │   ├── chroma_store.py        # POC implementation
│   │   └── prod_store.py          # production stub (company vector DB)
│   ├── embeddings/
│   │   ├── base.py                # EmbeddingClient Protocol
│   │   └── adk_embeddings.py      # POC: Gemini via ADK
│   ├── jira_client/
│   │   ├── base.py                # JiraClient Protocol
│   │   ├── rest_client.py         # for bulk backfill
│   │   └── mcp_client.py          # for incremental sync + dev introspection
│   ├── config_loader/             # YAML loading + per-intake-type resolution
│   └── observability/             # structured logging
├── agents/
│   ├── intake_quality/            # already built (move in if not already)
│   └── duplicate_detection/       # new — see duplicate-detection-agent-spec.md
│       ├── agent.py               # ADK agent
│       ├── detectors/
│       │   ├── exact.py           # Layer 1
│       │   ├── fuzzy.py           # Layer 2
│       │   └── semantic.py        # Layer 3
│       ├── intake_input/          # parses Intake Quality Agent JSON
│       ├── rerank/                # Gemini re-ranker
│       ├── aggregator.py
│       ├── normalize.py
│       ├── schemas.py
│       ├── config/
│       │   ├── default.yaml
│       │   └── intake_types/      # per-intake-type config + field_mapping
│       └── tests/
├── jira_indexer/                  # new — see jira-vectordb-spec.md
│   ├── cleaner.py
│   ├── document_formatter.py      # thin wrapper around shared formatter
│   ├── backfill.py
│   ├── sync.py
│   ├── reconciliation.py
│   ├── hash_cache.py
│   ├── checkpoint.py
│   ├── config/
│   │   ├── backfill.yaml
│   │   └── sync.yaml
│   └── tests/
├── orchestration/
│   └── pipeline.py                # wires the agents together
├── scripts/
│   ├── run_backfill.py            # entrypoint for vector DB build
│   ├── run_sync_loop.py
│   ├── calibrate_thresholds.py    # produces threshold values for agent YAML
│   ├── validate_index.py
│   └── inspect_neighbors.py       # interactive
├── tests/
│   └── integration/               # end-to-end across both workstreams
├── data/                          # gitignored
│   ├── chroma/
│   ├── hash_cache.sqlite
│   ├── backfill_state.json
│   └── sync_state.json
├── pyproject.toml
└── requirements.txt
```

### One Repo, One VS Code Workspace

Both workstreams live in the same repo and share a single VS Code workspace. They're separated by **directory**, not by repo or workspace.

| Folder | Owner | Notes |
|---|---|---|
| `shared/contracts/` | 🤝 Joint | Locked early; rare changes after, both owners sign off on any PR |
| `shared/vector_store/`, `shared/embeddings/`, `shared/jira_client/` | Vector DB workstream writes; agent imports | Both sides use the protocols; only the Vector DB workstream evolves the implementations |
| `jira_indexer/` | Vector DB workstream | |
| `agents/duplicate_detection/` | Agent workstream | |
| `agents/duplicate_detection/config/intake_types/` | Agent workstream | Threshold values written here come from the Vector DB workstream's calibration script |
| `scripts/run_backfill.py`, `calibrate_thresholds.py`, `validate_index.py`, `inspect_neighbors.py` | Vector DB workstream | |
| `tests/integration/` | 🤝 Joint | End-to-end tests across both workstreams |

This gives the two devs disjoint working directories, so day-to-day they don't collide. Use feature branches per workstream and merge to `main` when each phase passes CI.

**Why same repo, same workspace:**
- The shared contract is imported by both sides. In a single workspace, the language server flags contract violations immediately; across repos, you find out at integration time.
- Convergence is a config change (point the agent at the populated collection), not a cross-repo coordination event.
- Integration tests, fixture sets, and CI run across both workstreams in one pass.
- Atomic cross-cutting changes (e.g., adding a new metadata field) ship as one PR.

**Recommended `.vscode/settings.json`:**

```json
{
  "python.analysis.extraPaths": ["./shared", "./agents", "./jira_indexer"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests", "agents", "jira_indexer", "shared"],
  "python.analysis.typeCheckingMode": "basic",
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "data/chroma": true
  }
}
```

This lets Pylance resolve cross-package imports, runs pytest discovery across all three packages, and hides the local Chroma data directory from the file tree. Single-root workspace is fine; multi-root is unnecessary.

The Intake Quality Agent already exists; its code moves under `agents/intake_quality/` if it's not there already (preserve git history with `git subtree` or `git filter-repo`). The Duplicate Detection Agent and the Jira indexer are new packages alongside it.

---

## Workstream Sequencing

### Phase 0: Lock the Contract (1–3 days, both owners together)

Required before either workstream begins coding:

1. Resolve the open questions in `shared-contracts-spec.md` §11 (model identifier, dimensions, max tokens, boilerplate list, code-heavy issue types, LOB field source, Epic linkage field)
2. Write `shared/contracts/vector_record.py`, `embedding_config.py`, `document_formatter.py`
3. Write unit tests for `document_formatter.py`
4. Both owners sign off on the PR

### Phase 1: Parallel Builds (work runs concurrently)

**Workstream A — Vector DB**
Follow `jira-vectordb-spec.md` §9. Headline milestones:
- Embedding client, vector store adapter, Jira REST client
- Content cleaning module (highest-leverage code in the workstream)
- Backfill against one project end-to-end
- Full backfill across in-scope projects
- Sanity validation (`validate_index.py`)
- Threshold calibration (`calibrate_thresholds.py`) — produces concrete numbers for the agent's YAML
- Embedding quality review

**Workstream B — Agent**
Follow `duplicate-detection-agent-spec.md` §12. Headline milestones:
- I/O schemas, intake input parser, field mapper
- Layer 1 (exact) wired into ADK skeleton
- Layer 2 (fuzzy) with RapidFuzz
- Layer 3 (semantic) against a 10–20 issue seed corpus
- Aggregator and verdict logic
- YAML config loader with per-intake-type field mappings

### Phase 2: Convergence (~1 day if contract held)

1. Workstream A delivers a populated collection plus calibrated threshold values
2. Workstream B's `chroma_path` config points at A's collection
3. Workstream B's per-intake-type YAMLs receive the threshold values from A
4. Run agent's startup compatibility check (`verify_collection_compatibility` from §7 of contracts spec)
5. Run integration test fixture set against the real corpus
6. Tune any thresholds that need adjustment based on integration test results

### Phase 3: Sync, Observability, Hardening

- Incremental sync loop (POC only — production data pipeline takes over later)
- Reconciliation job (daily orphan detection)
- Structured logs per agent invocation
- Acceptance criteria checklists in each spec

---

## Design Principles

A few principles cut across all three specs and are worth stating once:

**1. The contract is sacred.** Both workstreams import from `shared/contracts/`. Neither defines its own version of `JiraIssueVectorRecord`, embedding settings, or document formatting. Drift here causes silent score corruption.

**2. Abstract the swappable, not the stable.** ChromaDB and the company vector DB hide behind `VectorStore`. The Gemini embedding model and the production embedding service hide behind `EmbeddingClient`. The Jira REST API and the internal MCP server hide behind `JiraClient`. The agents themselves don't import these implementations directly — they use the protocols.

**3. Provenance in every record.** Every vector record carries the model name, version, task type, content hash, and schema version it was built with. The agent verifies this at startup. Mysterious low-quality results trace back to provenance mismatches more often than to algorithm problems.

**4. Bias toward flagging, not blocking.** A false positive (blocking a legitimate intake) costs more than a false negative (missing a duplicate). When detection layers disagree, the aggregator prefers `flag_for_review` over `block`.

**5. Degrade gracefully.** If embeddings fail, fall back to Layers 1+2. If the vector store is empty, return Layers 1+2 results. If the LLM re-ranker times out, use raw cosine similarity. The agent does not fail closed and block submissions because of its own infrastructure problems.

**6. POC is not production, and that's fine.** ChromaDB, the in-repo sync loop, the local SQLite hash cache — all of these are POC-only. The production migration is a swap of the vector store adapter and the handoff of sync to the company data pipeline. The contracts and the agent logic do not change.

---

## Key Risks (and Where They're Addressed)

| Risk | Where it's addressed |
|---|---|
| Embedding model drift between corpus and queries | `shared-contracts-spec.md` §3, §7 (compatibility check) |
| Boilerplate templates inflating similarity scores | `jira-vectordb-spec.md` §5.2, §7.3 (quality review) |
| Threshold guesses instead of empirical values | `jira-vectordb-spec.md` §7.2 (calibration) |
| Schema changes breaking the agent silently | `shared-contracts-spec.md` §8 (versioning policy) |
| Field IDs varying by intake type | `duplicate-detection-agent-spec.md` §7.1 (field_mapping config) |
| Production vector DB being different from POC | `VectorStore` protocol; `prod_store.py` adapter stub |
| Long-running backfill failing midway | `jira-vectordb-spec.md` §5.3 (checkpointing) |
| Auto-blocking legitimate submissions | `duplicate-detection-agent-spec.md` §3.5 (bias toward flag_for_review) |

---

## Glossary

- **Intake Quality Agent** — the upstream agent (already built) that validates and normalizes intake form responses. Produces the JSON input for Duplicate Detection.
- **Duplicate Detection Agent** — the agent being built per `duplicate-detection-agent-spec.md`. Determines whether an intake is a duplicate of an existing Jira issue.
- **Layer 1 / 2 / 3** — exact / fuzzy / semantic detection methods. All three run for every intake.
- **Verdict** — agent output: `none | possible | likely | exact`.
- **Recommended action** — agent output: `proceed | link_related | merge_suggestion | flag_for_review | block`.
- **Field mapping** — per-intake-type YAML that maps intake question IDs to detection roles (title, description, requester, etc.).
- **Convergence contract** — the shared contract in `shared/contracts/` that both workstreams honor.
- **Provenance fields** — `embedding_model`, `embedding_model_version`, `embedding_task_type`, `content_hash`, `indexed_ts`, `schema_version` on every record.

---

## Out of Scope for This Build

- Webhook-driven Jira sync (production data pipeline will own this)
- The company vector DB integration (interface only — `prod_store.py` is a stub)
- UI for reviewing duplicate decisions
- Threshold auto-tuning from reviewer feedback
- Cross-language embeddings
- Cross-tenant isolation
- HA / multi-node deployment

These are documented for the production roadmap but are not POC deliverables.

---

## Quick Start for New Readers

If you're picking this up cold:

1. Read this README to the end (you're almost there)
2. Read `shared-contracts-spec.md` — small, concrete, sets the foundation
3. Read whichever of `jira-vectordb-spec.md` or `duplicate-detection-agent-spec.md` matches the workstream you're joining
4. Skim the other one so you understand what your counterpart is building
5. Find the open questions in `shared-contracts-spec.md` §11 — if those aren't answered yet, that's the first conversation to have

If you're picking this up hot in the middle of the build:

1. Check the contract version in `shared/contracts/vector_record.py` — has it been bumped recently?
2. Run the agent's `verify_collection_compatibility` check — does the collection match the contract?
3. Read the latest entries in `data/sync_state.json` and `data/backfill_state.json` to see where the indexer left off
4. Check `tests/calibration_plot.png` for the most recent threshold calibration results
