# Agentic Intake Platform — Problem Statement & Value Proposition

---

## The Problem

Work enters the portfolio without a governance layer.

Submissions arrive at reviewers **incomplete**, with **no check for duplication**, **no alignment to strategic priorities**, and **no connection to the tools that will build them**. The costs are real — clarification cycles, redundant builds, misaligned approvals, stories created without the context that drove them — but none of it appears in any report. It is absorbed locally, silently, at every level of the review chain.

**The intake process is where portfolio quality is either established or lost. Right now, it is being lost.**

---

## What the Platform Delivers

A governance layer that enforces four things before any work enters the portfolio:

| Layer | What It Does |
|-------|-------------|
| **Quality** | Conversational intake with real-time validation. Every submission is complete and specific before it reaches a reviewer. Quality criteria are defined per-intake, per-question, by the intake owner. |
| **Duplication Detection** | Three-layer search (exact / fuzzy / semantic) across the full Jira portfolio before any ticket is created. Submitter is blocked until candidates are acknowledged — collaborate, reuse, or proceed with justification. |
| **Classification** | Every submission is classified by work type, OKR alignment, portfolio position, and complexity tier. Reviewers receive context pre-assembled. Routing is automatic. |
| **Agile Artifact Generation** | Approval triggers generation of compliant Epics, features, and stories in StoryWeaver — populated with the full context of the validated intake. The intake owner's knowledge is captured at submission and delivered at story creation, even when they are no longer in the room. |

---

## How We Are Different

### vs. The Existing AI Intake Agent

| | Existing Agent | This Platform |
|--|---------------|---------------|
| **Workflow** | Fixed | Configurable per intake type |
| **Experience** | Single | Shared across intake owners |
| **Problem scope** | Intake only | Intake + governance chain |
| **Duplication detection** | None | Three-layer (exact / fuzzy / semantic) |
| **Classification** | None | Work type, OKR, portfolio position, complexity |
| **Artifact generation** | None | Full StoryWeaver integration with intake context |

We are **problem-agnostic and workflow-configurable**. Any intake type. Any owner. One governance layer.

---

### vs. The Discovery Agent

The Discovery Agent is an **onboarding tool** — it surfaces what assets exist in the portfolio. It was designed to answer *"what do we have?"*

This platform's duplication detection answers a different question: *"has this already been built, or is it being built right now?"*

- Searches across **active, in-progress, and recently completed work** — not just onboarded assets
- Fires **at submission time** — before any ticket is created, before any resource is committed
- **Blocks submission** until the submitter acknowledges candidates and makes a conscious decision
- Captures the decision and rationale in the audit log

Asset reuse is the outcome. Governance at the point of submission is the mechanism.

---

### vs. StoryWeaver

StoryWeaver **creates and scores artifacts** — it ensures Epics, features, and stories have the right fields, the right structure, and a passing story score.

This platform **provides the context** those artifacts are built from.

The gap StoryWeaver cannot close: **the intake owner who drove the submission is not present when the stories are created.** Their knowledge of the business problem, the scope, the constraints, the OKR rationale — all of it exists at submission time and is lost by story creation time.

| | StoryWeaver | This Platform |
|--|------------|---------------|
| **Artifact structure** | ✓ Enforced | ✓ Enforced |
| **Story scoring** | ✓ Yes | — |
| **Business context from intake** | ✗ Not available | ✓ Carried forward from validated submission |
| **Duplication status** | ✗ Not available | ✓ Resolved before ticket creation |
| **OKR and classification tags** | ✗ Not available | ✓ Auto-applied from classification layer |
| **Quality floor at intake** | ✗ Not enforced | ✓ Enforced before submission is accepted |

StoryWeaver makes sure the story is **well-formed**. This platform makes sure the story is **worth building and built with full context**.

They are complementary. We integrate with StoryWeaver — we are not replacing it.

---

## The Bottom Line

> Every existing tool addresses one piece of the problem. The quality agent handles intake. The discovery agent handles onboarding. StoryWeaver handles artifact structure. **No existing tool connects them into a governance chain.**
>
> This platform is that chain — from the first question of the intake conversation to a compliant, context-rich artifact in StoryWeaver, with duplication resolved and OKRs tagged along the way.

---
*Agentic Intake Platform — Internal*
