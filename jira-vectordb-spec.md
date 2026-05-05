# Jira Vector Database — Build Specification (Parallel Workstream)

**Status:** Ready for implementation
**Workstream:** Independent — runs in parallel with the Duplicate Detection Agent build
**POC Vector Store:** ChromaDB (local, persistent)
**Production Target:** Company-managed vector database and data pipeline
**Companion Document:** `duplicate-detection-agent-spec.md`

---

## 1. Purpose

Build, populate, and maintain a vector database of Jira issues that the Duplicate Detection Agent (and future agents) will query for semantic similarity. This workstream is decoupled from agent development — the only thing the two streams share is the **convergence contract** in §3.

The deliverable of this workstream is:
1. A populated ChromaDB collection containing all in-scope Jira issues with embeddings and metadata
2. A repeatable backfill pipeline
3. An incremental sync loop for keeping the index fresh
4. A test/evaluation fixture set used to calibrate similarity thresholds
5. A set of validation scripts proving the index returns sensible results

This workstream can begin **day 1** alongside the agent build. They converge when the agent points its `VectorStore` adapter at the populated collection.

---

## 2. Why Parallel

The vector DB build is the longest-running piece of the duplicate detection system:
- Embedding API calls have throughput limits
- Jira pagination and content cleaning take time to get right
- Threshold calibration needs a real corpus, not mocks
- Discovering that descriptions are 80% boilerplate template happens at corpus-build time, not agent-build time

The agent and the index meet only at one interface (`VectorStore.query(...)`). As long as both sides honor the convergence contract, they can develop independently.

---

## 3. Convergence Contract (LOCK FIRST, BEFORE EITHER STREAM STARTS)

These specifications MUST be agreed and committed to `shared/contracts/` before either workstream begins coding. Changes after that point require a coordinated PR.

### 3.1 Record Schema

Each record in the vector store represents one Jira issue.

```python
# shared/contracts/vector_record.py
from pydantic import BaseModel
from typing import Optional

class JiraIssueVectorRecord(BaseModel):
    # Identity
    id: str                          # Jira issue key, e.g. "AIPLAT-1234"

    # Vector
    embedding: list[float]           # 768-dim (or whatever model produces)

    # Document text (what was embedded)
    document: str                    # see §3.3 for format

    # Metadata (Chroma requires primitives only)
    project: str                     # "AIPLAT"
    status: str                      # "In Progress"
    status_category: str             # "to-do" | "indeterminate" | "done"
    issue_type: str                  # "Story" | "Bug" | "Epic" | etc.
    components: str                  # comma-joined: "data-pipeline,ml"
    labels: str                      # comma-joined: "migration,bigquery"
    requester: str                   # username/email of reporter
    assignee: str                    # may be empty
    lob: str                         # line of business if available, else ""
    created_ts: int                  # unix seconds
    updated_ts: int                  # unix seconds
    resolved_ts: int                 # unix seconds, 0 if unresolved
    resolution: str                  # "" if unresolved, else e.g. "Done", "Won't Do"
    parent_key: str                  # parent Epic key if any, else ""

    # Provenance (required)
    embedding_model: str             # e.g. "gemini-embedding-001"
    embedding_model_version: str     # specific version string
    embedding_task_type: str         # "RETRIEVAL_DOCUMENT"
    content_hash: str                # SHA-256 of source text — for change detection
    indexed_ts: int                  # when this record was last embedded
    schema_version: str              # "1.0" — bump on contract changes
```

**Field rules:**
- All metadata values must be `str | int | float | bool` (Chroma constraint)
- Lists are comma-joined; filtering on list membership is done in the application layer
- Empty values are empty strings, not `None` (Chroma metadata constraint)
- Timestamps are unix seconds, not ISO strings, so range filters work

### 3.2 Embedding Model

Both workstreams MUST use the same embedding model with the same task-type convention.

| Setting | Value |
|---|---|
| Model | `gemini-embedding-001` (or company-approved equivalent via Google ADK) |
| Dimensions | Native model output (typically 768 or 3072) |
| Distance | Cosine |
| Document task type (indexing) | `RETRIEVAL_DOCUMENT` |
| Query task type (agent queries) | `RETRIEVAL_QUERY` |

The model name and version MUST be recorded in every record's metadata. The agent MUST verify on startup that the collection's recorded model matches what it's about to query with. Mismatched models produce garbage similarity scores.

### 3.3 Document Text Format

The text that gets embedded:

```
{cleaned_title}

{cleaned_description}
```

Where:
- Single blank line between title and description
- Title is normalized: trimmed, internal whitespace collapsed
- Description has Jira wiki markup converted to plain text (see §5.2)
- Total truncated to model's max input tokens (typically 2048 or 8192)
- If description is empty, just the title is embedded

### 3.4 Distance Metric

- **Cosine similarity**, expressed as `1 - cosine_distance`
- Scores in `[0.0, 1.0]` where 1.0 means identical, 0.0 means orthogonal
- Chroma is configured with `metadata={"hnsw:space": "cosine"}` at collection creation
- Scores returned to the agent are similarities, not distances — the adapter converts

### 3.5 Collection Naming

- POC collection name: `jira_issues`
- One collection, metadata-filtered for scope (not many collections)
- Schema version tracked in collection metadata: `metadata={"schema_version": "1.0"}`

---

## 4. Data Sources — REST vs MCP

The company has two ways to access Jira: the REST API directly, and an internal Jira MCP server. Use both, for different jobs.

### 4.1 Jira REST API — Bulk Backfill

Use REST for the initial 50K+ issue backfill.

**Why REST for backfill:**
- Predictable pagination control (`startAt`, `maxResults`)
- Precise JQL queries for scoping
- Deterministic rate-limit handling and retries
- Resumable from a checkpoint
- Parallelizable across projects

**Endpoints needed:**
- `GET /rest/api/3/search` (or `/rest/api/2/search` depending on Jira version) — paginated issue list with JQL
- `GET /rest/api/3/issue/{issueIdOrKey}` — full issue detail when search response is truncated
- `GET /rest/api/3/field` — field metadata, run once at startup to confirm field IDs

**Auth:** company-standard service account with read access to in-scope projects. Store credentials per company secrets policy. Never check credentials into the repo.

### 4.2 Internal Jira MCP — Incremental Sync and Dev Loop

Use the MCP server for:
- The incremental sync loop ("fetch updates from the last 15 minutes")
- Ad-hoc dev introspection ("pull issue X and let me look at its structure")
- One-off backfill of small projects where REST setup overhead isn't worth it

**Why MCP for these:**
- Already authenticated, already mapped to company conventions
- Returns normalized issue data — less field-mapping work
- Convenient when developing in Cursor or Claude Code

**Tradeoff:** MCP servers are typically tuned for interactive agent use, not 50K-record batch extraction. Benchmark before committing to it for the full backfill.

### 4.3 Recommended Split

| Phase | Tool | Why |
|---|---|---|
| Initial full backfill | REST | Throughput, resumability |
| Incremental sync (every N min) | MCP | Convenience, already auth'd |
| Dev introspection | MCP | Fast iteration |
| Re-backfill on schema change | REST | Bulk operation |

Build both clients behind a `JiraClient` interface so the rest of the pipeline doesn't care which is being used.

---

## 5. Backfill Pipeline

### 5.1 Scope Selection (JQL)

```jql
project in (AIPLAT, AIINIT, ...)
AND (
  statusCategory != Done
  OR resolved >= -365d
)
ORDER BY updated DESC
```

Open issues + closed issues from the last 365 days. Adjust per company policy.

Configurable via YAML:

```yaml
# config/backfill.yaml
projects:
  - AIPLAT
  - AIINIT
  - DATAPLAT
include_open: true
include_closed: true
closed_lookback_days: 365
batch_size: 100               # JQL pagination size
embedding_batch_size: 50      # how many to embed per API call
parallelism: 4                # how many projects to process concurrently
```

### 5.2 Content Cleaning

Jira descriptions are noisy. Before embedding:

1. **Strip Jira wiki markup** — convert `{code}`, `{quote}`, `{noformat}`, `*bold*`, `_italic_`, `[link|url]`, table syntax to plain text equivalents (use `jira2markdown` or similar, or a regex-based stripper)
2. **Strip ADF (Atlassian Document Format)** — if Jira returns description as ADF JSON, flatten it to plain text
3. **Strip boilerplate templates** — many orgs have Jira issue templates with headers like "Acceptance Criteria:", "Definition of Done:". These add noise. Configurable list of header phrases to drop with their following content, or to dampen
4. **Strip code blocks** — for non-bug issues, code blocks are usually noise. For bugs, keep them. Configurable per issue type
5. **Strip URLs** — replace with their anchor text or remove entirely
6. **Collapse whitespace** — multiple newlines to one blank line, runs of spaces to single
7. **Truncate** — to model's max token count, prefer truncating description over title

The cleaning logic is its own module with unit tests. Bad cleaning is a silent killer of embedding quality.

### 5.3 Embedding

```python
# Pseudocode
for batch in batches_of(issues, embedding_batch_size):
    documents = [format_document(issue) for issue in batch]
    hashes = [sha256(doc) for doc in documents]

    # Skip already-indexed unchanged issues
    new_or_changed = [
        (issue, doc, h) for issue, doc, h in zip(batch, documents, hashes)
        if h != cached_hash.get(issue.key)
    ]
    if not new_or_changed:
        continue

    embeddings = embedding_client.embed_documents(
        texts=[item[1] for item in new_or_changed],
        task_type="RETRIEVAL_DOCUMENT",
    )

    records = [
        build_vector_record(issue, doc, h, emb)
        for (issue, doc, h), emb in zip(new_or_changed, embeddings)
    ]
    vector_store.upsert(records)
    update_hash_cache({r.id: r.content_hash for r in records})
```

**Caching:** persist `{issue_key: content_hash}` in a SQLite file or simple JSON. On re-run, skip embedding for issues whose content hasn't changed. Saves time and money.

**Rate limiting:** use `tenacity` for exponential backoff on 429s. Log retries.

**Checkpointing:** after each batch, write progress to `./data/backfill_state.json`:
```json
{
  "started_at": "2026-05-05T14:00:00Z",
  "projects_completed": ["AIPLAT"],
  "current_project": "AIINIT",
  "current_project_offset": 4500,
  "total_indexed": 12480,
  "errors": []
}
```
On crash/restart, resume from checkpoint.

### 5.4 Validation After Backfill

The backfill script ends by running automated sanity checks (see §7). Backfill is not "complete" until checks pass.

---

## 6. Incremental Sync Loop

### 6.1 Strategy

A separate long-running process (or scheduled cron) that runs every 5–15 minutes:

```
1. Read last_sync_ts from ./data/sync_state.json
2. JQL: project in (...) AND updated >= "{last_sync_ts}"
3. For each returned issue:
   a. Compute content_hash
   b. If issue is in vector store with same hash → skip
   c. If issue is in vector store with different hash → re-embed, upsert
   d. If issue is new → embed, insert
4. Detect deletions: issues that moved out of scope (e.g., archived, deleted)
   - Periodic full reconciliation: query all in-scope keys, compare to collection IDs, delete orphans
5. Write new last_sync_ts
```

### 6.2 Sync State

```json
// ./data/sync_state.json
{
  "last_sync_ts": 1730500000,
  "last_full_reconciliation_ts": 1730000000,
  "last_run_status": "success",
  "last_run_duration_ms": 4200,
  "issues_added": 3,
  "issues_updated": 7,
  "issues_deleted": 0
}
```

### 6.3 Full Reconciliation Cadence

Run a full reconciliation (compare all in-scope Jira keys against the collection, find orphans/missing) once daily. Catches webhook misses, Jira-side deletions, and scope changes.

### 6.4 Production Note

In production, the company data pipeline takes over sync. This loop is **POC only**. Document the contract (record schema, refresh cadence) so the production pipeline can match it, but don't try to ship this sync loop to production.

---

## 7. Validation Tests (Required Deliverable)

These tests run against the populated collection and serve two purposes: (1) confirm the corpus is good, (2) calibrate similarity thresholds for the agent.

### 7.1 Sanity Checks (Automated)

Run after every backfill:

```python
def test_exact_title_returns_top1():
    """Querying with an exact known title should return that issue at rank 1."""
    issue = random.choice(known_issues)
    results = store.query(embed(issue.title + "\n\n" + issue.description), k=5)
    assert results[0].id == issue.id
    assert results[0].score > 0.99

def test_unrelated_topics_have_low_similarity():
    """Queries about clearly unrelated topics should not have high scores."""
    results = store.query(embed("How do I bake sourdough bread"), k=5)
    assert results[0].score < 0.6, "Unrelated query scored too high — model issue?"

def test_metadata_filters_work():
    """Filter by project should only return issues from that project."""
    results = store.query(
        embed("any query"),
        filters={"project": "AIPLAT"},
        k=20,
    )
    assert all(r.metadata["project"] == "AIPLAT" for r in results)

def test_status_category_filter():
    results = store.query(
        embed("any query"),
        filters={"status_category": {"$ne": "done"}},
        k=20,
    )
    assert all(r.metadata["status_category"] != "done" for r in results)

def test_date_range_filter():
    one_year_ago = int(time.time()) - 365*86400
    results = store.query(
        embed("any query"),
        filters={"created_ts": {"$gte": one_year_ago}},
        k=20,
    )
    assert all(r.metadata["created_ts"] >= one_year_ago for r in results)

def test_collection_size_matches_jira():
    """Collection count should match the number of in-scope Jira issues (±tolerance)."""
    jira_count = count_in_scope_issues_via_jql()
    collection_count = store.count()
    assert abs(jira_count - collection_count) < jira_count * 0.01  # 1% tolerance

def test_embedding_model_recorded():
    """Every record should have model provenance."""
    sample = store.sample(100)
    for r in sample:
        assert r.metadata["embedding_model"] == EXPECTED_MODEL
        assert r.metadata["embedding_model_version"] == EXPECTED_VERSION
```

### 7.2 Threshold Calibration (Manual + Automated)

This is what gives the agent its YAML threshold values.

**Step 1: Build a labeled fixture set**

Hand-pick from Jira history:
- 20 known **duplicate pairs** (issues that were marked as dupes, or that the team agrees are dupes)
- 20 known **related-but-distinct pairs** (same area, different scope)
- 20 known **unrelated pairs** (random pairs from the corpus)

Store in `tests/fixtures/duplicate_pairs.json`:

```json
[
  {
    "label": "duplicate",
    "issue_a": "AIPLAT-1234",
    "issue_b": "AIPLAT-1267",
    "notes": "Both BigQuery migrations of the churn pipeline, filed by different teams"
  },
  {
    "label": "related",
    "issue_a": "AIPLAT-100",
    "issue_b": "AIPLAT-101",
    "notes": "Both touch the data pipeline but different features"
  },
  {
    "label": "unrelated",
    "issue_a": "AIPLAT-50",
    "issue_b": "AIPLAT-9999",
    "notes": "Random pairing"
  }
]
```

**Step 2: Compute similarity for every pair**

```python
def calibrate_thresholds():
    pairs = load_fixture("duplicate_pairs.json")
    results = []
    for pair in pairs:
        a = store.get(pair["issue_a"])
        b = store.get(pair["issue_b"])
        sim = cosine_similarity(a.embedding, b.embedding)
        results.append({"label": pair["label"], "similarity": sim})

    duplicates = [r["similarity"] for r in results if r["label"] == "duplicate"]
    related = [r["similarity"] for r in results if r["label"] == "related"]
    unrelated = [r["similarity"] for r in results if r["label"] == "unrelated"]

    print(f"Duplicates:  min={min(duplicates):.3f}  median={median(duplicates):.3f}  max={max(duplicates):.3f}")
    print(f"Related:     min={min(related):.3f}  median={median(related):.3f}  max={max(related):.3f}")
    print(f"Unrelated:   min={min(unrelated):.3f}  median={median(unrelated):.3f}  max={max(unrelated):.3f}")
```

**Step 3: Pick thresholds from the distributions**

- `semantic_block` ≈ minimum of the duplicate distribution (or ~5th percentile if there are outliers)
- `semantic_flag` ≈ maximum of the unrelated distribution (above this, it's at least suspicious)
- The gap between these is where human review lives

Write these into `config/intake_types/<type>.yaml` for the agent.

**Step 4: Plot the distributions**

A simple histogram (matplotlib or plain text) saved as `tests/calibration_plot.png`. Visual review catches surprises that summary stats hide.

### 7.3 Embedding Quality Smell Test (Manual)

Pick 5 representative issues. For each, look at the top 10 nearest neighbors:

- Are the neighbors actually related, or is the model picking up superficial features?
- Common failure modes:
  - All neighbors share the same boilerplate template (cleaning insufficient)
  - All neighbors are from the same author (description is too short, model defaults to author signal)
  - All neighbors are the same length (description quality issue)
  - Neighbors are conceptually unrelated but share a prominent term

Document findings in `tests/embedding_quality_review.md`. If quality is poor, fix cleaning (§5.2) and re-embed.

---

## 8. Project Structure

This workstream lives in the same monorepo as the agent (per discussion), in a separate package:

```
intake_platform/
├── shared/
│   ├── contracts/
│   │   ├── vector_record.py        # JiraIssueVectorRecord — THE contract
│   │   └── embedding_config.py     # locked model/task-type names
│   ├── jira_client/
│   │   ├── base.py                 # JiraClient Protocol
│   │   ├── rest_client.py
│   │   └── mcp_client.py
│   ├── embeddings/
│   │   ├── base.py                 # EmbeddingClient Protocol
│   │   └── adk_embeddings.py       # Gemini via ADK
│   └── vector_store/
│       ├── base.py                 # VectorStore Protocol (shared with agent)
│       ├── chroma_store.py
│       └── prod_store.py           # production stub
├── jira_indexer/                   # this workstream
│   ├── __init__.py
│   ├── cleaner.py                  # content cleaning (§5.2)
│   ├── document_formatter.py       # title + description format (§3.3)
│   ├── backfill.py                 # full backfill pipeline (§5)
│   ├── sync.py                     # incremental sync loop (§6)
│   ├── reconciliation.py           # full reconciliation
│   ├── hash_cache.py               # content_hash cache for skip-unchanged
│   ├── checkpoint.py               # resume support
│   ├── config/
│   │   ├── backfill.yaml
│   │   └── sync.yaml
│   └── tests/
│       ├── test_cleaner.py
│       ├── test_document_formatter.py
│       ├── test_backfill_resumes.py
│       ├── test_sync_idempotent.py
│       └── fixtures/
│           ├── sample_jira_issues_raw.json
│           ├── sample_adf_descriptions.json
│           └── duplicate_pairs.json
├── scripts/
│   ├── run_backfill.py             # entrypoint: python -m scripts.run_backfill
│   ├── run_sync_loop.py            # entrypoint: python -m scripts.run_sync_loop
│   ├── calibrate_thresholds.py     # §7.2
│   ├── validate_index.py           # §7.1
│   └── inspect_neighbors.py        # §7.3 — interactive
└── data/                           # gitignored
    ├── chroma/
    ├── hash_cache.sqlite
    ├── backfill_state.json
    └── sync_state.json
```

---

## 9. Build Order

1. **Lock the convergence contract** (§3) — `shared/contracts/` PR, both workstreams sign off
2. **Embedding client + cache** — `shared/embeddings/`, with unit tests
3. **VectorStore protocol + ChromaVectorStore** — `shared/vector_store/`
4. **Jira REST client** — `shared/jira_client/rest_client.py`
5. **Content cleaner + document formatter** — with extensive unit tests against fixture issues; this is the highest-leverage code in the workstream
6. **Hash cache + checkpoint** — small, but de-risks long-running backfills
7. **Backfill pipeline** — wire it all together, run against ONE small project end-to-end
8. **Validation scripts** — §7.1 sanity checks
9. **Run full backfill** — across all in-scope projects; iterate on cleaning if quality issues surface
10. **Threshold calibration** — §7.2; produce the threshold values for the agent's YAML config
11. **Embedding quality review** — §7.3
12. **Jira MCP client** — `shared/jira_client/mcp_client.py` (can be deferred until incremental sync)
13. **Incremental sync loop** — using MCP client
14. **Reconciliation script** — daily full check

Steps 1–9 produce a populated, validated index that the agent can immediately use. Steps 10–11 produce calibrated threshold values. Steps 12–14 keep the index fresh but aren't blocking for the first agent demo.

---

## 10. Acceptance Criteria

The vector DB workstream is complete when:

- [ ] Convergence contract (§3) is committed to `shared/contracts/` and signed off
- [ ] ChromaDB collection exists at `./data/chroma/` and persists across restarts
- [ ] Collection contains all in-scope Jira issues with full metadata per §3.1
- [ ] Every record has provenance fields: `embedding_model`, `embedding_model_version`, `embedding_task_type`, `content_hash`, `indexed_ts`, `schema_version`
- [ ] Content cleaning module has ≥ 80% unit test coverage and handles ADF, wiki markup, code blocks, boilerplate
- [ ] Backfill is resumable from checkpoint (kill it mid-run, restart, completes correctly)
- [ ] Incremental sync runs on a schedule and updates the collection without duplicates
- [ ] All §7.1 sanity checks pass
- [ ] §7.2 threshold calibration has produced concrete `semantic_flag` and `semantic_block` values, written into a config file the agent can consume
- [ ] §7.3 embedding quality review has been done and documented
- [ ] No Jira credentials in repo; secrets per company policy
- [ ] README documents how to run backfill, sync loop, calibration, and validation

---

## 11. Convergence with the Agent Workstream

When the agent workstream reaches Layer 3 implementation, it does NOT need to wait for the vector DB workstream to finish. The convergence steps:

1. Agent imports `JiraIssueVectorRecord` from `shared/contracts/`
2. Agent imports `VectorStore` protocol from `shared/vector_store/base.py`
3. Agent imports `EmbeddingClient` from `shared/embeddings/base.py`
4. Agent's Layer 3 code uses these abstractions only
5. For early agent development, agent points at a small seed corpus (e.g., 20 issues) hand-indexed for unit tests
6. **Convergence point:** agent's `chroma_path` config is changed to point at the populated collection from this workstream
7. Threshold values from §7.2 are written into the agent's per-intake-type YAML configs

If both sides honored the contract, this is a configuration change, not a code change.

---

## 12. Out of Scope

- The Duplicate Detection Agent itself (separate spec)
- Production vector DB integration (interface only; the company data pipeline owns this)
- UI for browsing the index
- Multi-project access controls
- Cross-language embedding support
- Webhook-based sync (production data pipeline handles this)

---

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Embedding model changes mid-build | Pin model name + version in contract; record in every record's metadata; agent verifies on startup |
| Jira description boilerplate inflates scores | §7.3 quality review catches this; cleaning module is iteratively improved |
| Backfill fails halfway through | Checkpointing (§5.3) makes it resumable |
| MCP server can't handle bulk load | Use REST for backfill; MCP only for incremental |
| Threshold values drift as corpus grows | §7.2 calibration is re-run periodically; thresholds versioned with corpus |
| Schema needs to change after agent ships | Bump `schema_version`, plan a re-embed migration; coordinate via shared contract |
| Embedding API rate limits slow backfill | Tenacity-based exponential backoff; configurable parallelism; run overnight if needed |
| Issues deleted from Jira but linger in collection | Daily reconciliation job (§6.3) catches orphans |
