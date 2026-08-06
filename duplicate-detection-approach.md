# Duplicate Detection — Layered Approach

Three layers run in sequence. Each trades recall for precision. Layers 1 and 2 are deterministic and serve as the fallback path if the embedding API or vector store is unavailable.

## Layer 1 — Exact Duplicate

- SHA-256 hash of normalized `name + description`
- Normalized name equality (lowercase, strip punctuation, stopwords, whitespace)
- Direct equality on project codes, issue keys, and inventory IDs

## Layer 2 — Fuzzy Duplicate (lexical)

- Levenshtein / `token_set_ratio` on names, ~85% threshold
- BM25 sparse retrieval over names and descriptions
- Jaccard similarity on tokenized descriptions
- Word n-gram matching to catch reordered titles

## Layer 3 — Semantic Duplicate

- Embed composite record text with `gemini-embedding-001`
- Cosine similarity search over the vector store, top-k candidates
- Threshold flag for review (calibrate against labeled pairs)
- LLM re-ranker over surviving candidates for final verdict

---

## Justification — `gemini-embedding-001`

- **Unifies and outperforms the prior models.** Replaces `text-embedding-005` and `text-multilingual-embedding-002`, beating both in their own domains. Legacy models are on a deprecation path; starting here avoids a forced re-embed later.
- **Catches what Layers 1–2 structurally cannot.** Edit distance and BM25 require shared characters or tokens. "Vendor onboarding automation" and "supplier intake bot" share neither, and only a semantic representation resolves them.
- **Matryoshka dimension scaling.** Default 3072 dimensions can be truncated to 1536 or 768 without retraining, trading marginal accuracy for large reductions in index size and query latency. Vectors must be re-normalized after truncation.
- **Fits the record profile.** 2048-token input limit accommodates intake titles, descriptions, and acceptance criteria as a single composite document. Records exceeding the limit are silently truncated and must be length-checked at ingestion.
- **Supports task-type conditioning.** Duplicate detection is symmetric — both sides are documents — so `SEMANTIC_SIMILARITY` is the correct task type, not the retrieval types tuned for short-query-to-long-document asymmetry.

## Justification — Cosine Similarity

- **Length-invariant.** Measures angle, not magnitude, so a two-line intake request and a fully specified Epic describing the same work score as similar. Euclidean distance would penalize the length gap.
- **Bounded and interpretable.** Output falls in a fixed range, making thresholds portable across configs and legible to reviewers and to the score-fusion function.
- **Equivalent ranking on normalized vectors.** Vertex embeddings are returned normalized, so cosine, dot product, and Euclidean distance produce identical rankings — cosine is chosen for interpretability at no accuracy cost.
- **Native vector store support.** Cosine is a first-class distance metric in ChromaDB and Vertex AI Vector Search, requiring no custom scoring layer.

> Thresholds are model-specific. Any change of embedding model or output dimension invalidates existing cutoffs and requires re-embedding the full corpus and recalibrating against labeled duplicate pairs.
