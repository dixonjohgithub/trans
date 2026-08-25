# MVP2 - Roadmap Classification Agent

**Agentic Intake Platform | Requirements Specification**
Version 0.2 | Draft

> This document states **requirements only**. It deliberately does not prescribe an
> implementation approach, algorithm, prompt design, scoring formula, module structure,
> or library choice. Those decisions belong to the implementation phase.
>
> Where a requirement constrains the solution space, the constraint is stated as an
> outcome that must hold, not as a method for achieving it.

---

## 1. Purpose and scope

MVP2 determines whether an incoming intake aligns to any of the owning team's approved
roadmap categories, records that determination on a Jira issue, and creates that issue.

The business goal is prioritisation triage: a team lead should be able to open their
board and see which incoming demand aligns to approved strategy and which does not.

Aligned intakes receive a roadmap tag. Intakes that align to nothing receive no tag.
Absence of a tag is a meaningful result meaning "not aligned to the roadmap", not a
failure or an error state.

---

## 2. Terminology

| Term | Meaning |
|---|---|
| **Roadmap** | A team's approved strategy document. One per team. |
| **Category** | A top-level division of the roadmap (e.g. "Core Solution"). The category is the classification class and the tag target. |
| **Initiative** | A concrete work item listed under a category. |
| **Intake** | A single submitted request, produced by MVP0 and MVP1. |
| **Intake owner** | The person accountable for the resulting Jira issue, who may correct it after creation. |
| **Intake user** | The person submitting the intake. |

"Class" and "category" are used interchangeably and refer to the same thing.

Source roadmaps vary in structure between teams. No single source layout can be
assumed. What is fixed is the **canonical form** every roadmap is transformed into
before classification:

```
Roadmap (one per team, canonical form)
  |
  +-- Category  <- the classification class and tag target
        |
        +-- (content sufficient to define the class - see Section 10)
```

Any source roadmap format is acceptable provided it can be transformed into this
canonical form.

---

## 3. Phase context

| Phase | Scope | User-facing |
|---|---|---|
| MVP0 | Intake quality - guided Q&A, guidelines, Jira field mappings | Yes |
| MVP1 | Duplicate detection against enterprise repositories | Yes |
| **MVP2** | **Roadmap classification and Jira issue creation** | **No** |
| MVP3 | Agile artifact creation | Not yet defined |

Flow: the intake user completes MVP0, reviews MVP1 duplicate candidates, and chooses to
stop or continue. If they continue, MVP2 runs and the Jira issue is created. The intake
user interacts with MVP0 and MVP1 only.

---

## 4. Input requirements

MVP2 consumes the persisted results of the two preceding agents. Both are held in agent
state and are read by MVP2; MVP2 does not re-derive either.

### 4.1 Agent state: intake quality (MVP0)

```
=============================================================
PLACEHOLDER - MVP0 AGENT STATE STRUCTURE

To be supplied. This block will define the intake quality
agent state that MVP2 reads.

Known to be present, structure TBD:
  - the questions asked and the user's responses
  - the Jira field mapping for each response, as defined in
    the MVP0 intake YAML
  - the category grouping each question belonged to
    (see REQ-403 - not used for classification)
  - intake quality outcome / score
=============================================================
```

**REQ-401** MVP2 shall read the MVP0 result from agent state. It shall not re-run intake
quality logic or re-prompt the user.

**REQ-402** MVP2 shall carry the Jira field mapping defined in the MVP0 intake YAML
through to issue creation. MVP2 does not define its own mapping for intake responses.

**REQ-403** MVP0 categories are generic, optional groupings that exist so the intake user
can track progress through the questions. They have no semantic relationship to roadmap
categories. MVP2 shall not use MVP0 categories as a classification signal.

**REQ-404** MVP2 shall handle an MVP0 result where optional elements are absent, without
failing.

### 4.2 Agent state: duplicate detection (MVP1)

```
=============================================================
PLACEHOLDER - MVP1 AGENT STATE STRUCTURE

To be supplied. This block will define the duplicate detection
agent state that MVP2 reads.

Known to be present, structure TBD:
  - candidate duplicates identified
  - a confidence score per candidate duplicate
  - the source repository for each candidate
  - the user's decision to continue past duplicate review
=============================================================
```

**REQ-405** MVP2 shall read the MVP1 result from agent state. It shall not re-run
duplicate detection.

**REQ-406** MVP2 shall carry candidate duplicates and their confidence scores through to
the created Jira issue.

**REQ-407** MVP2 shall only execute for intakes where the user chose to continue past
duplicate review. An intake halted at MVP1 does not reach MVP2.

### 4.3 Roadmap input

**REQ-408** MVP2 shall load the roadmap belonging to the intake's owning team.

**REQ-409** Each team owns exactly one roadmap and one intake definition. Roadmaps are
never shared across teams. MVP2 shall never evaluate an intake against a roadmap
belonging to another team.

---

## 5. Roadmap configuration requirements

**REQ-501** The roadmap shall be held in a canonical, machine-readable configuration
separate from the MVP0 intake YAML.

Rationale: the two have different owners (intake governance vs. the team roadmap owner),
different approval gates, and different change cadences. A roadmap change must not force
re-validation of the intake question set, and a malformed roadmap must not be able to
break intake form rendering.

**REQ-502** The roadmap configuration shall be versioned, and the version in force at
classification time shall be recorded on the resulting Jira issue.

**REQ-503** Roadmaps are formally approved and change at most annually. The system shall
not assume mid-cycle roadmap changes.

**REQ-504** Each roadmap category shall carry an identifier and a Jira tag value.

**REQ-505** The system shall reject or refuse to classify against a roadmap that is
expired, malformed, or missing required content, rather than degrading silently.

---

## 6. Classification requirements

**REQ-601** MVP2 shall evaluate each intake against every category in the team's roadmap.

**REQ-602** The result shall permit an intake to align to more than one category, to
exactly one category, or to none.

**REQ-603** "Aligned to no category" shall be a first-class, explicitly recorded outcome.
The system shall not be constructed such that it must select a best-matching category.

**REQ-604** MVP2 shall produce a confidence score for each category it considers.

**REQ-605** Each category's confidence score shall be independent of the other categories
present in the roadmap. Adding or removing an unrelated category shall not change another
category's score.

Rationale: thresholds are applied to absolute scores. A score meaning "best of the
available options" cannot be thresholded consistently.

**REQ-606** MVP2 shall record, for each category considered, the reasoning and the
supporting evidence behind its score, in a form a governance reviewer can read.

**REQ-607** Evidence shall be traceable to what the intake user actually wrote, not only
to a system-generated restatement.

**REQ-608** Where a category's initiatives are known and the alignment is attributable to
a specific initiative, MVP2 shall record which initiative.

---

## 7. Threshold and tagging requirements

**REQ-701** A configurable confidence threshold shall determine which categories are
tagged. Only categories scoring at or above the threshold shall be tagged on the Jira
issue.

**REQ-702** Categories scoring below the tagging threshold but above a configurable lower
bound shall be recorded in the notes of the Jira issue, without being tagged.

**REQ-703** Categories scoring below the lower bound shall not be surfaced.

**REQ-704** Thresholds shall be configurable per roadmap, not fixed globally.

Rationale: roadmaps differ in how precisely their categories are written. The same raw
score does not mean the same thing across two teams' roadmaps.

**REQ-705** The thresholds in force at classification time shall be recorded with the
result.

**REQ-706** The number of tags applied to a single issue shall be configurably capped.

---

## 8. Jira output requirements

**REQ-801** MVP2 shall create the Jira issue. Issue creation is part of MVP2, not a
preceding phase.

**REQ-802** MVP0 responses shall be written to the Jira fields specified by the MVP0
intake YAML field mapping.

**REQ-803** Above-threshold roadmap categories shall be recorded on the issue as tags in
a form that supports reliable querying for prioritisation reporting.

**REQ-804** Below-threshold categories shall be recorded in the issue notes, together
with their confidence scores and the reasoning behind them.

**REQ-805** The notes content shall be identifiable as machine-generated and attributable
to a specific classification run.

**REQ-806** MVP1 candidate duplicates and their confidence scores shall be recorded on
the issue.

**REQ-807** The roadmap version in force shall be recorded on the issue.

**REQ-808** It shall be possible to distinguish a tag set by MVP2 from a tag subsequently
set or changed by a human.

**REQ-809** Issue creation shall not leave a partially populated issue. If the intended
content cannot be fully written, the failure shall be explicit and recoverable rather
than silently partial.

---

## 9. Execution model requirements

**REQ-901** MVP2 shall run without human interaction. There is no review, approval, or
confirmation step between MVP1 and issue creation.

**REQ-902** Corrections are made after the fact, in Jira, by the intake owner. The system
shall not block on, or wait for, such corrections.

**REQ-903** Jira writes shall use the intake user's own Jira credentials, supplied by the
user at intake time. Only authorised users may submit to a given Jira board.

**REQ-904** Because the credential is scoped to the user's intake session, classification
and issue creation shall complete within that session. The system shall not defer Jira
writes to a point after the session ends.

**REQ-905** The intake user's credential shall never be logged, persisted beyond the
session, or included in any stored result or diagnostic output.

**REQ-906** MVP2 shall record a durable result for every run, sufficient to explain after
the fact why each category was or was not tagged.

**REQ-907** The durable result shall be structured for downstream consumption by MVP3.

---

## 10. Roadmap transformation requirements

Source roadmaps are authored as product documents. They vary in structure, section
naming, level of detail, and file format between teams. They must be converted into the
canonical configuration defined in Section 5 before classification.

**REQ-1001** The system shall support transforming a source product roadmap into the
canonical roadmap configuration.

**REQ-1002** The transformation shall be source-agnostic. It shall not assume a fixed set
of source sections, a fixed section naming convention, or a fixed document structure. Any
roadmap format is acceptable provided it can be transformed into the canonical form.

**REQ-1003** The canonical form is the fixed contract, not the source. For each category,
the transformation shall produce at minimum:

| Canonical element | Purpose |
|---|---|
| Identifier | Stable reference for the category |
| Tag value | What is written to Jira when the category is matched |
| Name | Human-readable category name |
| Statement of intent | What the category is trying to achieve |
| Scope indicators | What falls inside the category, and what does not |

How each element is derived from a given source roadmap is a per-roadmap mapping
concern, not a fixed rule.

**REQ-1004** Source content that does not map to a canonical element shall be either
discarded deliberately or retained as non-classifying metadata. It shall not be silently
folded into classifying content.

**REQ-1005** The transformation shall record, per category, which canonical elements
could not be derived from the source.

**REQ-1006** The transformation shall not silently produce a category definition too
sparse to classify against. Such categories shall be rejected or flagged for human
attention.

**REQ-1007** Classification quality depends on how the roadmap is written and how it was
transformed. The system shall provide a means for the roadmap owner to review and correct
the transformed configuration before it is used.

**REQ-1008** Since roadmaps change at most annually, review of the transformed
configuration shall be attachable to the existing annual roadmap approval process.

**REQ-1009** Technology or tooling shared between categories shall not by itself be
treated as evidence of alignment.

**REQ-1010** The transformation output shall be human-readable and editable.

### 10.1 Example source structure

The following is **one observed roadmap layout**, provided as illustration only. It is
not a required or expected structure, and the transformation shall not be built around
it.

| Section | Content |
|---|---|
| Category title | Name of the category, e.g. "Core Solution" |
| Description | Prose description of the category |
| Key Capabilities | List of key items for the category |
| Tech Stack | Technologies used within the category |
| Initiatives | Current initiatives aligned to the category |

Other roadmaps use different sections, different names for equivalent content, or a
different organising principle entirely. Not every roadmap has all of the sections above.

---

## 11. Non-functional requirements

**REQ-1101** Every classification decision shall be auditable: which roadmap version,
which thresholds, which scores, which reasoning, and what was written to Jira.

**REQ-1102** Intake content shall not be written to unstructured logs.

**REQ-1103** All configuration shall be validated when loaded. A malformed configuration
shall fail loudly at load time, not partway through a classification.

**REQ-1104** Failure of the classification step shall be handled explicitly. The system
shall define and implement its behaviour when classification cannot complete.

**REQ-1105** The system shall operate within a corporate proxy environment. All
dependencies must be obtainable through the approved internal mirror.

**REQ-1106** The system shall expose operational metrics sufficient to detect
classification drift, including at minimum the rate at which intakes are tagged, the rate
at which humans subsequently correct tags, and the rate at which intakes align to no
category.

**REQ-1107** Intakes aligning to no category shall be retrievable as a set, per team, for
reporting.

---

## 12. Out of scope

The following are explicitly excluded from MVP2:

1. **Re-classification after a roadmap change.** Tags reflect the roadmap version in
   force at submission time, permanently.
2. **Any human review step within the MVP2 flow.**
3. **Modification of MVP0 or MVP1 behaviour.**
4. **MVP3 agile artifact creation.**
5. **Parsing of source roadmap documents in their original file format** (see Section 13,
   item 4).
6. **Correcting or improving intake quality.** MVP2 consumes the MVP0 result as given.

---

## 13. Open items

1. **MVP0 agent state structure** - to be supplied (Section 4.1 placeholder).
2. **MVP1 agent state structure** - to be supplied (Section 4.2 placeholder).
3. **Jira custom field identifiers** - the fields required by Section 8 must be
   provisioned, and it must be confirmed that a non-admin intake user has write access to
   them.
4. **Source roadmap document formats in use** - Confluence, PowerPoint, Excel, or other.
   Formats and structures vary by team. This determines how much of Section 10 is
   automated versus assisted, and whether a per-roadmap mapping definition is needed
   alongside the roadmap itself.
5. **Threshold calibration method** - how initial threshold values are established for a
   new team, and how they are revised, is not yet defined.
6. **Capturing human corrections** - REQ-808 makes agent and human tags distinguishable.
   Whether and how subsequent human corrections are read back and used is not yet
   defined.
7. **Onboarding posture for a new team** - whether a team should initially run without
   writing tags is not yet decided.
8. **MVP2 to MVP3 contract** - the structure required by REQ-907 cannot be finalised
   until MVP3 scope is defined.
9. **Latency budget** - the acceptable in-session duration for REQ-904 is not yet
   established.
