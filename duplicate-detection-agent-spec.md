# Duplicate Detection Agent — Build Specification

**Status:** Ready for implementation
**Framework:** Google ADK (Agent Development Kit)
**POC Vector Store:** ChromaDB (local, persistent)
**Production Target:** Company-managed vector database and data pipeline (TBD; abstracted behind interface)
**Upstream Agent:** Intake Quality Agent (already implemented — produces the JSON input to this agent)

---

## 1. Purpose

The Duplicate Detection Agent inspects an incoming intake submission and determines whether the same or a substantially similar idea already exists in Jira. It is the second agent in the intake pipeline, running after the Intake Quality Agent (already built) and before downstream Classification.

The agent does not make terminal decisions on its own. It produces a graded assessment with linked candidates, confidence scores, and a recommended action. Humans (or downstream agents) decide what to do with that assessment.

The agent is implemented using **Google ADK** as a multi-agent component. The vector store is abstracted behind an interface so the POC (ChromaDB) and production (company-managed vector DB) implementations are interchangeable without changes to agent logic.

---

## 2. Position in the Intake Workflow

```
Submission → Intake Quality Agent → Duplicate Detection Agent → Classification Agent → Artifact Generator → Jira
              (already built)              ▲
                                           │
                                           └── this spec
```

### 2.1 Upstream Contract — Intake Quality Agent

The Intake Quality Agent is **already implemented and in production use**. Its output is the input contract for this agent. It emits a JSON payload containing the validated, normalized responses to all intake questions for a given intake type. The Duplicate Detection Agent consumes that JSON directly.

Key implications:

- **Do not rebuild upstream validation.** Trust that required fields are present and well-formed. If they aren't, the upstream agent has failed and this agent should return `verdict: none, action: proceed` with a warning log.
- **Field set is intake-type dependent.** Different intake types ask different questions, so the JSON payload structure varies. The agent MUST handle this via configuration, not hardcoded field names.
- **The intake type itself is a routing key.** Use it to load the correct YAML config (thresholds, field mappings, search scope).

See §7.1 for the input schema produced by the Intake Quality Agent.

### 2.2 Downstream

Outputs feed the Classification Agent and are surfaced to the requester for confirmation when the verdict is `likely` or `exact`.

---

## 3. Core Functional Requirements

### 3.1 Three-Layer Detection

The agent MUST implement three independent detection layers and combine their results:

| Layer | Method | Catches | Latency Budget |
|---|---|---|---|
| 1 — Exact | Normalized hash match | Resubmissions, copy-paste, identical titles | < 50 ms |
| 2 — Fuzzy | Lexical similarity (RapidFuzz, n-grams) | Typos, reordering, minor rewording | < 200 ms |
| 3 — Semantic | Vector embeddings + LLM re-rank | Same idea expressed differently, jargon, paraphrasing | < 3 s |

Each layer runs against the same candidate corpus (open + recently closed Jira issues within the configured scope) but uses different signals.

### 3.2 Layer 1 — Exact Match

- Normalize the intake title: lowercase, strip punctuation, collapse whitespace, remove common stop phrases (`request to`, `need`, `please`, `can we`, `proposal for`)
- Compute SHA-256 of the normalized title
- Compute SHA-256 of `normalized_title + requester + target_system` as a composite key
- Maintain an in-memory or SQLite hash index of existing issues for O(1) lookup
- Return all hash matches as `match_type: exact`

### 3.3 Layer 2 — Fuzzy Match

- Compute `token_set_ratio` (RapidFuzz) between intake title and each candidate's title
- Compute n-gram Jaccard similarity (n=3) between the first 500 characters of intake description and candidate description
- Apply a metadata boost: +5 to score when requester, LOB, or target component matches
- A fuzzy hit requires title_score ≥ `fuzzy_title_threshold` OR (title_score ≥ 70 AND description_score ≥ `fuzzy_description_threshold`)
- Thresholds are YAML-configurable per intake type

### 3.4 Layer 3 — Semantic Match

- Embed `intake.title + "\n\n" + intake.description` using the configured embedding model (see §5.4) with query-side task type
- Query the vector store with the configured metadata filters
- Retrieve top-K candidates (default K=10)
- Pass the top candidates to a Gemini re-ranker (via Google ADK's model interface) with the intake and candidate texts
- The re-ranker returns a duplicate confidence score (0.0–1.0) and a one-sentence reasoning per candidate
- Final semantic score = max(cosine_similarity, llm_confidence) — the LLM can promote a candidate the embedding underweighted, but cannot suppress one without explicit reasoning

### 3.5 Verdict Aggregation

The agent combines layer results into a single verdict:

| Condition | Verdict | Recommended Action |
|---|---|---|
| Exact match on open issue | `exact` | `block` — surface existing ticket, offer to add as watcher |
| Fuzzy ≥ threshold AND same requester/team | `likely` | `merge_suggestion` |
| Semantic ≥ `semantic_block` threshold AND LLM agrees | `likely` | `flag_for_review` (NOT auto-block) |
| Semantic ≥ `semantic_flag` threshold | `possible` | `link_related` |
| Match on closed issue only | `possible` | `link_related` (do not block) |
| No matches above thresholds | `none` | `proceed` |

**Bias rule:** false positives (blocking a legitimate new request) are more costly than false negatives. When the layers disagree, prefer `flag_for_review` over `block`.

---

## 4. Configuration (YAML)

The agent MUST be configurable per intake type via YAML, following the platform's existing convention.

```yaml
intake_type: ai_initiative
duplicate_detection:
  enabled: true
  field_mapping:                 # maps intake question IDs to detection roles
    title_field: title
    description_fields:
      - problem_statement
      - proposed_solution
    requester_field: submitted_by
    lob_field: lob
    target_system_field: target_system
    component_fields: components
    stakeholder_fields: stakeholders
  search_scope:
    projects: [AIPLAT, AIINIT]
    statuses: [Open, In Progress, In Review, Blocked]
    include_closed: true
    closed_lookback_days: 365
    open_lookback_days: 730
  thresholds:
    exact_block: true            # block on exact match against open issue
    fuzzy_title: 85              # 0–100 RapidFuzz score
    fuzzy_description: 70
    semantic_flag: 0.82          # cosine similarity
    semantic_block: 0.95
    llm_rerank_min: 0.80         # LLM confidence to count as duplicate
  llm_rerank: true
  max_candidates_to_review: 10
  metadata_boost:
    same_requester: 5
    same_lob: 3
    same_component: 3
```

The agent MUST fail closed (return `verdict: none, action: proceed`) if its config is missing or invalid, and emit a warning log. It MUST NOT block submissions due to its own misconfiguration.

---

## 5. Vector Store (POC: ChromaDB)

ChromaDB is the POC implementation. The production target is the company's managed vector database (specifics TBD). All vector store access MUST go through the abstraction in §5.5 so the production swap is a single adapter change.

### 5.1 Setup

```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./data/chroma",
    settings=Settings(anonymized_telemetry=False),
)

collection = client.get_or_create_collection(
    name="jira_issues",
    metadata={"hnsw:space": "cosine"},
)
```

Use **one collection with metadata filtering**, not many collections. This matches how most managed vector DBs are structured and simplifies the production migration.

### 5.2 Record Schema

```python
collection.add(
    ids=["PROJ-1234"],
    embeddings=[vector_768d],
    documents=[title + "\n\n" + description],
    metadatas=[{
        "project": "AIPLAT",
        "status": "In Progress",
        "status_category": "indeterminate",   # to-do | indeterminate | done
        "issue_type": "Story",
        "components": "data-pipeline,ml",      # comma-joined; Chroma needs primitives
        "labels": "migration,bigquery",
        "requester": "jdoe",
        "lob": "retail",
        "created_ts": 1730000000,
        "updated_ts": 1730500000,
        "resolution": "",
    }],
)
```

**Chroma metadata constraints:** values must be `str | int | float | bool`. Lists are comma-joined; filtering on list membership is done in the application layer after retrieval, or by using the document field with a `$contains` query.

### 5.3 Query Pattern

```python
results = collection.query(
    query_embeddings=[intake_vector],
    n_results=10,
    where={
        "$and": [
            {"project": {"$in": ["AIPLAT", "AIINIT"]}},
            {"status_category": {"$ne": "done"}},
            {"created_ts": {"$gte": one_year_ago_ts}},
        ],
    },
)
```

### 5.4 Embedding Model

Embeddings are produced via Google ADK's model interface using a Gemini embedding model. The specific model is configurable so the POC and production deployments can use different models as company policy dictates.

- **POC model:** `gemini-embedding-001` (or whichever Gemini embedding model is available through ADK's standard model interface)
- **Dimensions:** match the model's native output (typically 768 or 3072)
- **Task type asymmetry (if supported by the model):**
  - Indexing Jira issues → document/retrieval-document task type
  - Embedding intake queries → query/retrieval-query task type
- **Input format:** `f"{title}\n\n{description}"` truncated to model's max input tokens
- **Caching:** key embeddings by SHA-256 of input text + model name + task type; skip re-embedding if hash unchanged
- **Production:** the production embedding model will be whatever the company-managed data pipeline provides. The `EmbeddingClient` interface in `embeddings/base.py` MUST be the only point of coupling.

### 5.5 VectorStore Abstraction (Required)

To enable the migration from ChromaDB to the company-managed vector DB without rewriting agent logic, the agent MUST access the vector store through a thin interface, not the Chroma client directly.

```python
from typing import Protocol, TypedDict, Any

class VectorRecord(TypedDict):
    id: str
    vector: list[float]
    document: str
    metadata: dict[str, Any]

class VectorMatch(TypedDict):
    id: str
    score: float
    metadata: dict[str, Any]
    document: str

class VectorStore(Protocol):
    def upsert(self, records: list[VectorRecord]) -> None: ...
    def query(
        self,
        vector: list[float],
        filters: dict,
        k: int = 10,
    ) -> list[VectorMatch]: ...
    def delete(self, ids: list[str]) -> None: ...
    def count(self) -> int: ...
```

Provide a `ChromaVectorStore` implementation for the POC. The production implementation against the company-managed vector DB will be a separate adapter implementing the same protocol.

---

## 6. Jira Sync

### 6.1 POC Strategy: Scheduled Batch

Run a separate sync job (not inline with the agent) that:

1. Reads `last_sync_ts` from a local state file (`./data/sync_state.json`)
2. Issues a JQL query: `project in (PROJECTS) AND updated >= -15m`
3. For each returned issue:
   - Compute content hash of `title + description`
   - If hash matches the cached hash for this issue ID, skip
   - Otherwise: embed via the configured embedding client, upsert to vector store, update hash cache
4. Write new `last_sync_ts` on success

Run the job every 5–15 minutes via cron, APScheduler, or a FastAPI background task.

### 6.2 Initial Backfill

A one-time backfill job that paginates through:

```jql
project in (PROJECTS)
AND (
  statusCategory != Done
  OR resolved >= -365d
)
ORDER BY updated DESC
```

Embed and index in batches of 50–100 to respect embedding API rate limits. Log progress and support resume from a checkpoint.

### 6.3 Production Strategy (Out of Scope for POC)

In production, Jira issue indexing will be handled by the company-managed data pipeline. The agent should not implement its own production sync — instead, the production vector store adapter will read from a corpus already populated by the company pipeline. Document the contract (record schema, refresh cadence) but do not implement.

---

## 7. Agent Inputs & Outputs

### 7.1 Input — JSON from the Intake Quality Agent

The input to this agent is the JSON payload produced by the **already-built Intake Quality Agent**. That payload contains the validated responses to all intake questions for a given intake type.

The structure is `intake_type` + a `responses` map keyed by question ID. The Duplicate Detection Agent does NOT define which questions are asked — it consumes whatever the upstream agent produces.

```json
{
  "intake_id": "INTAKE-2026-00482",
  "intake_type": "ai_initiative",
  "submitted_at": "2026-05-05T14:22:00Z",
  "submitted_by": "jsmith",
  "intake_quality": {
    "status": "passed",
    "version": "intake_quality.v2",
    "issues": []
  },
  "responses": {
    "title": "Migrate customer churn model from Teradata to BigQuery",
    "problem_statement": "The current churn prediction pipeline runs on Teradata...",
    "proposed_solution": "Re-platform the churn model and its feature pipeline onto BigQuery...",
    "business_value": "Reduces compute cost by ~40%, aligns with Teradata sunset...",
    "lob": "retail",
    "target_system": "BigQuery",
    "components": ["data-pipeline", "ml"],
    "stakeholders": ["jdoe", "asmith"],
    "estimated_effort": "M",
    "desired_completion": "2026-Q3"
  }
}
```

#### Field Mapping Configuration

Because question IDs vary by intake type, the agent uses a **field mapping** in YAML to identify which response fields play which roles in detection. This is part of the per-intake-type config (§4):

```yaml
intake_type: ai_initiative
duplicate_detection:
  field_mapping:
    title_field: title                    # used for exact + fuzzy title match
    description_fields:                   # concatenated for fuzzy desc + semantic embedding
      - problem_statement
      - proposed_solution
    requester_field: submitted_by         # top-level, not under responses
    lob_field: lob
    target_system_field: target_system
    component_fields: components          # list field
    stakeholder_fields: stakeholders
```

The agent reads the field mapping, extracts the relevant values from `responses` (or top-level for fields like `submitted_by`), and feeds them into the three detection layers. This keeps the agent intake-type-agnostic.

#### Required vs Optional Fields

The agent requires only:
- `intake_id`
- `intake_type`
- A resolvable `title_field`
- At least one resolvable `description_fields` entry

Everything else is optional and used for metadata boost and reviewer context if present. Missing optional fields MUST NOT cause the agent to fail.

#### Trust Boundary

The Intake Quality Agent has already validated and normalized this payload. This agent does NOT re-run quality checks. If `intake_quality.status != "passed"`, the agent returns `verdict: none, action: proceed` and logs a warning — quality is the upstream agent's responsibility.

### 7.2 Output

```json
{
  "intake_id": "INTAKE-2026-00482",
  "verdict": "likely",
  "confidence": 0.88,
  "recommended_action": "merge_suggestion",
  "matches": [
    {
      "jira_key": "AIPLAT-1234",
      "title": "BigQuery migration for Teradata churn pipeline",
      "match_type": "semantic",
      "similarity_score": 0.91,
      "fuzzy_title_score": 78,
      "llm_confidence": 0.88,
      "status": "In Progress",
      "status_category": "indeterminate",
      "requester": "jdoe",
      "url": "https://jira.example.com/browse/AIPLAT-1234",
      "reasoning": "Both describe migrating the churn model from Teradata to BigQuery; same target system and ML domain."
    },
    {
      "jira_key": "AIPLAT-0987",
      "title": "Teradata sunset: ML workloads inventory",
      "match_type": "semantic",
      "similarity_score": 0.74,
      "llm_confidence": 0.65,
      "status": "Done",
      "status_category": "done",
      "url": "https://jira.example.com/browse/AIPLAT-0987",
      "reasoning": "Related Teradata sunset effort but broader scope; useful prior context."
    }
  ],
  "reviewer_notes": "Strong likely duplicate of AIPLAT-1234 (same scope, same target). Recommend merging requester as stakeholder. AIPLAT-0987 is related context only.",
  "layers_executed": ["exact", "fuzzy", "semantic"],
  "latency_ms": {
    "exact": 12,
    "fuzzy": 145,
    "semantic": 2380,
    "total": 2537
  }
}
```

The output schema MUST be stable; downstream agents depend on it.

---

## 8. Decision Logic — Worked Examples

### Example A: Exact resubmission
- Intake title: `"Migrate Teradata to BigQuery"`
- Existing open issue AIPLAT-555 title: `"Migrate Teradata to BigQuery"`
- Same requester
- **Verdict:** `exact`, **action:** `block`

### Example B: Reworded title, same idea
- Intake: `"BigQuery migration from Teradata for churn model"`
- Existing AIPLAT-1234: `"Migrate customer churn model from Teradata to BigQuery"`
- Fuzzy title score: 82, semantic similarity: 0.91, LLM confidence: 0.88
- **Verdict:** `likely`, **action:** `merge_suggestion`

### Example C: Same problem, different framing
- Intake: `"Need ML platform on GCP for retention modeling"`
- Existing AIPLAT-1234: `"Migrate customer churn model from Teradata to BigQuery"`
- Fuzzy title score: 31, semantic similarity: 0.79, LLM confidence: 0.62
- **Verdict:** `possible`, **action:** `link_related`
- Reviewer note: scope overlaps but framing is broader; let humans decide

### Example D: Semantic match on closed issue
- Intake: `"Build dashboard for Q3 sales forecasts"`
- AIPLAT-0420 (status: Done, resolved 4 months ago): `"Q3 sales forecast dashboard"`
- Semantic similarity: 0.94
- **Verdict:** `possible`, **action:** `link_related`
- Do NOT block — surface as prior art, the requester likely wants something new or extended

### Example E: Multiple weak matches
- Intake matches AIPLAT-100 (0.74), AIPLAT-101 (0.71), AIPLAT-102 (0.68) at semantic layer
- No single strong match
- **Verdict:** `none`, **action:** `proceed` with related-issue links attached
- Reviewer note: "Touches on themes from 3 prior issues; may benefit from broader scoping conversation"

### Example F: Epic candidate
- Intake describes a feature
- Best match is an Epic (AIPLAT-100) covering that feature area at high level
- **Verdict:** `none` (not a duplicate), but output `epic_candidate: AIPLAT-100`
- **Action:** `proceed` with suggested parent linking

---

## 9. Edge Cases the Agent MUST Handle

1. **Empty or trivial input** — title or description under 10 chars: skip detection, return `verdict: none`, log warning
2. **Cold start** — vector store empty: skip Layer 3, return Layers 1+2 results only, log warning
3. **Embedding API failure** — degrade gracefully to Layers 1+2; do not fail the agent
4. **Vector store unavailable** — same: degrade to Layers 1+2
5. **LLM re-ranker timeout** — fall back to raw cosine similarity; mark `llm_rerank: skipped` in output
6. **Closed-as-wont-do issues** — surface prominently in reviewer notes; the prior decision context matters
7. **Splits**: intake matches parts of multiple existing issues — LLM re-ranker MUST flag this in `reviewer_notes`
8. **Parent/child detection**: a Story matching an Epic is a candidate child, not a duplicate — return as `epic_candidate`, not as a duplicate match
9. **Cross-project matches**: if the configured scope spans projects, indicate the project in match output so humans can judge relevance
10. **Reopened candidates**: if a closed issue matches at high semantic confidence, include `prior_resolution` in the match record so the requester sees what was tried before

---

## 10. Logging & Observability (Required)

Every agent invocation MUST emit a structured log record:

```json
{
  "timestamp": "2026-05-05T14:22:03Z",
  "intake_id": "INTAKE-2026-00482",
  "input_hash": "sha256:...",
  "layers_executed": ["exact", "fuzzy", "semantic"],
  "candidates_considered": {
    "exact": 0,
    "fuzzy": 3,
    "semantic": 10
  },
  "verdict": "likely",
  "confidence": 0.88,
  "recommended_action": "merge_suggestion",
  "matches_returned": 2,
  "latency_ms": {"exact": 12, "fuzzy": 145, "semantic": 2380, "total": 2537},
  "config_version": "ai_initiative.v3",
  "embedding_model": "gemini-embedding-001",
  "rerank_model": "gemini-2.0-flash"
}
```

These logs feed:
- Threshold tuning (compare agent verdicts against reviewer overrides)
- Drift detection (semantic score distributions over time)
- Value reporting (intakes prevented, intakes consolidated)

---

## 11. Project Structure

```
duplicate_detection_agent/
├── agent.py                      # ADK agent definition + orchestration
├── config/
│   ├── default.yaml
│   └── intake_types/
│       ├── ai_initiative.yaml
│       ├── feature.yaml
│       └── analytics.yaml
├── detectors/
│   ├── __init__.py
│   ├── exact.py                  # Layer 1
│   ├── fuzzy.py                  # Layer 2 (RapidFuzz)
│   └── semantic.py               # Layer 3 (vector + LLM rerank)
├── vector_store/
│   ├── __init__.py
│   ├── base.py                   # VectorStore Protocol
│   ├── chroma_store.py           # POC implementation
│   └── prod_store.py             # Production adapter stub (company vector DB)
├── embeddings/
│   ├── __init__.py
│   ├── base.py                   # EmbeddingClient Protocol
│   └── adk_embeddings.py         # POC: Gemini embedding via ADK
├── intake_input/
│   ├── __init__.py
│   ├── parser.py                 # parses Intake Quality Agent JSON
│   └── field_mapper.py           # resolves field_mapping config to values
├── jira/
│   ├── __init__.py
│   ├── client.py                 # Jira REST client wrapper
│   └── sync.py                   # Scheduled batch sync job (POC only)
├── rerank/
│   ├── __init__.py
│   └── gemini_reranker.py        # Gemini re-ranker via ADK
├── normalize.py                  # Title/text normalization
├── aggregator.py                 # Verdict aggregation logic
├── schemas.py                    # Pydantic models for I/O contracts
├── tests/
│   ├── test_exact.py
│   ├── test_fuzzy.py
│   ├── test_semantic.py
│   ├── test_aggregator.py
│   ├── test_normalize.py
│   ├── test_field_mapper.py
│   └── fixtures/
│       ├── sample_intake_quality_outputs.json
│       └── sample_jira_issues.json
├── scripts/
│   ├── backfill.py               # One-time initial indexing (POC only)
│   └── sync_loop.py              # Periodic sync runner (POC only)
├── data/                         # gitignored
│   ├── chroma/
│   └── sync_state.json
├── requirements.txt
└── README.md
```

---

## 12. Build Order

1. **Schemas + normalize.py + tests** — lock the I/O contract first; pydantic models for Intake Quality Agent input and this agent's output
2. **Intake input parser + field mapper** — parse Intake Quality Agent JSON, resolve `field_mapping` config, with unit tests against fixture payloads representing 2–3 different intake types
3. **VectorStore interface + ChromaVectorStore** — unit tests against an in-memory Chroma instance
4. **EmbeddingClient interface + ADK Gemini embeddings + cache** — verify task-type asymmetry where supported
5. **Jira client + backfill script** — index a single project to start
6. **Layer 1 (exact)** — wire to the ADK agent skeleton, verify end-to-end with one match
7. **Layer 2 (fuzzy)** — RapidFuzz integration, threshold tuning
8. **Layer 3 (semantic)** — vector query + Gemini re-ranker
9. **Aggregator** — verdict combination logic
10. **Sync job** — scheduled incremental updates (POC only)
11. **Observability** — structured logging, latency tracking
12. **YAML config loader** — per-intake-type overrides including field mapping
13. **Integration test** — end-to-end with a fixture set of 50–100 sample Intake Quality Agent outputs feeding into this agent

Do not skip ahead. Layers 1 and 2 must work standalone before Layer 3 is added; the system must degrade to them if the vector store is unavailable.

---

## 13. Dependencies

```
# requirements.txt
google-adk>=0.2.0
google-genai>=0.3.0
chromadb>=0.5.0
rapidfuzz>=3.9.0
atlassian-python-api>=3.41.0
pydantic>=2.7.0
pyyaml>=6.0.1
fastapi>=0.110.0
apscheduler>=3.10.0
tenacity>=8.2.0
structlog>=24.1.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

Pin exact versions in your lockfile per company policy. Do not pull in `google-cloud-aiplatform` or other Vertex-specific SDKs — embeddings and model calls go through ADK.

---

## 14. Acceptance Criteria for POC

The POC is complete when:

- [ ] Agent is implemented as a Google ADK agent
- [ ] Agent consumes the Intake Quality Agent JSON output (§7.1) directly, including resolving `field_mapping` per intake type
- [ ] Agent returns the output schema in §7.2
- [ ] All three layers run and degrade gracefully if any one fails
- [ ] YAML config controls thresholds, search scope, and field mapping per intake type
- [ ] ChromaDB persists across restarts and contains ≥ 1 project's worth of issues
- [ ] Embeddings produced via ADK's Gemini embedding model with correct task-type usage where supported
- [ ] Sync job runs on a schedule and incrementally updates the index
- [ ] Six worked examples in §8 produce the expected verdicts on test fixtures
- [ ] Structured logs emitted per §10
- [ ] VectorStore protocol is the only point of vector-store coupling — no Chroma imports outside `vector_store/chroma_store.py`
- [ ] EmbeddingClient protocol is the only point of embedding-model coupling
- [ ] Unit test coverage ≥ 70% on `detectors/`, `aggregator.py`, `normalize.py`, `intake_input/`
- [ ] README documents how to run backfill, start the sync loop, and invoke the agent
- [ ] At least 2 different intake types' field mappings are tested end-to-end

---

## 15. Out of Scope (POC)

- Production vector DB adapter (interface only; the company-managed vector DB is the production target)
- Production data pipeline integration for Jira indexing (the company pipeline owns this in production)
- UI / reviewer dashboard
- Threshold auto-tuning from reviewer feedback
- Multi-language embedding models
- Cross-tenant isolation
- Production-grade authentication and authorization
- HA / multi-node deployment

These are documented for the production roadmap but are not POC deliverables.

---

## 16. Migration Path Summary (For Reference)

| Concern | POC | Production |
|---|---|---|
| Agent framework | Google ADK | Google ADK (unchanged) |
| Vector store | ChromaDB (local, persistent) | Company-managed vector DB |
| Vector store client | `chromadb.PersistentClient` | Company SDK / API client |
| Upsert | `collection.add()` | Handled by company data pipeline |
| Query | `collection.query()` | Company SDK query method |
| Filtering | Chroma `where={...}` | Whatever the company DB supports (mapped in adapter) |
| Embeddings | Gemini embedding via ADK | Per company-managed pipeline |
| Jira sync | Scheduled batch in this repo | Company data pipeline |
| Persistence | Local disk | Managed |

The migration is intended to be:
1. A single adapter swap (`ChromaVectorStore` → `CompanyVectorStore` implementing the same `VectorStore` protocol)
2. Removal of the in-repo sync job (the company pipeline takes over)
3. Possible swap of the embedding client if production uses a different model

**No agent logic, detector logic, aggregator logic, or YAML config schema should require modification.** That's the test of whether the abstractions are right.
