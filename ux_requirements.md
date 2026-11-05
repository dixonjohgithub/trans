# AIM Intake Quality — UX Redesign Requirements

**Scope:** MVP0 Intake Quality stage of the Agentic Intake Model (AIM)
**Status:** Draft for implementation
**Audience:** Implementing agent / engineering team
**Stack (existing):** React 19 + TypeScript frontend, FastAPI + Google ADK backend, per-intake YAML config, Jira as system of record

---

## 1. Problem statement

The current intake quality UI is a chat window wrapped in multi-step-form chrome. The agent performs semantic validation of each response against owner-defined guidelines — something a form cannot do — but the surrounding interaction makes the experience feel like a form with an error message:

- Every turn is treated as a fresh full submission ("Please send your full answer again, not just the missing part").
- Questions are asked one at a time, in fixed order, with future questions marked **Locked**.
- Three overlapping progress indicators (stepper, step progress bar, "N of 7 questions answered" + %) plus Current/Done/Locked badges.
- Agent messages are rigid templates with bold labels (`Thanks, noted X. Question: …` / `Why this didn't meet the guidelines: … Tip: … Example: … Question: …`) that restate the canonical YAML question verbatim every turn.
- The rejection Example uses `<team name>` placeholders even when the agent already knows the request's subject from the user's prior answers.
- The opening message announces the form model: "I'll walk you through a few questions, one at a time."

Users report it "feels form-based, not AI." The content validation is the strong part and must be preserved; the interaction around it is what needs to change.

## 2. Goals

1. Preserve the quality bar: every response is still evaluated against the owner's guidelines before it reaches Jira.
2. Make the agent's reasoning visible and collaborative rather than purely evaluative.
3. Eliminate retyping: a user never re-enters text the agent has already captured.
4. Support two selectable UX modes over the same backend so they can be A/B tested with real intake users:
   - **Mode A — AI-assisted form**
   - **Mode B — conversational intake**
5. Keep the per-question → Jira-field contract intact in both modes.
6. Define `MAX_ATTEMPTS` behavior so that low-quality information is never *silently* written to Jira.

## 3. Non-goals

- Changing guideline semantics or how the owner authors the YAML (additions are backward-compatible and optional).
- Changing duplicate detection (MVP1) or classification (MVP2).
- Changing the Jira workflow, issue types, or field mappings.
- Replacing the Agentspace / ADK agent architecture.

## 4. Hard constraints

| Constraint | Implication |
|---|---|
| Each intake question maps to one Jira field (defined in the intake YAML), and **several questions may map to the same field**; their responses are aggregated into that field at submission, as today. | Both modes must produce exactly one final response string per question ID. Free-text that spans several questions must be split and attributed to question IDs before submission. The existing aggregation step (question order and separator format) is preserved unchanged; this spec only adds the quality header to it. |
| Jira is the workflow system of record. | Quality flags, attempt counts, and agent assessments must land in Jira (field, label, or comment) so owners act on them inside their existing board. |
| Jira writes use the submitting user's credentials. | No change; submission path is unchanged. |
| Guidelines are owner-authored per question. | The validator continues to evaluate against the owner's guideline text. New optional YAML keys (§8) refine behavior but never replace the guideline. |
| Corporate environment: Gemini flash-tier models via the platform. | Extraction and merge steps must tolerate imperfect model output: every agent-drafted or agent-merged text is shown to the user and requires explicit confirmation before it is marked accepted. |

## 5. Shared backend requirements (mode-agnostic)

These changes apply regardless of UI mode. Mode A and Mode B are two renderings of the same state machine.

### 5.0 LLM call budget (governs everything below)

The platform has material per-call latency, and several existing UI behaviors are deliberately deterministic to avoid an LLM round trip. That decision stands. Rules for this spec:

1. **At most one LLM call per user turn** in the main flow. That call is the validation call that already exists; this spec widens its output, it does not add calls alongside it.
2. **Zero LLM calls** for: the opener, acknowledgments, presenting a new question (canonical YAML text), state transitions, the review screen, example placeholder filling, and Jira submission.
3. Any step that would require a second call is either folded into the single call's structured output, made deterministic, or feature-flagged off by default and listed as such.
4. Perceived latency is reduced with deterministic optimistic UI (an immediate acknowledgment line while the call runs) and, where the platform supports it, streaming of the follow-up text.

| Step | Calls | How |
|---|---|---|
| New question presented | 0 | Canonical YAML text, deterministic template |
| User answers a question | 1 | Single validation call returns merge + assessment + follow-up (§5.2) |
| Accepted, single fragment | 0 extra | No confirmation card; move on |
| Accepted after merge | 0 extra | Confirmation card renders the merged text already returned |
| Follow-up on partial | 0 extra | Follow-up text already returned by the validation call |
| Agent proposes a value | 0 extra | Included in the same call's output when inferable (§7.4) |
| Example on request | 0 | Deterministic substitution from prior answers into YAML `examples` |
| Multi-question extraction | 1 | Only on explicit paste-to-fill or opening free-text; feature-flagged (§5.6) |
| Mode A field Check | 1 | On explicit user action only, never on blur |
| Mode A Draft assist | 1 | On explicit user action only |

The conversational quality this spec is after comes from what the single call *returns* and from the wording of the deterministic templates — not from additional model trips.

### 5.1 Per-question response state

A per-question state model already exists in the platform. Extend it rather than replace it; the target shape is below. Map existing states onto these names where they correspond and add only what is missing (`drafted`, `accepted_with_flag`, `deferred`, `fragments[]`, `provenance`).

| State | Meaning |
|---|---|
| `empty` | Nothing captured. |
| `partial` | Something captured but guideline not yet satisfied; attempt count > 0. |
| `drafted` | Agent produced or merged text that the user has not confirmed. |
| `accepted` | User-confirmed text that satisfies the guideline criteria. |
| `accepted_with_flag` | User-confirmed text that does not satisfy all criteria; written to Jira with a quality flag (see §5.5). |
| `deferred` | User explicitly skipped. Required questions must leave this state before submission; optional questions (existing flag) may be submitted as `deferred`. |

Each question record holds:

```
question_id
state
captured_text          # the current best response text (merged across turns)
fragments[]            # ordered list of {turn_id, text, source: user|agent}
attempts               # number of validation passes that returned "not met"
last_assessment        # {met: bool, covered: [criteria], missing: [criteria], confidence}
provenance             # user | agent_drafted | agent_merged (resolved to `user` once confirmed)
```

### 5.2 Accumulate-and-merge validation

**Current behavior to remove:** validator evaluates only the latest message and asks the user to resend the full answer.

**Required behavior — one call:**

1. On each user turn for a question, append the new text as a fragment (deterministic).
2. Make **one** validation call with: the guideline (and `criteria` if present), all fragments in order, and the prior turns' acknowledged content for this question. The call returns a single structured object:
   ```json
   {
     "captured_text": "<all fragments merged into one coherent response; user's wording preserved; no added facts>",
     "merged": true,
     "met": false,
     "covered": ["problem described", "current state is manual"],
     "missing": ["teams/roles involved today", "systems involved today"],
     "confidence": 0.86,
     "follow_up": "Got it — policy impact assessment is manual today. Who does that review now, and where are the results recorded?",
     "proposed_value": null
   }
   ```
   - `captured_text` is the merge. When there is a single fragment it is returned unchanged and `merged` is `false`.
   - `follow_up` is populated only when `met` is false (§5.4). It is the text shown to the user; no separate generation call.
   - `proposed_value` is an optional confirmable guess (§7.4), populated only when inferable from the fragments or prior answers supplied in the call.
3. If `met` → state `accepted`. If `merged` is true, the UI shows the confirmation card (§5.3) using the returned text; no further call.
4. If not met → state `partial`; the UI shows `follow_up`. No full rejection, no restated question.

The user is never asked to resend text already captured. The existing validation prompt is extended to produce this object; the existing single call per turn is preserved.

### 5.3 Merged-text confirmation

Whenever `captured_text` was produced by merging two or more fragments (`merged: true`), or was agent-drafted, show it to the user and require explicit confirmation ("Looks right" / edit) before marking `accepted`. Confirmation converts `provenance` to `user`. Confirmation is a deterministic state transition — no call. A user edit to the merged text re-runs the single validation call once.

When `merged` is `false` and `met` is true, skip the card entirely: acknowledge and move on.

### 5.4 Targeted follow-up generation

The follow-up is the `follow_up` string returned by the validation call (§5.2); it is not generated separately. The validation prompt instructs the model to compose it as:

1. One clause acknowledging what was captured, in the user's own terms.
2. One question asking for the single most important missing criterion (or two if tightly related).
3. Optional: an agent-proposed value when it can be inferred from context, phrased as a confirmable guess.

The follow-up MUST reference the user's own content. Example, given the user wrote that policy impact assessment is manual and error-prone:

> Got it — policy impact assessment is manual today and that's the pain. Who does that review now, and where do the results get recorded? (e.g. a governance team working in a specific system)

Tip and Example content from the guideline moves behind the existing **Help** affordance and the right-hand Guidelines panel; it is not repeated in the follow-up.

If the YAML supplies `examples` (§8), placeholder filling is **deterministic string substitution** from already-accepted answers (e.g. `{title}`, `{team}` if a prior question captured it); unfilled placeholders remain as readable placeholders. No model call.

### 5.5 `MAX_ATTEMPTS` policy

`MAX_ATTEMPTS` is a per-intake (optionally per-question) integer. Behavior on reaching it for a **required** question is a configurable policy, `on_max_attempts`, with three values (optional questions always behave as `flag_and_continue` — see §8 notes):

| Value | Behavior |
|---|---|
| `block` | User cannot proceed past the question. Intake cannot be submitted. (Current implicit assumption; **not recommended** — see rationale.) |
| `flag_and_continue` | **Recommended default.** Agent produces its best merged `captured_text` from all fragments, shows the user what is still missing, and lets them confirm. Question enters `accepted_with_flag`. On Jira submission a quality header is prepended to that field's text (§9) so the owner sees the gap exactly where they read the answer. |
| `escalate` | Same as `flag_and_continue`, plus the agent posts a Jira comment addressed to the intake owner summarizing the gap, so clarification happens asynchronously in Jira rather than in a refinement meeting. |

**Rationale.** The quality goal is to stop *unmarked* low-quality responses from reaching review. A hard block has two costs: abandoned intakes, and users routing around the platform via email/Teams (zero quality, zero visibility). `flag_and_continue` preserves the quality signal — the owner knows exactly which field is weak and why — while keeping the intake in the governed path. It converts a refinement meeting into a comment thread. Make the policy configurable so owners who insist on a hard gate can have it, and measure abandonment and flag rates per intake to inform the default.

Flagged responses are never written to Jira as if they were accepted. The flag is mandatory and visible.

### 5.6 Multi-question extraction (feature-flagged; off by default)

This is the one capability that costs an additional call. It is gated behind `extraction_enabled: true` in the intake YAML and triggers only on (a) the opening free-text message in Mode B when the user writes more than a configurable length, or (b) an explicit paste-to-fill action in either mode. Ordinary turns answering a single question never invoke it.

When enabled, one call takes the free-text message and the full question set and:

1. Attributes spans of the message to zero or more question IDs **and** evaluates each attributed span against its guideline in the same call, returning the §5.2 object per touched question.
2. Each attributed span is appended as a fragment; states update deterministically from the returned objects.
3. Returns a coverage summary: which questions were touched, their new states.
4. Unattributed content is retained in a scratch buffer and offered to the user ("I couldn't place this — which question does it belong to?").

Extraction uses the question text, guideline, and optional `extraction_hints` (§8). Low-confidence attributions (below a configurable threshold) are presented as proposals, not auto-applied. Treat this as a later phase (§12); the rest of the spec does not depend on it.

### 5.7 Mode assignment and experiment support

- Intake YAML may set `ux_mode: form | conversational | user_choice` (default `user_choice`).
- `user_choice` shows a mode picker at intake start; the choice is recorded.
- Optional: `ux_mode_assignment: random` for a 50/50 split; assignment recorded on the intake record.
- All telemetry events (§9) carry `ux_mode`.

## 6. Mode A — AI-assisted form

A conventional form with the validator attached to each field. Intended for users who prefer to see everything at once and work in their own order.

### 6.1 Layout

- All questions rendered as labeled fields, grouped by the YAML `category` (collapsible sections). Nothing is locked.
- Each field shows: label (question text), the guideline summary (one line, expandable to full guideline), the text area, and an assessment strip beneath.
- A single overall completion indicator (e.g., "5 of 7 fields ready"). No stepper, no percentage bar.

### 6.2 Per-field behavior

- On an explicit **Check** action only (never on blur — that would fire a call per field visit), run the single validation call (5.2) and render the assessment strip:
  - ✔ covered criteria listed inline (brief)
  - ◌ missing criteria listed inline with the targeted follow-up text (5.4)
- **Draft assist** button per field: the agent proposes a filled-in response using the guideline, examples, and any content already present in other fields. Proposed text is inserted with a visible "drafted — review before accepting" marker; user edits/accepts.
- **Paste to fill** (only when `extraction_enabled`): a top-level paste area where the user can drop a document or description; multi-question extraction (5.6) pre-fills fields as `drafted`.

### 6.3 Submission

- Submit enabled when every required question is `accepted` or `accepted_with_flag` (per `on_max_attempts`); optional questions may be `empty`, `deferred`, `accepted`, or `accepted_with_flag`.
- Pre-submit review panel lists each field, its state, and any flags.

## 7. Mode B — Conversational intake

A conversation that builds the same per-question record set. The left panel becomes a live coverage map rather than a locked checklist.

### 7.1 Opening

Replace the current opener. Required shape:

> Welcome to the **{intake name}** intake. Tell me about the request in your own words — what you're trying to get done and why. I'll capture it against what the {owner team} needs and only ask about what's missing. You can also answer the questions on the left directly, in any order.

No "one at a time." No "walk you through."

### 7.2 Left panel — coverage map

- Lists all questions grouped by category. None are locked.
- Each item shows state (empty / partial / drafted / accepted / flagged / deferred) with a subtle indicator — not Current/Done/Locked badges.
- Clicking an item:
  - `empty` → the agent asks that question next.
  - `partial` / `drafted` / `accepted` → opens the captured text for review/edit; edits re-run validation.
  - `deferred` → un-defers and asks.
- Remove the top stepper, "Step N of 4" bar, and percentage. Keep one lightweight completion count if desired ("4 of 7 ready").

### 7.3 Agent turn behavior

1. User message arrives for the current question → **immediately** render a deterministic optimistic line ("Checking that against what the team needs…") → one validation call (5.2). (If `extraction_enabled` and this is the opening free-text, the extraction call runs instead — §5.6.)
2. When the call returns, the agent message is assembled **deterministically** from the returned object and templates (§7.6):
   - If `met` and not merged: deterministic acknowledgment that quotes a short span of the user's own text, then the next canonical question. Zero extra calls.
   - If `met` and merged: the confirmation card with the returned `captured_text`; on confirm, the next canonical question.
   - If not `met`: the returned `follow_up` string (and `proposed_value` if present, rendered as a confirmable chip). No restated question, no Tip/Example.
3. The next question is presented using its canonical YAML `text`. Contextual paraphrasing of new questions is **not** done (it would cost a call); the conversational feel comes from the follow-ups and the acknowledgment wording. Optional future: ask the validation call to also return a one-line `next_question_lead_in` for the following question, which keeps it at one call per turn — listed in §13.
4. No bold label templates (`Question:`, `Tip:`, `Why this didn't meet the guidelines:`). Deterministic templates are written as sentences.
5. The user may at any time:
   - Say "skip" / "come back to that" → `deferred` (deterministic intent match on a small phrase list; no call).
   - Ask for an example / help → serve guideline Tip/Example with deterministic placeholder filling; no call.
   - Click a left-panel item to redirect (deterministic).
   - Answer several questions in one message — only when `extraction_enabled`.

### 7.4 Agent contributes, not only requests

Where the validation call can infer a plausible value for a missing criterion from the fragments or the prior accepted answers passed into it, it returns it as `proposed_value` in the same response — no additional call. The UI renders it as a confirmable chip alongside the follow-up:

> Who does that review now? — *Sounds like a policy governance team; is that right?* [Yes] [Edit]

A wrong guess is acceptable; the user corrects it. A guess never enters `captured_text` until the user confirms, at which point it is appended as a fragment and the next turn's validation call sees it. Corpus-backed guesses (using the duplicate-detection corpus) would require retrieval and are out of scope for this phase.

### 7.5 Review and submit

When all required questions are `accepted` / `accepted_with_flag`:

- Agent presents a compiled review grouped by target Jira field: for a field fed by several questions, show the aggregated text as it will be written, with each contributing question's label and flag status visible.
- User can edit any item inline (re-validates) or confirm.
- On confirm → existing duplicate detection step → Jira submission (unchanged path).

### 7.6 Message templates (replace existing)

All templates below are **deterministic** string templates filled from the validation call's returned object and the YAML — they are not prompts. Only `{follow_up}` and `{proposed_value}` are model-generated, and both come from the single call already made. Wording may be tuned; structure is required.

**Optimistic line (shown immediately on send)**
```
Checking that against what {owner_team} needs…
```

**Acknowledge + next question (met, not merged)**
```
Got it — "{first_n_words_of_captured_text}…" {next_question_canonical_text}
```
`{first_n_words_of_captured_text}` is a deterministic truncation (e.g. first 8–12 words) of the user's own answer, which is what makes the acknowledgment feel read rather than generic. No model call.

**Targeted follow-up (not met)**
```
{follow_up}
```
Rendered as-is from the call. If `proposed_value` is present, render beneath it as a confirmable chip.

**Merge confirmation**
```
Here's what I have for "{question_short_label}":
> {captured_text}
Does that capture it? You can edit it or just say yes.
```

**Max attempts (flag_and_continue)**
```
I'll record what you've given me for "{question_short_label}" and note for the {owner team} that {missing_criteria_plain_language} is still open. They may follow up in Jira. Want to add anything before we move on?
```

**Help / example**
```
{guideline_tip}
For example: {example_filled_from_prior_answers_or_placeholders}
```

## 8. YAML schema extensions (backward compatible)

All new keys are optional. Existing YAML files continue to work unchanged.

```yaml
intake:
  name: Consumer Intelligent Automation
  owner_team: Consumer Intelligent Automation
  ux_mode: user_choice            # form | conversational | user_choice
  ux_mode_assignment: null        # null | random
  max_attempts: 3
  on_max_attempts: flag_and_continue   # block | flag_and_continue | escalate
  jira:
    project_key: CIA
    issue_type: Intake
    quality_header_template: |              # NEW — prepended once to any Jira field that contains a flagged response
      ⚠ AIM QUALITY NOTE — {flagged_count} of {total_count} responses in this field did not fully meet guidelines.
      {for each flagged: • {short_label} ({attempts} attempts) — missing: {missing_criteria}}
      ---
    quality_flag_label: aim-needs-refinement   # NEW, optional — applied only if the project permits labels

categories:
  - id: basic
    label: Basic Information
  - id: problem_value
    label: Problem and Value

questions:
  - id: q3
    category: problem_value
    text: "Please provide the problem description of the request in detail. What process or task would you like automated, and who is involved today?"
    short_label: Problem description          # NEW — used in UI and review
    guideline: |
      Describe the current process and name the teams, roles, or systems
      involved today. Non-technical terms. Include a deadline only if one applies.
    required: true                            # existing — unchanged; drives blocking behavior (see notes)
    why: "The automation team needs the current-state actors to scope the work."   # NEW — surfaced on request
    criteria:                                 # NEW — optional explicit rubric; validator uses these for covered/missing
      - problem described
      - teams or roles involved today
      - systems involved today
      - deadline if applicable
    examples:                                 # NEW — placeholders filled from prior answers where possible
      - "{team} currently reviews new policies manually and records results in {system}. {teams} are involved today."
    extraction_hints:                         # NEW — phrases that signal content for this question in free text
      - "today"
      - "currently"
      - "manual"
      - "involved"
    max_attempts: null                        # NEW — per-question override
    jira_field: description                   # existing — may be shared by several questions; responses aggregate into the field in YAML question order, as today
```

Notes:
- `jira_field` is many-to-one. The aggregation format (order, separators, whether question labels are included) is whatever the current implementation does; this spec does not change it.
- The existing `required` flag is reused, not duplicated:
  - **Required** question, guideline not met after `max_attempts` → `on_max_attempts` policy applies (`block` can prevent submission).
  - **Optional** question → may be `deferred` at submission with no flag. If the user answers it and the guideline is not met after `max_attempts`, it is always treated as `flag_and_continue` regardless of the intake-level policy; an optional question never blocks.
  - Either way, an answered question is validated the same way; required/optional only changes what happens when it can't be satisfied.
- If `criteria` is absent, the validator derives covered/missing from the guideline text as it does today.

## 9. Jira integration requirements

- Field population is unchanged: each question's confirmed `captured_text` is written to its `jira_field`; where several questions share a field, they are aggregated in the existing order and format.
- If **any** question feeding a field is `accepted_with_flag`, a single rendered `quality_header_template` is prepended to that field's aggregated text, listing every flagged question that contributes to the field. The individual question sections within the aggregate are not altered. Example for a `description` field fed by two questions, one flagged:
  ```
  ⚠ AIM QUALITY NOTE — 1 of 2 responses in this field did not fully meet guidelines.
  • Problem description (3 attempts) — missing: teams or roles involved today; systems involved today
  ---
  [existing aggregated content, in the existing format]
  ```
  One header per field, not per question, so the strip rule for downstream consumers stays simple and the field reads cleanly. The header opens with a fixed string so owners can find flagged intakes with a text search (e.g. JQL `description ~ "AIM QUALITY NOTE"`). No custom fields are required.
- The `quality_header_template` in YAML therefore takes a list of flagged questions (`{flagged_questions}` with per-item `{short_label}`, `{attempts}`, `{missing_criteria}`) rather than a single question's values.
- If `quality_flag_label` is set and the project permits labels, also apply the label; this is optional and exists only to make board filtering easier. Do not fail submission if the label cannot be applied.
- For `escalate`: additionally post a comment summarizing all flagged questions and mentioning the owner team / assignee per existing Jira conventions.
- Owners find flagged intakes by header text search (or label) — this is the replacement for the refinement meeting.
- Downstream consumers of field text (e.g. MVP3 artifact creation) must strip the header block (everything up to and including the `---` line) before reusing the text.
- No changes to issue transitions, workflow, or credential handling.

## 10. Telemetry (required for the A/B evaluation)

Emit per intake session, tagged with `ux_mode`:

- `intake_started`, `intake_submitted`, `intake_abandoned` (with last state snapshot)
- Per question: `attempts`, final `state`, time-to-accepted, whether a merge/draft occurred, whether user edited a draft
- Count of `accepted_with_flag` per intake
- Count of user clicks on left-panel items / out-of-order answers (Mode B)
- Count of Draft-assist / Paste-to-fill uses (Mode A)
- Post-submit: whether the owner later edited any flagged field in Jira (via Jira webhook or periodic poll) — this is the downstream quality signal

Primary comparison metrics between modes:
1. Submission rate (vs. abandonment)
2. Flagged-field rate per intake
3. Owner edit rate on submitted fields (proxy for "refinement needed")
4. Median time to submit
5. User-reported satisfaction (1-question prompt at submit)

## 11. Acceptance criteria

**Shared**
- [ ] A user is never prompted to resend text that was already captured.
- [ ] Every merged or agent-drafted text is shown and confirmed before state becomes `accepted`.
- [ ] Validator returns structured `covered` / `missing` / `confidence` for every evaluation.
- [ ] `on_max_attempts` is configurable per intake; `flag_and_continue` prepends the quality header to the flagged field's text in Jira; `block` prevents submission.
- [ ] Flagged field text in Jira is findable by text search on the fixed header string.
- [ ] Every question ID still resolves to exactly one final string, written to its mapped Jira field; fields shared by several questions aggregate exactly as they do today.
- [ ] A shared field with one or more flagged responses carries exactly one quality header, listing each flagged question.
- [ ] Existing intake YAML files load without modification.

**Mode A**
- [ ] All questions visible; none locked; per-field Check and Draft-assist work.
- [ ] Paste-to-fill populates multiple fields as `drafted`.

**Mode B**
- [ ] Opener does not announce one-at-a-time questioning.
- [ ] A single user message can resolve or partially resolve multiple questions.
- [ ] Follow-ups reference the user's own content and ask for the missing criterion only.
- [ ] No bold-label message templates; canonical question text appears only in the left panel and Guidelines panel.
- [ ] Left-panel items are clickable for redirect, review, and edit.
- [ ] Review screen appears before duplicate detection and submission.

**Experiment**
- [ ] Mode is selectable (or randomly assigned) and recorded; all telemetry events carry `ux_mode`.

## 12. Suggested implementation sequence

1. Widen the existing validation call's output to the §5.2 object (merge + assessment + follow-up + proposed value) and pass fragments + prior answers into it. Extend the existing per-question state (5.1). This alone removes "resend your full answer" and the five-part rejection, at the same call count as today.
2. Replace the deterministic message templates (7.6) and add the optimistic line. Zero new calls.
3. `on_max_attempts` policy and Jira header writing (5.5, 9).
4. YAML schema extensions and loader (8).
5. Mode B UI: remove stepper/progress chrome, unlock left panel, new opener, review screen.
6. Mode A UI.
7. Mode selection + telemetry (5.7, 10).
8. Multi-question extraction (5.6), feature-flagged — only after measuring whether the one extra call on the opening message is worth its latency.

Steps 1–3 are mode-agnostic and should ship first; they improve the existing experience without waiting for either new UI and without adding a single model trip.

## 13. Open decisions

- Default for `on_max_attempts` across the 120+ intakes: proposal is `flag_and_continue`; confirm with the intake governance group.
- Final wording of the quality header, and whether the optional label is enabled per project.
- Whether to ask the validation call to also return a `next_question_lead_in` (one contextual sentence introducing the following question) — still one call per turn, but a longer response; decide after measuring token/latency cost.
- Whether the platform supports streaming for the `follow_up` string; if so, stream it to cut perceived latency.
- Length threshold and latency acceptance for enabling extraction on the opening message.
- Extraction confidence threshold for auto-applying attributed spans vs. proposing them.
- Whether the mode picker is shown per intake or remembered per user.
