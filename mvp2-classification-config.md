# MVP2 - Classification Configuration

**Agentic Intake Platform | Configuration Reference**
Version 0.1 | Draft

> Companion to `mvp2-classification-spec.md`. That document states requirements; this one
> defines the YAML file format the configuration takes.
>
> Where this document specifies a field, it is because a requirement calls for the
> information. Where the implementation needs additional internal configuration - scoring
> internals, prompt content, model parameters - those belong in the implementation's own
> section and are marked as reserved below.

---

## 1. Files

| File | Contains | Owner | Cadence |
|---|---|---|---|
| `roadmaps/<team>.yaml` | One team's canonical roadmap | Team roadmap owner | Annual |
| `classification_policy.yaml` | Thresholds, Jira mapping, runtime settings | Platform team | As tuned |

The YAML itself is delivered as separate files, not embedded in this document:

| File | Purpose |
|---|---|
| `roadmap-cards-platform-fy26.yaml` | Fully populated roadmap example |
| `roadmap-wealth-ops-fy26.yaml` | Minimal valid roadmap - sparse source degradation |
| `classification_policy.yaml` | Platform policy with per-roadmap overrides |

This document is the field reference for those files.

Two files, not one. REQ-501 requires the roadmap to be held separately from the MVP0
intake YAML; the policy file is separated from the roadmap for the same reason - it has a
different owner and a different change cadence.

One roadmap file per team (REQ-409). One policy file for the platform, with per-roadmap
overrides.

---

## 2. Canonical roadmap YAML

### 2.1 Example

See `roadmap-cards-platform-fy26.yaml` for a fully populated roadmap and
`roadmap-wealth-ops-fy26.yaml` for the minimal valid case. Both carry inline requirement
references.

### 2.2 Field reference

| Field | Required | Requirement | Notes |
|---|---|---|---|
| `roadmap.id` | Yes | - | Stable across versions |
| `roadmap.team` | Yes | REQ-409 | Must match the intake's owning team |
| `roadmap.version` | Yes | REQ-502 | Recorded on the Jira issue |
| `roadmap.effective_to` | Yes | REQ-505 | Expired roadmaps fail closed |
| `roadmap.source` | No | REQ-1002 | Provenance only; format is free text |
| `categories[].id` | Yes | REQ-1003 | Unique within the roadmap |
| `categories[].tag` | Yes | REQ-504, REQ-803 | Value written to Jira |
| `categories[].name` | Yes | REQ-1003 | Human-readable |
| `categories[].status` | Yes | - | Only `active` categories are evaluated |
| `categories[].intent` | Yes | REQ-1003 | See 2.3 |
| `categories[].in_scope` | Yes | REQ-1003 | Scope indicator |
| `categories[].out_of_scope` | Yes | REQ-1003 | Scope indicator; see 2.4 |
| `categories[].aliases` | No | - | Alternative names |
| `categories[].initiatives` | No | REQ-608 | Enables initiative-level attribution |
| `categories[].metadata` | No | REQ-1004, REQ-1009 | Never a classification signal |

### 2.3 On `intent`

`intent` must state what the category is trying to achieve, not what subject it covers.

```yaml
# Insufficient - describes a subject area, not an outcome
intent: "Our foundational data and decisioning platform."

# Sufficient - states an outcome that an intake can be judged against
intent: >
  Deliver a unified decisioning platform that replaces per-LOB point
  solutions, so new decisioning use cases ship without bespoke
  integration work.
```

Source roadmap descriptions are usually written in the first form. Converting them to the
second is part of transformation and requires roadmap owner confirmation (REQ-1007) -
only the owner knows which outcome the team committed to.

### 2.4 On `out_of_scope`

Required, and rarely present in source roadmaps. It exists because categories drawn from
a strategy document are broad, and breadth attracts topically adjacent intakes that do not
advance the stated intent.

Entries must be specific. "Things unrelated to this" provides no signal.

### 2.5 `metadata` is never a classification signal

REQ-1004 requires source content that does not map to a canonical element to be either
discarded or retained as non-classifying metadata. `metadata` is that container. REQ-1009
specifically excludes shared technology from being treated as evidence of alignment -
several categories may legitimately share the same stack.

---

## 3. Classification policy YAML

See `classification_policy.yaml`. It holds thresholds (REQ-701 to REQ-706), per-roadmap
overrides (REQ-704), the Jira field mapping required by Section 8 of the spec, runtime
settings, and model access.

The `engine` block is intentionally empty. Scoring internals, prompt configuration, and
sampling behaviour are not prescribed by the requirements spec and belong to the
implementation design.

### 3.1 Values that do not exist yet

`<FILL IN>` marks values that cannot be supplied until open items in spec Section 13 are
resolved. Configuration loading must fail clearly when they are unset rather than
defaulting (REQ-1103).

| Value | Blocked on |
|---|---|
| `jira.*` fields | Custom field provisioning, and confirmation that non-admin intake users can write to them |
| `runtime.latency_budget_ms` | Spec Section 13, item 9 |
| `runtime.on_failure` | REQ-1104 - behaviour not yet defined |
| `model.*` | Endpoint and model selection |

---

## 4. Validation rules

Applied at configuration load. All failures are loud (REQ-506, REQ-1103).

**Reject:**
- A roadmap past `effective_to`
- A category missing `id`, `tag`, `name`, `intent`, `in_scope`, or `out_of_scope`
- A category whose `intent` describes a subject area without stating an outcome, where
  detectable
- Duplicate `id` or `tag` values within a roadmap
- A `tag_threshold` at or below its `note_threshold`
- Any `<FILL IN>` value remaining in an active policy file

**Warn:**
- A category with empty or generic `out_of_scope`
- A category with no `initiatives`
- Two categories whose `intent` statements are near-identical in meaning

Warnings surface during roadmap onboarding review (REQ-1007), not at request time.

---

## 5. Minimal valid roadmap

See `roadmap-wealth-ops-fy26.yaml`. It is the smallest configuration satisfying the
required fields, included to show what a sparse source roadmap degrades to - not as a
target.

A category thinner than that - a name with nothing stating an outcome or bounding the
scope - is not classifiable and is rejected under REQ-1006.
