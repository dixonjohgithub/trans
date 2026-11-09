# Generic Intake (Try-It Mode) — Specification and Requirements

**Status:** Draft v1.0
**Owner:** JD (Principal AI Engineer)
**Target:** Agentic Intake Platform — React 19 + TypeScript frontend, FastAPI + Google ADK backend
**Related specs:** UAT Feedback Widget; Intake Learning Loop

---

## 1. Purpose

Let a potential adopter experience the full intake workflow — intake quality (MVP0), duplicate detection (MVP1), and classification (MVP2) — in minutes, without onboarding their own intake YAML, Jira board, or roadmap (which can take weeks). The generic intake runs the same agents and the same code paths as a real intake, but against platform-provided sample configuration, and ends with an on-screen summary and a **Finish** button instead of a Jira submission.

Secondary purpose: turn the demo into the first step of onboarding. Everything the adopter touches (sample questions, a pasted roadmap, their own answers) can be exported as a starter YAML so the demo session becomes the seed for their real intake.

## 2. Goals and non-goals

### Goals
- Zero-setup entry: a user opens the app, picks "Try the generic intake", and is in the conversation within one click.
- Exercise every production stage with production code; only the configuration and the final sink differ.
- Make the value of each stage visible: what the agent caught, what it would have cost without it, and what would have landed in Jira.
- No Jira credentials, no enterprise repository access, no team roadmap required.
- Produce a take-away (summary, starter YAML) the adopter can bring to their team.

### Non-goals
- Not a sandbox for editing agent logic or prompts.
- No persistent user accounts; sessions are anonymous or name-only (consistent with the UAT app having no auth).
- No writes to any Jira instance, even a sandbox, in this version.
- Not a replacement for real onboarding; it demonstrates and seeds onboarding.

## 3. User stories

| ID | As a… | I want… | So that… |
|---|---|---|---|
| US-1 | Prospective intake owner | to try the intake flow with no setup | I can judge fit before committing onboarding effort |
| US-2 | Prospective intake owner | to see the agent reject a weak answer and explain why | I understand how it reduces refinement meetings |
| US-3 | Prospective intake owner | to see duplicate candidates surface against a realistic corpus | I understand the reuse/avoid-rework value |
| US-4 | Prospective intake owner | to see how a request classifies against a roadmap with confidence scores | I understand how roadmap-aligned work gets flagged |
| US-5 | Prospective intake owner | a summary of what each stage did and what Jira would have received | I can show my leadership the outcome |
| US-6 | Prospective intake owner | to paste my own questions or roadmap and rerun | I can see it work on my material, not just the sample |
| US-7 | Prospective intake owner | to export a starter YAML from the session | onboarding starts from something real |
| US-8 | Platform team | to see who ran the demo, how far they got, and what they thought | we can follow up with warm leads and fix drop-off points |

## 4. Workflow

```
Landing: "Try the generic intake"
  │   pick a scenario (or "blank"), optionally enter name/team
  ▼
Stage 1 — Intake Quality (MVP0)
  │   generic card: 6–8 questions, guidelines, categories
  │   same chat UI, same accept/reject/re-ask loop
  │   stage summary panel updates live
  ▼
Stage 2 — Duplicate Detection (MVP1)
  │   runs against the platform demo corpus (seeded with planted near-matches)
  │   user sees candidates, can "stop" or "continue" exactly as in production
  ▼
Stage 3 — Classification (MVP2)
  │   runs headless against the demo roadmap (or a user-pasted roadmap)
  │   on-screen: tags, confidence, threshold, below-threshold candidates
  ▼
Stage 4 — Summary & Finish  (replaces Jira submission)
      per-stage recap, "what Jira would have received" preview,
      value metrics, export options, feedback prompt, Finish / Run again
```

## 5. Functional requirements

### 5.1 Entry and session
- **GR-1** A "Try the generic intake" entry point on the app landing page (and a direct route `/try`) that requires no login.
- **GR-2** Session is identified by a server-generated `demo_session_id`; optional fields `tester_name` and `team` (2–80 chars each) are collected on the landing screen and reused by the UAT feedback widget if it is enabled.
- **GR-3** Scenario picker (see §6.2): the user chooses a pre-written scenario that pre-fills context (a short description of the "situation" they are submitting for) or starts blank. Scenarios do not pre-fill answers; they give the user a story to answer from.
- **GR-4** The session can be restarted at any time ("Start over"); a restart creates a new `demo_session_id`.
- **GR-5** Session state is held server-side and expires after 24 h; the frontend holds only the session id.

### 5.2 Stage 1 — Intake quality
- **GR-6** The generic intake is an ordinary intake YAML card (`cards/generic-work-request.yaml`) processed by the existing MVP0 engine with **no code branches for demo mode** in the intake quality agent itself.
- **GR-7** Card contents (initial; owner may tune):
  - Categories (UX grouping only): `Problem`, `Outcome`, `Scope & Impact`, `Logistics`.
  - Questions (each with `id`, `guideline`, `required`, category, and a Jira field mapping used only for the preview in §5.5):

    | id | Question | Guideline summary | Required |
    |---|---|---|---|
    | `title` | Give this request a short title | ≤ 12 words, names the capability not the solution | yes |
    | `problem` | What problem are you trying to solve? | Describes who is affected, what happens today, and why it matters; not a solution statement | yes |
    | `outcome` | What does success look like? | At least one measurable or observable outcome | yes |
    | `users` | Who are the users or stakeholders? | Names roles/teams, approximate count or scale | yes |
    | `impact` | What is the business impact if this is not done? | Quantified or clearly qualified (risk, cost, time, compliance) | yes |
    | `scope` | What is in and out of scope? | At least one explicit in-scope and one out-of-scope item | no |
    | `timing` | When is this needed and why? | A date or event plus the driver behind it | no |
    | `existing` | Is there anything that does this today, even partially? | Names systems/processes or states "none known" | no |
- **GR-8** Guidelines are written to be intentionally demonstrable: a one-line vague answer to `problem` or `impact` must be rejected with a clear explanation, so a first-time user sees the loop within the first two questions.
- **GR-9** The existing per-question response state model, required/optional handling, and `MAX_ATTEMPTS` behave exactly as in production. For the demo card, `MAX_ATTEMPTS` is set to 3 and reaching it lets the user continue with the answer flagged "accepted with reservations" (recorded in the summary).
- **GR-10** A **Stage summary panel** (right rail or collapsible drawer on narrow screens) shows live: questions answered / remaining, attempts per question, number of rejections and the one-line reason for each, and elapsed time.
- **GR-11** An optional **"Why did it ask that?"** affordance on each follow-up reveals the guideline text the answer was checked against. Default collapsed. Logs an event when opened.

### 5.3 Stage 2 — Duplicate detection
- **GR-12** Runs the production Duplicate Detection Agent (aggregated-response embedding over the `IntakeCorpusRecord` schema) against a **demo corpus** instead of enterprise repositories.
- **GR-13** Demo corpus: 150–300 synthetic `IntakeCorpusRecord` rows, generated once and checked into the repo as a fixture (`fixtures/demo_corpus.json`), covering common bank request types (analytics, automation, access, reporting, integration, support tooling). Records carry a fake source (`DEMO-JIRA`, `DEMO-INVENTORY`) and fake keys so they are visibly not real.
- **GR-14** Each scenario in §6.2 has at least one **planted near-duplicate** in the corpus so that a user who follows the scenario reliably sees a strong candidate, and at least one plausible-but-different record so they see a weak one. Scenario text and planted records are authored together.
- **GR-15** The user sees candidates exactly as in production (title, source, similarity score, matching excerpt) and the same **Stop / Continue** choice. Choosing Stop ends the workflow and goes straight to the Summary with a "stopped at duplicate detection — potential reuse of DEMO-JIRA-1042" line, which is itself a value demonstration.
- **GR-16** A **"Try it against your own list"** option: user pastes up to 200 lines of `title | description` (or uploads a CSV with those two columns); the agent embeds them on the fly, merges them with the demo corpus, and reruns. Pasted data lives only in the session and is discarded on expiry.
- **GR-17** Embedding model and threshold are the production settings; the panel shows the threshold value and the model name so the user understands the mechanics.

### 5.4 Stage 3 — Classification
- **GR-18** Runs the production classification agent headless, consuming only intake-quality output, against a **demo roadmap** in the canonical classification YAML format (`fixtures/demo_roadmap.yaml`, ~8 roadmap items with descriptions and key capabilities, matching the realistic "fewer than 10 items" case).
- **GR-19** Each scenario is written so that at least one roadmap item scores above threshold and at least one lands just below it, so the user sees both an applied tag and a "recorded in notes, not applied" candidate.
- **GR-20** Results screen shows: applied tags with confidence, below-threshold candidates with confidence, the threshold value, and the one-paragraph rationale per candidate. A **threshold slider** (demo-only UI; does not change production config) lets the user drag the threshold and watch tags move between "applied" and "candidate" — this makes the confidence mechanism tangible.
- **GR-21** **"Use your own roadmap"** option: user pastes roadmap text in any structure (bullets, headings, a table) or uploads a `.md`/`.txt`/`.docx`. The platform's roadmap-to-canonical-YAML transformation runs, shows the resulting YAML for confirmation/edit, then classification reruns against it. This exercises the exact capability a real onboarding needs and lets the adopter see their own roadmap items light up.

### 5.5 Stage 4 — Summary and Finish (replaces Jira submission)
- **GR-22** No Jira call is made. The summary screen is the terminal stage and is reachable only after Stage 3 completes or after a Stop in Stage 2.
- **GR-23** Summary sections:
  1. **Intake quality recap** — final accepted answer per question; count of first-pass accepts vs. rejections; the rejection reasons; any "accepted with reservations".
  2. **Duplicate detection recap** — candidates found, scores, user's Stop/Continue decision.
  3. **Classification recap** — tags applied, candidates, threshold, rationale.
  4. **What Jira would have received** — a read-only mock of the issue: fields populated via the card's Jira mapping (including many-to-one aggregation of several answers into one field), the roadmap tag(s), and the notes block containing below-threshold candidates. Rendered as a plain issue preview, with no Jira branding, so it is clearly a mock-up.
  5. **Value metrics** (see §6.1).
  6. **Take-aways** — export buttons (§5.6).
  7. **Feedback** — if the UAT feedback widget is enabled, an inline prompt "How was that? Tell us" opens the same widget with type pre-set to `Suggestion` and the session id attached.
- **GR-24** **Finish** button: marks the session `completed`, shows a short thank-you with a "Start over" and "Request onboarding" link (the latter opens a mailto or internal form configured in settings — no Jira).
- **GR-25** **Run again with the same answers** button: re-enters Stage 2 or Stage 3 with the user's accepted answers retained, so they can try their own list or roadmap without re-answering questions.

### 5.6 Exports
- **GR-26** Summary as **Markdown** and **PDF** (server-rendered), containing sections 1–5 of the summary. Filename `intake-demo-summary-<date>.md|pdf`.
- **GR-27** **Starter intake YAML**: the generic card with the user's session edits applied (any questions they marked "not relevant to us" in the summary, any roadmap they pasted converted to canonical YAML, and the Jira mapping left as placeholders). Filename `intake-starter-<team>.yaml`. This is the onboarding seed.
- **GR-28** **Session JSON**: full structured record (answers, verdicts, candidates, classification output) for engineers who want to inspect it.
- **GR-29** Exports never include the demo corpus or other users' data.

## 6. Making the value visible

### 6.1 Value metrics on the summary screen
Computed from the session; shown with a one-line explanation each. All are deterministic (no LLM call).

| Metric | How computed | What it demonstrates |
|---|---|---|
| Low-quality answers caught | number of rejected attempts | the refinement meetings avoided |
| First-pass quality rate | first-pass accepts ÷ required questions | how far the user's natural answers were from the guideline |
| Potential duplicates surfaced | count of candidates ≥ threshold | rework/reuse awareness |
| Roadmap alignment | tags applied and top confidence | prioritization signal available at submission time |
| Jira fields auto-populated | fields in the mock issue with content ÷ mapped fields | manual ticket-writing eliminated |
| Time in intake | elapsed wall-clock | sets expectations for real users |

### 6.2 Scenarios
A scenario gives the user a realistic situation to describe, so they are not inventing a request from nothing. Each is a 3–5 sentence brief plus hints, authored together with its planted duplicates and roadmap alignment.

Initial set (owner may add):
1. **Reporting automation** — a team re-keys numbers from three systems into a weekly deck. Planted near-dup: an existing "Weekly ops metrics consolidation" record. Aligns with roadmap item "Self-service reporting".
2. **Access request process** — onboarding to a data feed takes two weeks of emails. Planted near-dup: "Vendor feed access workflow". Aligns with "Workflow automation".
3. **Customer-facing chatbot ask** — a group wants an assistant for internal policy questions. Planted near-dup: "Policy Q&A assistant pilot". Aligns with "Knowledge assistants"; near-miss with "Document ingestion".
4. **Vague ask (intentionally)** — "We need AI for our process." Designed to trigger multiple rejections and show the agent extracting a real problem statement. Weak duplicate matches; classification below threshold → shows the "recorded, not applied" path.
5. **Blank** — no brief; user brings their own situation.

### 6.3 Additional ideas to show utility (recommended; flag-controlled)
- **Guided tour** on first visit: four callouts, one per stage, dismissable; never shown again for that browser (`localStorage`).
- **Before/after panel** in the summary: the user's first attempt vs. the accepted answer for the two most-revised questions, side by side. This is the most persuasive single artifact for a skeptic.
- **"Peek at the YAML"**: a read-only viewer for the generic card and demo roadmap so technically-minded adopters see that onboarding is configuration, not code.
- **"What onboarding would take"** card on the summary: a short checklist (questions and guidelines, Jira mapping, roadmap in canonical YAML, repository connections) with an estimate derived from the counts in their session (e.g., "8 questions → typically 1–2 working sessions with the platform team"). Wording configurable; no commitments.
- **Shareable summary link**: a read-only URL for the summary, expiring with the session (24 h), so the adopter can show a colleague without re-running.
- **Conversational-mode toggle** (if available from current UX work): lets the user compare the form-like and the more conversational interaction on the same card; useful for addressing the "feels like a form" feedback directly.
- **Latency indicator** per LLM turn in the stage summary panel, with a note on which steps are deterministic. Sets honest expectations and shows the engineering care around turn reduction.
- **Multi-intake comparison** (later): run two scenarios and show how the same roadmap classifies them differently.

## 7. Backend requirements

- **BR-1** Settings: `GENERIC_INTAKE_ENABLED: bool = False`; when false, the `/try` route and `/api/demo/*` router are not mounted.
- **BR-2** Router `/api/demo`:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/sessions` | create session; body `{tester_name?, team?, scenario_id}` → `{demo_session_id}` |
| `GET` | `/sessions/{id}` | current state (stage, progress, summary so far) |
| `POST` | `/sessions/{id}/intake/turn` | user message → existing MVP0 engine (thin adapter; no logic duplication) |
| `POST` | `/sessions/{id}/duplicates/run` | run detection; optional `custom_records[]` |
| `POST` | `/sessions/{id}/duplicates/decision` | `{decision: "stop" | "continue"}` |
| `POST` | `/sessions/{id}/classify/run` | run classification; optional `custom_roadmap_text` |
| `POST` | `/sessions/{id}/roadmap/transform` | roadmap text → canonical YAML (preview before classify) |
| `GET` | `/sessions/{id}/summary` | summary payload incl. mock Jira issue and metrics |
| `POST` | `/sessions/{id}/finish` | mark completed |
| `GET` | `/sessions/{id}/export?format=md|pdf|yaml|json` | exports (§5.6) |
| `GET` | `/scenarios` | scenario list |
| `GET` | `/admin/sessions` | admin: list sessions and funnel metrics (admin token, as in the UAT feedback spec) |

- **BR-3** Sinks are pluggable: the production flow ends with a `JiraSubmissionSink`; the demo flow ends with a `SummarySink` that builds the mock issue via the same field-mapping code. The pipeline orchestrator selects the sink by session type; no other stage knows it is in demo mode.
- **BR-4** The demo corpus is embedded once at startup (or at build time, cached to disk keyed by model version) so Stage 2 latency is only the user's own record plus any pasted custom records.
- **BR-5** Rate limits per client IP: 20 session creations/hour, 60 turns/minute. Custom records capped at 200; custom roadmap text capped at 50 KB.
- **BR-6** Session storage: `demo_sessions` table (`id`, `created_at`, `expires_at`, `tester_name`, `team`, `scenario_id`, `stage`, `status`, `state_json`, `completed_at`). `state_json` holds answers, verdicts, candidates, classification output, and user-pasted data. A nightly job deletes expired sessions.
- **BR-7** Event log for funnel analysis: `demo_events` (`session_id`, `event`, `ts`, `data_json`) for `session_created`, `question_accepted`, `question_rejected`, `duplicates_shown`, `duplicate_stop`, `duplicate_continue`, `custom_records_used`, `custom_roadmap_used`, `classification_shown`, `threshold_slider_used`, `summary_viewed`, `export_downloaded`, `finished`, `abandoned` (set by the expiry job if never finished).
- **BR-8** Demo conversations are logged through the same conversation logger as production, tagged `source=demo`, so the Intake Learning Loop can include or exclude them explicitly (default: excluded from friction metrics; included for eval-case candidates only when flagged by a reviewer).

## 8. Frontend requirements

- **FE-1** Route `/try` rendered only when `VITE_GENERIC_INTAKE === "true"`; lazy-loaded so it is absent from builds where the flag is unset.
- **FE-2** Reuse the production intake chat component and question list; the stage summary panel and the demo-only controls (scenario picker, threshold slider, custom list/roadmap inputs, export buttons) live in a `src/demo/` package and are composed around the production components, not forked from them.
- **FE-3** A persistent **stage indicator** (Intake quality → Duplicates → Classification → Summary) across the top, showing the current stage and allowing back-navigation to review (not edit) completed stages.
- **FE-4** Responsive: stage summary panel becomes a bottom sheet under 768 px; the mock issue preview scrolls horizontally rather than truncating field names.
- **FE-5** Accessibility: all demo-only controls keyboard-operable; slider has an accessible label and announces the current threshold.
- **FE-6** Latency handling: each stage run shows a progress state with the step currently executing (embedding, searching, classifying) rather than a blank spinner.

## 9. Security and privacy

- **SP-1** No Jira credentials are requested or accepted anywhere in the demo flow; the Jira credential prompt from the production submission step is not rendered.
- **SP-2** User-pasted lists and roadmaps are session-scoped, stored in `state_json`, never merged into the demo corpus fixture, and deleted on expiry.
- **SP-3** The demo corpus and roadmap contain no real projects, people, or systems; a review checklist for fixture authors is included in the README.
- **SP-4** Admin funnel endpoints require the admin token; they expose tester name/team and events, not answer text.
- **SP-5** Exports are generated per request and not stored.
- **SP-6** Same network placement and rate limiting as the UAT app; the feature flag is off outside UAT/demo environments.

## 10. Configuration

| Tier | Variable | Purpose | Default |
|---|---|---|---|
| Frontend | `VITE_GENERIC_INTAKE` | mount `/try` | unset |
| Backend | `GENERIC_INTAKE_ENABLED` | mount `/api/demo` | `false` |
| Backend | `GENERIC_INTAKE_SESSION_TTL_HOURS` | session expiry | `24` |
| Backend | `GENERIC_INTAKE_MAX_ATTEMPTS` | per-question attempts for the demo card | `3` |
| Backend | `GENERIC_INTAKE_ONBOARDING_LINK` | target of "Request onboarding" | required when enabled |
| Backend | `GENERIC_INTAKE_CORPUS_PATH` / `GENERIC_INTAKE_ROADMAP_PATH` | fixture locations | repo defaults |
| Backend | `GENERIC_INTAKE_ADMIN_TOKEN` | admin funnel endpoints | required when enabled |

## 11. Acceptance criteria

- [ ] AC-1 With both flags on, `/try` loads, the scenario picker shows 5 scenarios, and a session is created on "Start".
- [ ] AC-2 Following scenario 4 (vague ask) and giving one-line answers produces at least two rejections with explanations before any question is accepted.
- [ ] AC-3 Following scenario 1 produces a duplicate candidate with similarity ≥ threshold referencing the planted record, and at least one candidate below it.
- [ ] AC-4 Choosing Stop at Stage 2 goes to the summary; the summary states the stop and names the candidate; Stages 3 metrics are shown as "not run".
- [ ] AC-5 Pasting a custom list of 20 records that includes a near-copy of the user's request surfaces that record as the top candidate.
- [ ] AC-6 Scenario 1 classification applies "Self-service reporting" above threshold and lists at least one below-threshold candidate with rationale; dragging the slider below that candidate's confidence moves it to "applied" without any server call to production config.
- [ ] AC-7 Pasting a bullet-list roadmap produces canonical YAML for confirmation; classification reruns against it and the results reference the pasted item names.
- [ ] AC-8 The mock issue preview shows a field populated from two questions mapped to the same Jira field, aggregated.
- [ ] AC-9 No request to any Jira host is made during a full session (verified by network capture in test).
- [ ] AC-10 Markdown, PDF, starter YAML, and JSON exports download and the starter YAML validates against the intake card schema.
- [ ] AC-11 Finish marks the session completed; the admin funnel endpoint shows the session with its events.
- [ ] AC-12 With `VITE_GENERIC_INTAKE` unset, the production bundle contains no `/try` route or `src/demo/` code; with `GENERIC_INTAKE_ENABLED=false`, `/api/demo/*` returns 404 and is absent from `/docs`.
- [ ] AC-13 Expired sessions and their pasted data are deleted by the cleanup job.

## 12. Deliverables
1. `cards/generic-work-request.yaml` and five scenario definitions.
2. `fixtures/demo_corpus.json` (with generator script and authoring checklist) and `fixtures/demo_roadmap.yaml`.
3. `SummarySink` and sink selection in the orchestrator.
4. `/api/demo` router, session and event tables with migrations, cleanup job, exports (md/pdf/yaml/json).
5. `src/demo/` frontend package: landing/scenario picker, stage indicator, stage summary panel, duplicate and classification demo controls, summary screen, exports, guided tour.
6. Tests: scenario-driven end-to-end tests for AC-2 through AC-9; unit tests for sink selection and export validity.
7. `README-generic-intake.md`: enabling the feature, authoring scenarios and fixtures, reading funnel metrics.

## 13. Open questions for the implementer
1. Does the pipeline orchestrator already have a sink abstraction at the Jira submission step, or does submission need to be refactored behind an interface first?
2. Can the roadmap-to-canonical-YAML transformation be invoked as a library function with user-supplied text, or does it currently assume a file in the repo?
3. Which Gemini model should back the demo (latency vs quality trade-off); should the demo pin a model to keep behavior stable for scenarios?
4. Is there an existing PDF rendering path in the backend, or should Markdown → PDF be added (e.g., via a headless renderer already approved in the environment)?
5. Where should "Request onboarding" point (mailto, Confluence form, internal ticketing)?
