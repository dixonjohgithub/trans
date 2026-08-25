# Devin Task: MVP2 Roadmap Classification Agent

## Repository

```
Repo:   <FILL IN>
Branch: <FILL IN base branch>
```

Existing code for MVP0 (intake quality) and MVP1 (duplicate detection) lives in this
repo. Read them before designing - MVP2 consumes their output and should be consistent
with their conventions, not a foreign body beside them.

---

## Context

`mvp2-classification-spec.md` is attached. It is a **requirements specification**, not a
design. It deliberately does not tell you how to build this: no algorithm, no scoring
method, no prompt design, no module structure, no library choices. Those are yours.

Read it completely before producing anything.

Where this prompt and the spec disagree, the spec wins. Tell me about the conflict rather
than resolving it silently.

Background: this is a four-phase agentic intake platform in a regulated bank. MVP0 and
MVP1 are built. MVP2 classifies an intake against its team's approved roadmap and creates
the Jira issue. MVP3 is not yet defined.

---

## Your task, in two stages

### Stage 1 - Design proposal. Do this first. Do not write implementation code.

Produce `DESIGN.md` containing:

1. **Your proposed approach to classification.** How you intend to satisfy Sections 6 and
   7 of the spec. Explain the mechanism, and explain specifically how it satisfies
   REQ-603 (aligning to nothing is a first-class outcome) and REQ-605 (a category's
   confidence score is independent of which other categories exist in the roadmap). These
   two constrain the solution space more than anything else in the document - if your
   approach cannot satisfy both, it is the wrong approach.

2. **Your proposed canonical roadmap configuration schema**, satisfying Section 5 and
   REQ-1003. Show a worked example.

3. **Your proposed component breakdown**, with the responsibility of each and the
   boundaries between them.

4. **Your proposed approach to roadmap transformation** (Section 10), including how you
   intend to keep it source-agnostic per REQ-1002.

5. **Requirements traceability matrix.** Every REQ number in the spec, mapped to where in
   your design it is satisfied. Any requirement you cannot satisfy, or believe is
   ambiguous, is listed explicitly with your question.

6. **Your open questions**, at minimum covering the Blockers section below.

7. **Anything in the spec you think is wrong.** You will have read it more carefully than
   most reviewers. If a requirement is unachievable, internally inconsistent, or would
   produce a bad outcome, say so now rather than implementing it faithfully and letting
   me discover it later.

**Stop after Stage 1 and wait for my response.** Do not begin implementation.

### Stage 2 - Implementation. Only after I approve the design.

Build what we agreed, with tests. Details below.

---

## Blockers - these values do not exist yet

Do not invent, infer, or place a plausible-looking placeholder value for any of these.
Ask.

1. **MVP0 agent state structure.** Section 4.1 of the spec is a placeholder. You cannot
   finalise the input contract without it. Propose what you need from it.
2. **MVP1 agent state structure.** Section 4.2 is a placeholder. Same.
3. **Jira custom field identifiers.** The fields required by Section 8 are not yet
   provisioned. Read them from configuration and fail clearly when unset.
4. **LLM endpoint, model, and auth pattern.** Do not assume a provider or SDK. Define an
   interface; I will supply the concrete adapter.
5. **Source roadmap formats in use.** These vary by team and are not yet catalogued
   (spec Section 13, item 4).
6. **Persistence target** for the durable result required by REQ-906.
7. **Latency budget** for REQ-904.
8. **MVP3 contract** for REQ-907 - MVP3 scope is undefined.

If you hit an ambiguity not on this list, record it in `DECISIONS.md` with your
interpretation and flag it in your summary.

---

## Constraints that are not open to design

These come directly from the requirements. They are not preferences.

**Credential handling (REQ-903, REQ-905).** Jira writes use the intake user's own
credentials, supplied at intake. The credential must never be logged, persisted beyond
the session, written into any stored result, or appear in an exception trace. Treat this
as a security control and test it directly.

**In-session execution (REQ-904).** The credential is session-scoped, so classification
and issue creation complete within the user's session. No deferred writes, no background
completion, no post-session patching.

**Headless (REQ-901).** No human review, approval, or confirmation step anywhere between
MVP1 and issue creation. Do not add one, even as a configurable option.

**Issue integrity (REQ-809).** Issue creation must not leave a partially populated issue.

**Team isolation (REQ-409).** An intake is never evaluated against another team's
roadmap.

**Fail closed (REQ-506, REQ-1103).** Invalid, expired, or malformed configuration fails
loudly at load. It does not degrade into a partial classification.

**No re-classification (Section 12).** Do not build re-run, roadmap-diff, or
tag-reconciliation logic. Out of scope entirely.

**Corporate proxy (REQ-1105).** Every dependency must resolve through our internal
Artifactory mirror. `huggingface.co` is blocked at the network level and there is no
Hugging Face repository in Artifactory - only a PyPI mirror. If your design needs
something unavailable, raise it in Stage 1 rather than discovering it mid-build.

---

## Implementation requirements for Stage 2

**Testability.** Decision logic - scoring, thresholding, tagging decisions - must be
testable without invoking an LLM or Jira. Structure accordingly.

**No network in tests.** Every test runs offline against mocks or fixtures.

**Non-deterministic components are isolated.** Wherever your approach introduces
variability, confine it and make the surrounding logic deterministic given its output.

**Malformed model output is an expected condition, not an exception.** If your design
uses an LLM, it must handle malformed, incomplete, or unparseable responses without
failing the user's intake submission. Define the policy in `DESIGN.md`.

**Structured logging.** One structured record per classification run sufficient to
satisfy REQ-1101. Intake content does not go into unstructured logs (REQ-1102).

**Fixtures.** Build a fixture roadmap and a set of fixture intakes spanning: clear single
match, clear multi-category match, ambiguous near-tie, clear non-alignment, and one that
should be excluded despite topical similarity. These serve as regression tests and as the
basis for later threshold calibration.

**Harness.** A script that runs the fixture intakes against the fixture roadmap and
reports the resulting scores and decisions. It reports; it does not assert.

---

## Deliverables

**Stage 1:** `DESIGN.md` with the seven items above.

**Stage 2:**
1. Implementation, typed, matching the approved design.
2. Tests, passing, offline.
3. Roadmap transformation capability per Section 10.
4. `README.md` - setup, how to run the harness, how to onboard a new team's roadmap.
5. `DECISIONS.md` - every place you interpreted rather than followed the spec, and what
   you chose.
6. Updated traceability matrix reflecting what was actually built.

---

## Definition of done

- Every REQ in the spec is either satisfied and traced, or explicitly listed as not
  satisfied with a reason.
- Tests pass with no network access.
- The intake user's credential provably appears in no log, trace, or stored artifact.
- The harness runs end to end and reports a result matrix.
- No dependency outside the Artifactory mirror.
- `DECISIONS.md` is complete.

---

Begin with Stage 1. Post `DESIGN.md` and your questions. Do not write implementation code
until I have answered them.
