# Shared Contracts — Vector Record & Embedding Config

**Status:** LOCK BEFORE EITHER WORKSTREAM BEGINS CODING
**Owners:** Both the Duplicate Detection Agent workstream and the Jira Vector DB workstream
**Location in repo:** `shared/contracts/`
**Companion documents:** `duplicate-detection-agent-spec.md`, `jira-vectordb-spec.md`

---

## 1. Why This Document Exists

The Duplicate Detection Agent and the Jira Vector DB build are running in parallel. They meet at one interface: the agent queries vectors that the indexer wrote. If the two sides disagree on **what a record looks like**, **what model produced the embeddings**, **how the document text is formatted**, or **what distance metric is in use**, the agent's similarity scores will be garbage and no one will notice until integration testing — or worse, demo day.

This document is the single source of truth for those agreements. Both workstreams import from `shared/contracts/`; neither side defines these things locally.

**Rule:** any change to this document is a coordinated PR with sign-off from both workstream owners. No silent edits.

---

## 2. The Contract Surface

Three things are locked here:

| Contract | Purpose | File |
|---|---|---|
| `JiraIssueVectorRecord` | Shape of every record in the vector store | `vector_record.py` |
| `EmbeddingConfig` | Model, dimensions, task types, distance metric | `embedding_config.py` |
| Document text format | How `title + description` is formatted before embedding | §5 below + `document_formatter.py` |

The vector store protocol (`VectorStore.upsert/query/delete`) and embedding client protocol (`EmbeddingClient.embed_documents/embed_query`) are also shared, but they live in their own modules (`shared/vector_store/base.py`, `shared/embeddings/base.py`) and are documented in the agent spec.

---

## 3. `JiraIssueVectorRecord` — Pydantic Model

```python
# shared/contracts/vector_record.py
"""
Canonical vector record for a Jira issue.

This is the contract between the Jira indexer (writer) and the
Duplicate Detection Agent (reader). Both sides MUST import this model;
neither side defines its own version.

Any change here requires a coordinated PR across workstreams.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.0"

StatusCategory = Literal["to-do", "indeterminate", "done"]


class JiraIssueVectorRecord(BaseModel):
    """One record in the vector store, representing one Jira issue."""

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    id: str = Field(
        ...,
        description="Jira issue key, e.g. 'AIPLAT-1234'. Unique. Used as the vector store ID.",
        pattern=r"^[A-Z][A-Z0-9_]+-\d+$",
    )

    # ------------------------------------------------------------------
    # Vector + Document
    # ------------------------------------------------------------------
    embedding: list[float] = Field(
        ...,
        description="Embedding vector. Dimensions must match EmbeddingConfig.dimensions.",
    )
    document: str = Field(
        ...,
        description=(
            "The exact text that was embedded. Format defined in §5 of contracts spec: "
            "'{cleaned_title}\\n\\n{cleaned_description}'. Stored for debugging and reranking."
        ),
        min_length=1,
    )

    # ------------------------------------------------------------------
    # Jira metadata (Chroma constraint: primitives only)
    # ------------------------------------------------------------------
    project: str = Field(..., description="Jira project key, e.g. 'AIPLAT'.")
    status: str = Field(..., description="Current status name, e.g. 'In Progress'.")
    status_category: StatusCategory = Field(
        ...,
        description="Normalized category: 'to-do' | 'indeterminate' | 'done'.",
    )
    issue_type: str = Field(..., description="'Story' | 'Bug' | 'Epic' | 'Task' | etc.")
    components: str = Field(
        default="",
        description="Comma-joined list of components, e.g. 'data-pipeline,ml'. Empty string if none.",
    )
    labels: str = Field(
        default="",
        description="Comma-joined list of labels, e.g. 'migration,bigquery'. Empty string if none.",
    )
    requester: str = Field(default="", description="Username/email of reporter. Empty if unknown.")
    assignee: str = Field(default="", description="Username/email of assignee. Empty if unassigned.")
    lob: str = Field(default="", description="Line of business if available. Empty string otherwise.")
    created_ts: int = Field(..., description="Issue creation time, unix seconds (UTC).", ge=0)
    updated_ts: int = Field(..., description="Last update time, unix seconds (UTC).", ge=0)
    resolved_ts: int = Field(
        default=0,
        description="Resolution time, unix seconds (UTC). 0 if unresolved.",
        ge=0,
    )
    resolution: str = Field(
        default="",
        description="Resolution name, e.g. 'Done', 'Won't Do'. Empty string if unresolved.",
    )
    parent_key: str = Field(
        default="",
        description="Parent Epic key if this is a Story under an Epic, else empty string.",
    )

    # ------------------------------------------------------------------
    # Provenance (REQUIRED — used for compatibility checks)
    # ------------------------------------------------------------------
    embedding_model: str = Field(
        ...,
        description="Embedding model name. MUST match EmbeddingConfig.model at query time.",
    )
    embedding_model_version: str = Field(
        ...,
        description="Specific model version. MUST match EmbeddingConfig.model_version at query time.",
    )
    embedding_task_type: str = Field(
        ...,
        description="Task type used when embedding this record. Typically 'RETRIEVAL_DOCUMENT'.",
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 of `document`. Used to detect content changes and skip re-embedding.",
        pattern=r"^[a-f0-9]{64}$",
    )
    indexed_ts: int = Field(
        ...,
        description="When this record was last embedded and written, unix seconds (UTC).",
        ge=0,
    )
    schema_version: str = Field(
        default=SCHEMA_VERSION,
        description="Contract version. Bump on breaking changes.",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("components", "labels")
    @classmethod
    def _validate_comma_joined(cls, v: str) -> str:
        # Empty string is fine. Otherwise must not have leading/trailing commas or spaces.
        if v == "":
            return v
        if v.startswith(",") or v.endswith(","):
            raise ValueError("comma-joined fields must not start or end with a comma")
        if " ," in v or ", " in v:
            raise ValueError("comma-joined fields must not contain spaces around commas")
        return v

    @field_validator("embedding")
    @classmethod
    def _validate_embedding_dim(cls, v: list[float]) -> list[float]:
        if len(v) == 0:
            raise ValueError("embedding cannot be empty")
        return v

    # ------------------------------------------------------------------
    # Conversion helpers — Chroma needs metadata as a flat dict
    # ------------------------------------------------------------------
    def to_chroma_metadata(self) -> dict:
        """
        Returns the metadata dict for Chroma's collection.add() call.
        Excludes id, embedding, and document — those are top-level args.
        """
        d = self.model_dump(exclude={"id", "embedding", "document"})
        # Chroma allows str | int | float | bool only. Pydantic should already
        # produce primitives for our schema, but assert here as a guardrail.
        for k, val in d.items():
            if not isinstance(val, (str, int, float, bool)):
                raise TypeError(
                    f"Chroma metadata field '{k}' is type {type(val).__name__}; "
                    f"must be str | int | float | bool"
                )
        return d

    @classmethod
    def from_chroma_result(
        cls,
        id: str,
        embedding: list[float],
        document: str,
        metadata: dict,
    ) -> "JiraIssueVectorRecord":
        """Reconstruct a record from a Chroma query result."""
        return cls(id=id, embedding=embedding, document=document, **metadata)
```

---

## 4. `EmbeddingConfig` — Locked Embedding Settings

```python
# shared/contracts/embedding_config.py
"""
Locked embedding configuration. Both the indexer and the agent
import EMBEDDING_CONFIG from this module.

Changing this is a breaking change: it invalidates every existing vector
in the collection. A change here requires a coordinated re-embed of the
entire corpus.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

DistanceMetric = Literal["cosine"]
TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]


class EmbeddingConfig(BaseModel):
    """The single source of truth for embedding settings."""

    model: str = Field(..., description="Embedding model identifier.")
    model_version: str = Field(..., description="Specific model version string.")
    dimensions: int = Field(..., gt=0, description="Vector dimension count.")

    distance_metric: DistanceMetric = Field(
        default="cosine",
        description="Cosine distance, expressed as similarity = 1 - distance.",
    )

    document_task_type: TaskType = Field(
        default="RETRIEVAL_DOCUMENT",
        description="Task type used when indexing Jira issues.",
    )
    query_task_type: TaskType = Field(
        default="RETRIEVAL_QUERY",
        description="Task type used when embedding intake queries.",
    )

    max_input_tokens: int = Field(
        ...,
        gt=0,
        description="Truncate input text to this token limit before embedding.",
    )

    chroma_collection_name: str = Field(
        default="jira_issues",
        description="Name of the ChromaDB collection.",
    )
    chroma_hnsw_space: str = Field(
        default="cosine",
        description="Chroma HNSW index space. MUST align with distance_metric.",
    )


# ----------------------------------------------------------------------
# THE locked config. Import this, do not construct your own.
# ----------------------------------------------------------------------
EMBEDDING_CONFIG = EmbeddingConfig(
    model="gemini-embedding-001",
    model_version="001",
    dimensions=768,
    distance_metric="cosine",
    document_task_type="RETRIEVAL_DOCUMENT",
    query_task_type="RETRIEVAL_QUERY",
    max_input_tokens=2048,
    chroma_collection_name="jira_issues",
    chroma_hnsw_space="cosine",
)
```

**Update protocol:**
- The values above are the working defaults. Confirm with the company-approved Gemini model accessible through Google ADK before locking — the model name, version, and dimension count must reflect what the team is actually authorized and able to use.
- Once locked, any change forces a full corpus re-embed. Do not change casually.
- Both workstreams import `EMBEDDING_CONFIG` and use its values — never hardcode model names or dimensions.

---

## 5. Document Text Format

The text that gets embedded. Both the indexer (writing records) and the agent (forming queries) MUST produce identical formatting given identical inputs. This logic lives in `shared/contracts/document_formatter.py`.

### 5.1 Format

```
{cleaned_title}

{cleaned_description}
```

- Single blank line between title and description (`\n\n`)
- If description is empty after cleaning, just the cleaned title is embedded (no trailing newlines)
- Total text truncated to `EMBEDDING_CONFIG.max_input_tokens` — prefer truncating description over title

### 5.2 Title Cleaning

Applied to titles for both indexed records and queries:

1. Trim leading/trailing whitespace
2. Collapse internal runs of whitespace to a single space
3. Do NOT lowercase — the embedding model handles case
4. Do NOT strip punctuation — it carries meaning
5. Do NOT remove stop phrases — that's a Layer 1 concern, not a semantic concern

### 5.3 Description Cleaning

Applied to descriptions for both indexed records and queries:

1. **Convert ADF to plain text** if Jira returns Atlassian Document Format JSON
2. **Strip Jira wiki markup** — `{code}`, `{quote}`, `{noformat}`, `*bold*`, `_italic_`, `[link|url]`, table syntax, etc.
3. **Strip URLs** — replace with anchor text where available, otherwise drop
4. **Strip code blocks** for non-bug issues — keep them for bugs (configurable per issue type)
5. **Strip boilerplate template headers** — configurable list (e.g., "Acceptance Criteria:", "Definition of Done:") with their following content removed or dampened
6. **Collapse whitespace** — multiple newlines to one blank line, runs of spaces to single space
7. **Truncate** to fit within `max_input_tokens`, keeping the beginning of the description (most signal is at the start)

### 5.4 Reference Implementation

```python
# shared/contracts/document_formatter.py
"""
Canonical document text formatter. Both workstreams MUST use this module.
"""
from __future__ import annotations
import re

# Configurable but checked into the repo — both sides see the same boilerplate list.
BOILERPLATE_HEADERS = [
    "Acceptance Criteria",
    "Definition of Done",
    "Description",
    "Background",
    "Steps to Reproduce",
    "Expected Result",
    "Actual Result",
]

CODE_HEAVY_TYPES = {"Bug", "Defect"}  # keep code blocks for these


def clean_title(raw_title: str) -> str:
    """Title cleaning per §5.2."""
    if not raw_title:
        return ""
    t = raw_title.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def clean_description(
    raw_description: str | dict | None,
    issue_type: str = "",
) -> str:
    """Description cleaning per §5.3."""
    if not raw_description:
        return ""

    text = _flatten_to_text(raw_description)
    text = _strip_wiki_markup(text)
    text = _strip_urls(text)
    if issue_type not in CODE_HEAVY_TYPES:
        text = _strip_code_blocks(text)
    text = _strip_boilerplate_headers(text)
    text = _collapse_whitespace(text)
    return text.strip()


def format_document(
    raw_title: str,
    raw_description: str | dict | None,
    issue_type: str = "",
    max_chars: int | None = None,
) -> str:
    """
    Produce the canonical embedded text per §5.1.

    Both indexer and agent call this with the same inputs and get the same output.
    """
    title = clean_title(raw_title)
    description = clean_description(raw_description, issue_type=issue_type)

    if not description:
        document = title
    else:
        document = f"{title}\n\n{description}"

    if max_chars is not None and len(document) > max_chars:
        # Token-aware truncation should happen at the embedding client.
        # This char-level cap is a safety net.
        document = document[:max_chars].rstrip()

    return document


# --- helpers (keep small, with full unit tests) ---

def _flatten_to_text(raw: str | dict) -> str:
    """If raw is ADF JSON, flatten to plain text. Otherwise return as-is."""
    if isinstance(raw, dict):
        return _flatten_adf(raw)
    return raw


def _flatten_adf(node: dict) -> str:
    """Recursively walk Atlassian Document Format JSON and emit plain text."""
    parts = []
    if node.get("type") == "text":
        parts.append(node.get("text", ""))
    for child in node.get("content", []) or []:
        parts.append(_flatten_adf(child))
    text = "".join(parts)
    if node.get("type") in {"paragraph", "heading", "listItem"}:
        text += "\n"
    return text


def _strip_wiki_markup(text: str) -> str:
    text = re.sub(r"\{code(?::[^}]+)?\}.*?\{code\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\{quote\}(.*?)\{quote\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\{noformat\}(.*?)\{noformat\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\[([^|\]]+)\|[^\]]+\]", r"\1", text)  # [text|url] -> text
    text = re.sub(r"[*_]{1,2}([^*_\n]+)[*_]{1,2}", r"\1", text)  # *bold* / _italic_
    text = re.sub(r"^h[1-6]\.\s*", "", text, flags=re.MULTILINE)  # h1. headings
    text = re.sub(r"^\|+", "", text, flags=re.MULTILINE)  # table rows
    return text


def _strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+", "", text)


def _strip_code_blocks(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]+`", "", text)
    return text


def _strip_boilerplate_headers(text: str) -> str:
    for header in BOILERPLATE_HEADERS:
        # Drop "Header:" or "Header" alone on a line; keep the content that follows
        text = re.sub(rf"^\s*{re.escape(header)}\s*:?\s*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text
```

This module is small enough to commit fully. Both workstreams import `format_document()` and never roll their own.

---

## 6. ID and Hash Conventions

### 6.1 Record ID

The Jira issue key, exactly as Jira returns it (e.g., `AIPLAT-1234`). Used as the vector store ID. This makes upserts trivial (re-embedding produces the same ID, which Chroma replaces in place).

### 6.2 Content Hash

```python
import hashlib

def compute_content_hash(document: str) -> str:
    """SHA-256 of the embedded text. Used to skip re-embedding unchanged issues."""
    return hashlib.sha256(document.encode("utf-8")).hexdigest()
```

The hash is computed over the **post-cleaning, pre-truncation** document text. Hashing pre-cleaning means trivial markup changes trigger re-embeds. Hashing post-truncation means a description edit beyond the truncation point is silently lost. Post-cleaning, pre-truncation is the right balance.

---

## 7. Compatibility Check (Required Runtime Behavior)

The Duplicate Detection Agent MUST verify on startup that the collection it's about to query was built with the same embedding model it's about to query with.

```python
def verify_collection_compatibility(store: VectorStore, expected: EmbeddingConfig) -> None:
    """Sample records from the collection and verify model provenance."""
    sample_records = store.sample(n=5)
    if not sample_records:
        # Cold start; collection is empty. Caller must handle gracefully.
        return

    for r in sample_records:
        if r.metadata["embedding_model"] != expected.model:
            raise IncompatibleCollectionError(
                f"Collection was built with model={r.metadata['embedding_model']!r}, "
                f"but agent is configured to query with model={expected.model!r}. "
                f"Re-embed the corpus or update EMBEDDING_CONFIG."
            )
        if r.metadata["embedding_model_version"] != expected.model_version:
            raise IncompatibleCollectionError(
                f"Collection model version mismatch: "
                f"{r.metadata['embedding_model_version']!r} vs {expected.model_version!r}."
            )
        if r.metadata["schema_version"] != SCHEMA_VERSION:
            raise IncompatibleCollectionError(
                f"Collection schema version {r.metadata['schema_version']!r} "
                f"does not match agent's {SCHEMA_VERSION!r}."
            )
```

Run this at agent startup. Failing fast with a clear error beats spending two days debugging mysterious low similarity scores.

---

## 8. Schema Versioning Policy

`SCHEMA_VERSION` lives in `vector_record.py` and is recorded in every record.

**Bump rules:**
- **Patch** (1.0 → 1.0.1): non-breaking additions — adding an optional field with a default
- **Minor** (1.0 → 1.1): non-breaking metadata additions that the agent might want
- **Major** (1.0 → 2.0): breaking — removed field, renamed field, changed type, changed semantic meaning, changed embedding model, changed document format

**Major bumps require:**
1. Coordinated PR across both workstreams
2. Decision on migration: re-embed entire corpus, or run a migration script that fills new fields
3. The agent's compatibility check (§7) refuses to query a collection at the wrong major version

Don't accumulate breaking changes silently. If you find yourself wanting to change three things, bundle them and bump once.

---

## 9. What Each Workstream Owns

| Concern | Indexer (Vector DB workstream) | Agent (Duplicate Detection workstream) |
|---|---|---|
| Building `JiraIssueVectorRecord` instances | ✅ writes them | ❌ reads them |
| Calling `EmbeddingClient.embed_documents` | ✅ | ❌ |
| Calling `EmbeddingClient.embed_query` | ❌ | ✅ |
| Setting `embedding_task_type` to `RETRIEVAL_DOCUMENT` | ✅ | ❌ |
| Using `RETRIEVAL_QUERY` task type | ❌ | ✅ |
| Computing `content_hash` | ✅ | ❌ |
| Running `verify_collection_compatibility` at startup | ❌ | ✅ |
| Defining the contract files in `shared/contracts/` | 🤝 jointly | 🤝 jointly |
| Bumping `SCHEMA_VERSION` | 🤝 jointly | 🤝 jointly |

---

## 10. Acceptance Criteria for the Contract

The contract is "locked" and both workstreams can begin coding when:

- [ ] `shared/contracts/vector_record.py` exists with `JiraIssueVectorRecord` and `SCHEMA_VERSION`
- [ ] `shared/contracts/embedding_config.py` exists with `EmbeddingConfig` and `EMBEDDING_CONFIG`
- [ ] `shared/contracts/document_formatter.py` exists with `format_document()` and helpers
- [ ] `EMBEDDING_CONFIG` model name and version reflect the company-approved Gemini embedding model accessible via ADK
- [ ] Unit tests for `document_formatter.py` cover: ADF flattening, wiki markup stripping, code-block handling per issue type, boilerplate header stripping, whitespace collapsing
- [ ] Both workstream owners have signed off on the contract (PR approval)
- [ ] Both workstreams have imports from `shared/contracts/` set up — no local copies

After lock, treat changes as a release event, not a casual edit.

---

## 11. Open Questions to Resolve Before Lock

These are knowable answers — they need to be filled in before the contract is finalized:

1. **Exact embedding model identifier** — `gemini-embedding-001` is the placeholder. Confirm what's accessible via the company's ADK setup.
2. **Model dimensions** — verify the chosen model produces the dimension count specified in `EMBEDDING_CONFIG.dimensions`.
3. **Max input tokens** — confirm against the chosen model's actual limit.
4. **Boilerplate header list** — review `BOILERPLATE_HEADERS` against actual Jira templates in use; add company-specific templates.
5. **Code-heavy issue types** — confirm `CODE_HEAVY_TYPES` matches the company's Jira issue type taxonomy.
6. **LOB field source** — where does `lob` come from in Jira? A custom field? A label prefix? Document the extraction logic before indexing.
7. **Parent/Epic linkage** — confirm the field name in Jira's REST API response (`customfield_10014` is common for Epic Link in older Jira; newer versions use `parent`).

Answer these, update the placeholders, then lock.
