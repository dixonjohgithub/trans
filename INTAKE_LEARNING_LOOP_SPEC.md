# Intake Learning Loop — Specification and Requirements

**Status:** Draft v1.0
**Owner:** JD (Principal AI Engineer)
**Target:** Agentic Intake Platform — React frontend + FastAPI backend + intake YAML cards
**Depends on:** existing conversation/response logging; UAT Feedback Widget spec (separate document)

---

## 1. Purpose

Use the intake conversations we already log to make intake cards better over time. Each intake YAML defines questions and per-question guidelines; when a user's response does not meet the guideline, the LLM asks follow-up questions until the gap is filled. Every follow-up is therefore a labeled signal that a question, a guideline, or the user needs help.

This spec covers four capabilities, in delivery order:

| # | Capability | What it produces | Needs |
|---|---|---|---|
| A | **Question friction scoring** | Per-question metrics and a ranked rewrite backlog | Aggregation only |
| B | **Few-shot examples at runtime** | Curated "good answer" examples shown to users and injected into adherence prompts | Curation UI + prompt change |
| C | **Auto-suggested question rewrites** | LLM-drafted rewrites of high-friction questions and guidelines, human-approved into new YAML versions | A + LLM + review UI |
| D | **Conversation replay eval suite** | Regression tests built from real conversations; run on every YAML or model change | A + CI hook |

## 2. Goals and non-goals

### Goals
- Measure which questions cause the most follow-ups, abandonment, and time cost.
- Reduce first-pass non-adherence by showing users what a good answer looks like.
- Shorten the loop from "this question is confusing" to "a better version ships" with an evidence-backed, human-approved rewrite flow.
- Prevent regressions: any change to a YAML card or the underlying model is checked against real past conversations before release.

### Non-goals
- No model fine-tuning in this phase. All learning is expressed as YAML changes, curated examples, and prompt content.
- No automatic (unreviewed) changes to production intake cards. Every YAML change goes through human approval.
- No cross-user surfacing of raw answers without scrubbing and curation (see §8).
- No predictive pre-fill, follow-up phrasing libraries, or drift alerting (future phases).

## 3. Definitions

- **Intake card** — a YAML file defining an intake flow: ordered questions, each with a `guideline` the answer must satisfy, plus card-level metadata.
- **Conversation** — one user's run through one card version: user turns, LLM turns, adherence verdicts, final captured answers.
- **Attempt** — a user's response to a specific question. The first attempt is the response before any follow-up.
- **Follow-up** — an LLM turn asking the user to add or fix something for a question because the attempt did not satisfy the guideline.
- **Accepted answer** — the attempt that the adherence check passed for a question.
- **Abandonment** — a conversation that ended before all required questions were accepted.
- **Card version** — an immutable identifier for a specific YAML content (git SHA or content hash).

## 4. Data model (shared by all four capabilities)

### 4.1 Required logging fields
The existing conversation log must expose (or be enriched to expose) the following per turn. If the current log is free-form, add a normalization step (§4.2) rather than changing the logger.

| Field | Description |
|---|---|
| `conversation_id` | unique per run |
| `card_id`, `card_version` | which YAML and which exact version |
| `question_id` | stable ID of the question in the YAML (add one if questions are only identified by text) |
| `turn_index`, `role` (`user` / `assistant` / `system`) | ordering and speaker |
| `turn_type` | `question`, `attempt`, `follow_up`, `accepted`, `other` |
| `adherence_verdict` | `pass` / `fail` plus the evaluator's reason text, for attempt turns |
| `gap_reason` | free text from the LLM on what was missing (used later for taxonomy; capture now) |
| `timestamp` | |
| `user_segment` | optional: LOB / team / role, if known, for later grouping |
| `outcome` | per conversation: `completed`, `abandoned`, `errored` |

### 4.2 Normalized tables
- **LR-1** Build an ETL job (scheduled, idempotent) that reads raw logs and writes:
  - `intake_conversations` — one row per conversation (`conversation_id`, `card_id`, `card_version`, `started_at`, `ended_at`, `outcome`, `user_segment`, `total_turns`).
  - `intake_attempts` — one row per attempt (`conversation_id`, `question_id`, `attempt_index`, `attempt_text`, `verdict`, `gap_reason`, `follow_up_text` (the LLM follow-up that followed this attempt, if any), `is_accepted`, `timestamp`).
- **LR-2** `question_id` must be stable across card versions when the question is "the same question" (so friction can be compared before/after a rewrite). Add `id:` to every question in every YAML; the ETL rejects cards without it.
- **LR-3** ETL runs at least nightly; backfill all historical logs on first run.

---

## 5. Capability A — Question friction scoring

### 5.1 Metrics (per `card_id` × `question_id`, computed per card version and rolled up across versions)

| Metric | Definition |
|---|---|
| `attempts_total` | number of first attempts |
| `first_pass_rate` | share of first attempts with verdict `pass` |
| `follow_up_rate` | 1 − `first_pass_rate` |
| `avg_follow_ups` | mean follow-ups per conversation for this question |
| `p90_follow_ups` | 90th percentile |
| `abandon_at_question_rate` | share of abandoned conversations whose last touched question is this one |
| `median_time_to_accept` | median seconds from question asked to accepted answer |
| `friction_score` | weighted composite (default: `0.4·follow_up_rate + 0.3·normalized(avg_follow_ups) + 0.3·abandon_at_question_rate`); weights configurable |

### 5.2 Requirements
- **FA-1** A nightly job computes the metrics above and writes them to `intake_question_metrics` with `computed_at`, `window_days` (default 30 and 90, both stored).
- **FA-2** Minimum sample guard: metrics are flagged `low_confidence=true` when `attempts_total < 20`.
- **FA-3** API: `GET /api/intake-learning/friction?card_id=&window_days=&limit=` returns questions ranked by `friction_score`, including the raw metrics and the question text/guideline from the YAML.
- **FA-4** API: `GET /api/intake-learning/friction/{card_id}/{question_id}` returns the metric history by card version (for before/after comparison).
- **FA-5** UI: a simple internal "Friction" page (table, sortable, filter by card and window) with a link from each row to the rewrite workflow (Capability C). Low-confidence rows are visually muted.
- **FA-6** Export: CSV of the ranked table.

### 5.3 Acceptance criteria
- [ ] A-AC1 Running the ETL and metrics job on a seeded set of 100 synthetic conversations produces the expected per-question values (unit test with hand-computed expectations).
- [ ] A-AC2 Changing a question's wording to a new card version produces a new row per version with the same `question_id`, visible in the history endpoint.
- [ ] A-AC3 The Friction page lists questions in descending `friction_score` and marks rows under 20 attempts as low confidence.

---

## 6. Capability B — Few-shot examples at runtime

### 6.1 Concept
For each question, keep 2–3 curated exemplary accepted answers. Use them in two places:
1. **User-facing** — shown as an expandable "Example of a good answer" under the question in the intake UI.
2. **Evaluator-facing** — injected into the adherence-check prompt as reference examples of answers that satisfy the guideline, improving verdict consistency.

### 6.2 Example sourcing and curation
- **FB-1** Candidate generation: a job proposes candidates per question from `intake_attempts` where `is_accepted=true`, preferring answers that passed on the first attempt, have median-ish length, and are dissimilar to each other (embedding diversity or simple token-overlap check).
- **FB-2** Scrubbing: candidates pass through a PII/sensitive-data scrubber (names, emails, employee IDs, system hostnames, account numbers, project codenames per a configurable deny-list) **before** a human sees them. Scrubber output is marked with `[REDACTED-<type>]` tokens.
- **FB-3** Curation UI: reviewer sees question, guideline, and up to 10 scrubbed candidates; can approve, edit, reject, or write a fresh example. Approved examples get `status=approved`, `approved_by`, `approved_at`.
- **FB-4** Only `approved` examples are ever used at runtime. Candidates and rejected items are never shown to end users or injected into prompts.
- **FB-5** Examples are stored in a table `intake_examples` (`card_id`, `question_id`, `example_text`, `source_conversation_id` (nullable, for audit), `status`, `approved_by`, `approved_at`), **not** in the YAML, so YAML stays a definition and examples can change without a card version bump. The YAML may optionally carry `examples:` as a seed; DB-approved examples take precedence.

### 6.3 Runtime use
- **FB-6** Intake UI: when a question renders, fetch `GET /api/intake-learning/examples?card_id=&question_id=` and show an "Example of a good answer" expander if ≥1 approved example exists. Collapsed by default. Log an event when it is expanded.
- **FB-7** Adherence prompt: when evaluating an attempt, include up to 3 approved examples with a line such as *"The following are examples of answers that satisfy this guideline."* Examples are reference material only; the prompt must state that the answer should be judged against the guideline, not against similarity to the examples.
- **FB-8** Feature flag per card (`learning.examples_enabled: true|false` in YAML metadata, default false) so cards can opt in one at a time.

### 6.4 Measurement
- **FB-9** Record `examples_shown` (count) and `example_expanded` (bool) per attempt in `intake_attempts` so Capability A can compare `first_pass_rate` with and without examples.

### 6.5 Acceptance criteria
- [ ] B-AC1 A candidate containing an email address or employee ID reaches the curation UI only with those values replaced by redaction tokens.
- [ ] B-AC2 A question with zero approved examples renders without the expander; with one approved example the expander appears and expanding it logs an event.
- [ ] B-AC3 With `examples_enabled: true`, the adherence prompt sent to the model contains the approved examples; with `false`, it does not (verified by prompt capture in test).
- [ ] B-AC4 Rejected or unapproved examples never appear in the runtime API response.

---

## 7. Capability C — Auto-suggested question and guideline rewrites

### 7.1 Concept
For a high-friction question, give the LLM the question, its guideline, a sample of real first attempts, the follow-ups that were asked, and the answers that finally passed. Ask it to diagnose the cause and propose a rewrite. A human reviews and, if approved, a new card version is produced through the normal YAML change process.

### 7.2 Trigger
- **FC-1** Manual: from the Friction page (A) a reviewer clicks "Propose rewrite".
- **FC-2** Scheduled (optional, flag-controlled): weekly, for any question with `friction_score` above a configurable threshold and `low_confidence=false`, generate a proposal automatically and queue it for review. Never more than one open proposal per question.

### 7.3 Proposal generation
- **FC-3** Input assembly (all text scrubbed per FB-2 before leaving the data layer):
  - question text and guideline (current version)
  - up to 30 first attempts with verdict `fail`, with their `gap_reason`
  - up to 30 follow-up texts the LLM issued for this question
  - up to 15 accepted answers
  - the metrics row from A
- **FC-4** The LLM is asked to return structured JSON:
  ```json
  {
    "diagnosis": "one paragraph: why users miss the guideline",
    "gap_patterns": ["missing business justification", "..."],
    "proposed_question": "rewritten question text",
    "proposed_guideline": "rewritten guideline text",
    "proposed_examples": ["..."],
    "rationale": "what changed and why",
    "risk_notes": "anything the reviewer should check (e.g. policy wording that must not change)"
  }
  ```
- **FC-5** Store proposals in `intake_rewrite_proposals` (`id`, `card_id`, `card_version`, `question_id`, `generated_at`, `model`, `input_summary` (counts, not raw text), `proposal_json`, `status` = `open` / `approved` / `rejected` / `superseded`, `reviewer`, `review_note`, `resulting_card_version` nullable).

### 7.4 Review and apply
- **FC-6** Review UI: side-by-side current vs proposed question and guideline, diagnosis, gap patterns, and a sample of the evidence (scrubbed attempts and follow-ups). Reviewer can edit proposed text inline before approving.
- **FC-7** Approve action produces a YAML diff (only the targeted `question`, `guideline`, and optional `examples` fields change; `id` is preserved) and opens a change in the normal YAML repository flow (PR/merge request). Nothing is written to a live card directly.
- **FC-8** When the new card version is deployed, the proposal is linked to `resulting_card_version` and Capability A's history view shows before/after metrics for that `question_id`.
- **FC-9** Guardrails: proposals must not remove any guideline requirement that is tagged `required_by_policy: true` in the YAML. The generator is told this; the reviewer UI additionally highlights any such requirement that is absent from the proposed guideline and blocks approval until acknowledged.

### 7.5 Acceptance criteria
- [ ] C-AC1 Clicking "Propose rewrite" on a question produces a proposal with all JSON fields populated and status `open`.
- [ ] C-AC2 The evidence shown in the review UI contains no unredacted PII (test with seeded PII in attempts).
- [ ] C-AC3 Approving a proposal produces a YAML diff that changes only the targeted question's fields and keeps `id` unchanged.
- [ ] C-AC4 A proposal whose guideline omits a `required_by_policy` requirement is flagged and cannot be approved without explicit acknowledgement.
- [ ] C-AC5 After deployment, the friction history endpoint returns metrics for both the old and new card version under the same `question_id`.

---

## 8. Capability D — Conversation replay eval suite

### 8.1 Concept
Turn real conversations into regression tests. Each test fixes: card version, question, a user attempt, and the expected adherence verdict (plus, optionally, that a follow-up was or was not needed). When a YAML card or the model/prompt changes, replay the suite and compare.

### 8.2 Case construction
- **FD-1** A job builds candidate cases from `intake_attempts`:
  - Positive cases: accepted answers (expected verdict `pass`).
  - Negative cases: first attempts with verdict `fail` where a follow-up was issued and a later attempt passed (expected verdict `fail`, expected `gap_reason` category if taxonomy exists).
  - Stratify per question: target ≥10 pass and ≥10 fail cases where data allows; sample for diversity.
- **FD-2** All case text is scrubbed (FB-2) before storage.
- **FD-3** Cases are stored in `intake_eval_cases` (`id`, `card_id`, `question_id`, `source_card_version`, `attempt_text`, `expected_verdict`, `expected_gap_category` nullable, `status` = `candidate` / `approved` / `retired`, `approved_by`, `notes`). Human spot-approval is required before a case is `approved`; a reviewer may bulk-approve.
- **FD-4** Cases carry `source_card_version` so that when a question is rewritten, cases built against the old guideline can be re-labeled or retired rather than silently failing.

### 8.3 Runner
- **FD-5** CLI/pytest entry point: `intake-eval run --card <id> --card-version <ver> [--model <name>] [--prompt-version <ver>]`. For each approved case, runs the real adherence evaluator (same code path as production, with examples from B if the card has them enabled) and records predicted verdict and reason.
- **FD-6** Report per card: accuracy, precision/recall for `fail`, per-question breakdown, and a list of flipped cases (expected ≠ predicted) with text. Output as JSON and a Markdown summary.
- **FD-7** Results stored in `intake_eval_runs` (`run_id`, `card_id`, `card_version`, `model`, `prompt_version`, `ran_at`, `metrics_json`, `flipped_case_ids`).
- **FD-8** Baseline comparison: `intake-eval compare <run_a> <run_b>` prints metric deltas and newly flipped cases.

### 8.4 CI integration
- **FD-9** Any PR that changes a YAML card runs the suite for that card against the PR's version; the job fails if `fail`-recall drops by more than a configurable threshold (default 5 points) or if any case tagged `critical: true` flips.
- **FD-10** Any change to the adherence prompt or model configuration runs the suite for all cards with ≥20 approved cases.
- **FD-11** Rewrite proposals from C run the suite automatically on the proposed version and attach the comparison to the proposal before review (so the reviewer sees "this rewrite keeps evaluator accuracy at X% and fixes/causes N flips").

### 8.5 Acceptance criteria
- [ ] D-AC1 Case builder produces stratified pass/fail cases per question with scrubbed text.
- [ ] D-AC2 Running the suite against the current production card version and model reproduces the expected verdicts at ≥95% on approved cases (establishes the baseline; cases that fail here are reviewed and relabeled or retired).
- [ ] D-AC3 A PR that weakens a guideline such that known-bad attempts now pass causes the CI job to fail with the flipped cases listed.
- [ ] D-AC4 `compare` between two runs lists metric deltas and newly flipped cases.

---

## 9. Privacy, security, and governance

- **PG-1** Raw attempt text is sensitive (may include names, system identifiers, business detail). It is readable only through the internal learning APIs behind the platform's standard auth and an `intake-learning-reviewer` role. The UAT app never calls these APIs.
- **PG-2** Every surface that shows attempt text to a reviewer (B curation, C review, D case approval) shows **scrubbed** text only. Raw text is accessible only by the ETL and scrubber jobs.
- **PG-3** Scrubber rules are configuration (regex + deny-list + optional NER), versioned, with a test fixture of known-sensitive strings that must all be redacted.
- **PG-4** Anything that reaches end users (approved examples in B) must be human-approved; no automated path from a past user's answer to another user's screen.
- **PG-5** Proposals and eval cases link back to `source_conversation_id` for audit, but the link is visible only to reviewers.
- **PG-6** Retention follows the existing conversation-log policy; derived tables are purged when their source conversations are purged, except approved examples and approved eval cases, which are retained as curated content with the source link removed.
- **PG-7** All LLM calls for proposal generation use the bank's approved model endpoint; no data leaves the approved environment.

## 10. Configuration

| Variable / YAML key | Purpose | Default |
|---|---|---|
| `INTAKE_LEARNING_ENABLED` | master switch for ETL, metrics, APIs | `false` |
| `INTAKE_LEARNING_WINDOWS` | metric windows in days | `30,90` |
| `INTAKE_LEARNING_MIN_SAMPLE` | low-confidence threshold | `20` |
| `INTAKE_LEARNING_FRICTION_WEIGHTS` | composite weights | `0.4,0.3,0.3` |
| `INTAKE_LEARNING_AUTO_PROPOSE` | enable scheduled proposals (C) | `false` |
| `INTAKE_LEARNING_PROPOSE_THRESHOLD` | friction score to auto-propose | `0.5` |
| `INTAKE_EVAL_FAIL_RECALL_DROP_MAX` | CI failure threshold (points) | `5` |
| YAML `questions[].id` | stable question identifier | required |
| YAML `questions[].required_by_policy` | guideline text that must not be weakened | `false` |
| YAML `learning.examples_enabled` | opt-in for B at runtime | `false` |

## 11. Delivery plan

| Phase | Scope | Exit criteria |
|---|---|---|
| 1 | §4 data model + ETL, Capability A metrics, API, Friction page | A-AC1–3 pass; backlog of top-10 high-friction questions reviewed with the team |
| 2 | Capability D case builder, runner, baseline, CI hook on YAML PRs | D-AC1–4 pass; baseline ≥95% on current cards |
| 3 | Capability B scrubber, curation UI, runtime examples on 1–2 opted-in cards | B-AC1–4 pass; first_pass_rate delta reported for opted-in cards |
| 4 | Capability C proposal generation and review flow, eval-on-proposal (FD-11) | C-AC1–5 pass; at least one rewrite shipped with before/after metrics |

D is sequenced before B and C deliberately: it is the safety net that lets later changes ship with confidence.

## 12. Deliverables
1. ETL job and normalized tables with Alembic migrations.
2. Metrics job, learning API router (`/api/intake-learning/*`), and internal Friction page.
3. Scrubber module with versioned rules and test fixtures.
4. Example curation UI and runtime example endpoint; adherence prompt change behind the per-card flag.
5. Rewrite proposal generator, review UI, YAML diff/PR integration.
6. `intake-eval` CLI, case builder, run storage, CI jobs.
7. `README-intake-learning.md` covering enabling each capability, roles, and how to interpret the Friction page and eval reports.

## 13. Open questions for the implementer
1. Do current YAML cards have stable `id` fields on questions? If not, propose an ID scheme and a one-time migration that preserves identity for existing questions.
2. Where is the adherence verdict and gap reason currently logged, and is the follow-up turn explicitly linked to the attempt it responds to? If not, specify the heuristic the ETL should use to pair them.
3. Is there an existing PII/sensitive-data scrubber in the platform that should be reused?
4. What is the YAML change process (repo, PR template, approvers) that Capability C should plug into?
5. Which internal role/group should map to `intake-learning-reviewer`?
