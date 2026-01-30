# Policy Change & Applicability Detector

## System Design Document

**Version:** 1.0  
**Date:** January 2025  
**Purpose:** End-to-end LLM-based solution to determine policy applicability across business units

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Approach](#solution-approach)
4. [Why Context Engineering Over RAG](#why-context-engineering-over-rag)
5. [System Architecture](#system-architecture)
6. [Data Model](#data-model)
7. [Processing Pipeline](#processing-pipeline)
8. [Prompt Engineering](#prompt-engineering)
9. [Code Implementation](#code-implementation)
10. [Expert Review Workflow](#expert-review-workflow)
11. [Continuous Improvement Loop](#continuous-improvement-loop)

---

## Executive Summary

This document describes an LLM-based system that automatically assesses whether policy requirements apply to specific business units, generating detailed rationales for each determination. The system uses a **context engineering approach** rather than Retrieval-Augmented Generation (RAG), leveraging structured prompts with complete document context and optional historical reference data.

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Context Engineering over RAG | Document relationships are known; complete context produces better rationales |
| Requirement-by-requirement processing | Focused reasoning, clear audit trail per decision |
| Human-in-the-loop verification | Every output is expert-reviewed before becoming authoritative |
| Historical data as reference only | BUs change; current description is source of truth |
| Simple SQL lookups over vector search | Sufficient for finding relevant historical examples |

---

## Problem Statement

### Business Context

When organizational policies change, compliance teams must determine:

1. **Which business units are affected** by the policy
2. **Which specific requirements** within the policy apply to each business unit
3. **Why** each requirement is or isn't applicable (documented rationale)

This process is currently manual, time-consuming, and inconsistent.

### Inputs Available

| Input | Description |
|-------|-------------|
| **Policy Document** | Contains policy description, scope, and individual requirements |
| **Procedure Documents** | Detail the procedures for implementing policy requirements |
| **Control Documents** | Specify the controls that procedures address |
| **Business Unit Profiles** | Description of each BU's responsibilities, functions, systems, and data handled |
| **Historical Applicability Data** | Past vetted decisions with yes/no per requirement and rationale (sparse, not guaranteed for all BUs) |

### Trigger

Policy change notification arrives via email containing the Policy ID.

### Desired Output

For each Business Unit:
- List of applicable requirements with evidence-based rationale
- List of non-applicable requirements with justification
- Confidence levels for expert review prioritization

---

## Solution Approach

### Core Philosophy

**The LLM generates first-draft assessments; human experts provide final verification.**

This approach:
- Accelerates the assessment process (LLM does bulk analysis)
- Maintains quality control (expert verification)
- Builds institutional knowledge (verified decisions feed back into historical data)
- Improves over time (more history = better future assessments)

### Processing Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ONE PROMPT TEMPLATE                                  │
│                     (Designed Once)                                      │
│                                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                        │
│  │   System    │ │   Policy    │ │ Requirement │ ← VARIABLE              │
│  │ Instructions│ │   Context   │ │  {current}  │   (changes per          │
│  └─────────────┘ └─────────────┘ └─────────────┘    iteration)           │
│                                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                        │
│  │ Procedures  │ │ Business    │ │ Historical  │ ← VARIABLE              │
│  │ & Controls  │ │ Unit {curr} │ │ (if exists) │   (changes per          │
│  └─────────────┘ └─────────────┘ └─────────────┘    iteration)           │
│                                                                          │
│  ┌─────────────────────────────────────────────┐                        │
│  │           Task & Output Format              │                        │
│  └─────────────────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    EXECUTED ONCE PER (Requirement × BU) PAIR
                    
    Policy with 10 Requirements × 8 Business Units = 80 LLM Calls
    Same template, different variables plugged in each time
```

---

## Why Context Engineering Over RAG

### What is Context Engineering?

**Context Engineering:** Pre-assemble all relevant documents into a single, well-structured prompt. The LLM receives complete context for each assessment.

**RAG (Retrieval-Augmented Generation):** Dynamically retrieve document chunks via semantic search based on a query, then inject retrieved chunks into the prompt.

### Head-to-Head Comparison

| Aspect | Context Engineering | RAG |
|--------|--------------------|----|
| **How context is gathered** | Fetch all linked docs via known relationships | Embed query, search vector DB, retrieve top-k chunks |
| **What you get** | Complete documents in full | Chunks/fragments ranked by similarity |
| **Document relationships** | Preserved perfectly (fetch by ID) | May break (chunks lose relationship context) |
| **Risk of missing context** | Low - explicitly include linked docs | Higher - relevant info might not be retrieved |
| **Citation accuracy** | High - LLM sees full docs | Medium - may cite chunk boundaries awkwardly |
| **Implementation complexity** | Simple - just fetch and format | Complex - chunking, embedding, vector DB, tuning |
| **Debugging** | Easy - see exactly what went in | Hard - "why didn't it retrieve that chunk?" |
| **Reproducibility** | Deterministic prompts | Variable - retrieval can differ |

### Why RAG is Not Needed for This Use Case

#### 1. Document Relationships are Known and Explicit

```
Policy ──(links to)──► Procedures ──(links to)──► Controls
```

We don't need semantic search to find relevant procedures - we know exactly which procedures belong to which policy via explicit IDs.

#### 2. Context is Bounded and Manageable

| Component | Typical Size | Max Reasonable |
|-----------|-------------|----------------|
| Policy description | 500 tokens | 2,000 tokens |
| Single requirement | 200 tokens | 500 tokens |
| Procedures (all) | 3,000 tokens | 15,000 tokens |
| Controls (all) | 2,000 tokens | 10,000 tokens |
| BU profile | 500 tokens | 2,000 tokens |
| Historical context | 500 tokens | 2,000 tokens |
| System + Output format | 800 tokens | 1,500 tokens |
| **TOTAL** | **~8,000 tokens** | **~35,000 tokens** |

Even worst case (35K tokens) is only ~17% of modern LLM context windows (200K+). No need for RAG to manage context limits.

#### 3. Rationale Quality Requires Complete Context

Compliance rationales must be:
- Evidence-based with accurate citations
- Logically coherent
- Traceable to source documents

RAG's chunking can fragment the very sentences needed for citation. Context engineering ensures the LLM sees complete documents.

#### 4. Historical Data is Sparse and Optional

Historical applicability data:
- Doesn't exist for every BU
- Doesn't exist for new policies
- May be outdated (BUs change)

This makes it unsuitable as a primary retrieval target. Instead, we treat historical data as optional reference material found via simple SQL lookups.

#### 5. Human Verification Eliminates Need for Perfect Retrieval

Every LLM output is verified by a human expert. The LLM's job is to produce a *reasonable first draft* - not to be the final authority. This reduces the need for sophisticated retrieval optimization.

#### 6. Simple SQL Queries Suffice for Historical Lookup

We need three types of historical examples:
1. **Exact match:** Same requirement + same BU
2. **Same requirement:** How was this requirement assessed for other BUs?
3. **Same BU:** How were other requirements assessed for this BU?

These are simple database queries - no vector similarity needed.

### When Would RAG Make Sense?

RAG would be beneficial if:

| Scenario | Our Situation |
|----------|---------------|
| Unknown document relationships | ❌ No - explicit links exist |
| Massive document corpus (1000s of docs) | ❌ No - bounded set per policy |
| Need to search across ALL policies | ❌ No - triggered by specific policy |
| Very long documents exceeding context | ❌ No - documents fit comfortably |
| Open-ended, unpredictable questions | ❌ No - structured assessment task |

**Conclusion:** RAG adds infrastructure complexity without meaningful benefit for this use case.

---

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         POLICY CHANGE TRIGGER                            │
│                     (Email with Policy ID)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FETCH CURRENT DOCUMENTS                             │
│                                                                          │
│   Policy ──► Procedures ──► Controls    (via known relationships)       │
│   All Business Units                    (current descriptions)          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              FOR EACH (Requirement × Business Unit)                      │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step 1: Historical Lookup (Simple SQL)                         │   │
│   │                                                                  │   │
│   │  • Query for exact match (requirement + BU)                     │   │
│   │  • Query for same requirement, different BUs                    │   │
│   │  • Query for same BU, different requirements                    │   │
│   │  • Result: 0-5 reference examples (may be empty)                │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step 2: Build Context-Engineered Prompt                        │   │
│   │                                                                  │   │
│   │  ALWAYS INCLUDED (Source of Truth):                             │   │
│   │  • Policy context                                               │   │
│   │  • Current requirement                                          │   │
│   │  • Current BU description ← DECISIONS BASED ON THIS             │   │
│   │  • Procedures & Controls                                        │   │
│   │                                                                  │   │
│   │  INCLUDED IF AVAILABLE (Reference Only):                        │   │
│   │  • Historical decisions + rationales                            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step 3: LLM Assessment                                         │   │
│   │                                                                  │   │
│   │  • Decision based on CURRENT documents                          │   │
│   │  • Rationale cites current BU description                       │   │
│   │  • May differ from historical (that's expected)                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGGREGATE RESULTS                                │
│                                                                          │
│   • Group by Business Unit                                              │
│   • Format for expert review                                            │
│   • Flag low-confidence decisions                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXPERT REVIEW (Human)                                 │
│                                                                          │
│   For each assessment:                                                  │
│   • Review LLM's decision + rationale                                   │
│   • Agree → Approve                                                     │
│   • Disagree → Modify decision and/or rationale                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SAVE TO DATABASE                                   │
│                                                                          │
│   • Store final (expert-verified) decision                              │
│   • Store final rationale                                               │
│   • Record who verified and when                                        │
│   • This becomes historical data for future runs                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| Document Storage | PostgreSQL | Store policies, procedures, controls, BU profiles |
| Historical Data | PostgreSQL | Store verified applicability decisions |
| LLM Service | Claude API | Generate assessments and rationales |
| Processing Engine | Python | Orchestrate the assessment pipeline |
| Expert Review UI | Web Application | Interface for human verification |

---

## Data Model

### Database Schema

```sql
-- Policies
CREATE TABLE policies (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    scope TEXT,
    version VARCHAR(20),
    effective_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Policy Requirements
CREATE TABLE requirements (
    id VARCHAR(50) PRIMARY KEY,
    policy_id VARCHAR(50) REFERENCES policies(id),
    requirement_text TEXT NOT NULL,
    category VARCHAR(100),
    sequence_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Procedures
CREATE TABLE procedures (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    steps TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Policy-Procedure Links
CREATE TABLE policy_procedures (
    policy_id VARCHAR(50) REFERENCES policies(id),
    procedure_id VARCHAR(50) REFERENCES procedures(id),
    PRIMARY KEY (policy_id, procedure_id)
);

-- Controls
CREATE TABLE controls (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    objective TEXT,
    activities TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Procedure-Control Links
CREATE TABLE procedure_controls (
    procedure_id VARCHAR(50) REFERENCES procedures(id),
    control_id VARCHAR(50) REFERENCES controls(id),
    PRIMARY KEY (procedure_id, control_id)
);

-- Business Units
CREATE TABLE business_units (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    responsibilities TEXT,
    functions TEXT,
    data_types_handled TEXT,
    systems_used TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Historical Applicability (Fed back from expert review)
CREATE TABLE historical_applicability (
    id SERIAL PRIMARY KEY,
    
    -- What was assessed
    policy_id VARCHAR(50) NOT NULL,
    policy_version VARCHAR(20),
    requirement_id VARCHAR(50) NOT NULL,
    requirement_text TEXT,
    business_unit_id VARCHAR(50) NOT NULL,
    business_unit_name VARCHAR(200),
    
    -- The decision
    is_applicable BOOLEAN NOT NULL,
    rationale TEXT NOT NULL,
    confidence VARCHAR(20),
    
    -- Audit trail
    llm_original_decision BOOLEAN,
    llm_original_rationale TEXT,
    was_modified BOOLEAN DEFAULT FALSE,
    
    -- Who verified
    vetted_by VARCHAR(200) NOT NULL,
    vetted_date TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Constraints
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(policy_id, requirement_id, business_unit_id, policy_version)
);

-- Indexes for historical lookups
CREATE INDEX idx_historical_exact 
    ON historical_applicability(requirement_id, business_unit_id);
    
CREATE INDEX idx_historical_requirement 
    ON historical_applicability(requirement_id, vetted_date DESC);
    
CREATE INDEX idx_historical_bu 
    ON historical_applicability(business_unit_id, vetted_date DESC);
```

### Entity Relationships

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   Policy    │──1:N──│   Requirement   │       │             │
└─────────────┘       └─────────────────┘       │             │
      │                       │                 │  Historical │
      │                       │                 │ Applicability│
      │ M:N                   │                 │             │
      ▼                       │                 │             │
┌─────────────┐               │                 └─────────────┘
│  Procedure  │               │                       ▲
└─────────────┘               │                       │
      │                       │                       │
      │ M:N                   │      Assessed For     │
      ▼                       └───────────────────────┤
┌─────────────┐                                       │
│   Control   │                                       │
└─────────────┘                                       │
                                                      │
┌─────────────┐                                       │
│Business Unit│───────────────────────────────────────┘
└─────────────┘
```

---

## Processing Pipeline

### Main Processing Loop

The system processes each (Requirement × Business Unit) pair independently:

```
Policy has N Requirements
Organization has M Business Units
                    ↓
            N × M = Total Assessments
                    ↓
        Each assessment: Same template, different data
```

### Historical Lookup Strategy

Before building each prompt, attempt to find relevant historical examples:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      HISTORICAL LOOKUP SEQUENCE                          │
│                                                                          │
│   Query 1: EXACT MATCH                                                  │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  "Has this specific requirement been assessed for this          │   │
│   │   specific BU before?"                                          │   │
│   │                                                                  │   │
│   │  SQL: WHERE requirement_id = X AND business_unit_id = Y         │   │
│   │  Result: 0 or 1 record                                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   Query 2: SAME REQUIREMENT, DIFFERENT BUs                              │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  "How was this requirement assessed for OTHER business units?"  │   │
│   │                                                                  │   │
│   │  SQL: WHERE requirement_id = X AND business_unit_id != Y        │   │
│   │  Result: 0 to N records (take top 2-3)                          │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   Query 3: SAME BU, DIFFERENT REQUIREMENTS                              │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  "How were other requirements assessed for THIS business unit?" │   │
│   │                                                                  │   │
│   │  SQL: WHERE business_unit_id = Y AND requirement_id != X        │   │
│   │  Result: 0 to N records (take top 2)                            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   COMBINE & RETURN                                                      │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Return up to 5 unique examples                                 │   │
│   │  (May return 0 - that's completely fine)                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### What Historical Data Provides

Historical data is **reference material**, not ground truth:

| It IS | It is NOT |
|-------|-----------|
| Reasoning examples - how humans structured rationale | Ground truth for current applicability |
| Terminology patterns - language and framing used | A lookup table (history=yes → answer=yes) |
| Consideration prompts - what factors were weighed | Complete coverage for all BUs |
| Calibration reference - what evidence justified decisions | A constraint on the current decision |

**Critical:** The current BU description is the source of truth. Historical decisions may no longer apply if the BU has changed.

---

## Prompt Engineering

### Design Principles

1. **Complete Context:** Include all relevant documents in full
2. **Clear Authority:** Emphasize current BU description as source of truth
3. **Historical as Reference:** Past decisions inform reasoning style, not outcome
4. **Structured Output:** JSON format for reliable parsing
5. **Evidence Requirements:** Force citation of specific quotes

### Prompt Variants

The system uses two prompt variants based on historical data availability:

| Scenario | Prompt Variant | Key Differences |
|----------|----------------|-----------------|
| Historical data found | WITH History | Includes historical section; asks for comparison |
| No historical data | WITHOUT History | Omits historical section; asks for assumptions/ambiguities |

---

## Prompt Template: WITH Historical Data

```xml
<system>
You are a Policy Compliance Analyst determining whether a policy 
requirement applies to a business unit.

DECISION AUTHORITY:
Your decision MUST be based on the CURRENT business unit description - 
this is the source of truth. Business units change over time, so 
historical decisions may no longer apply.

HISTORICAL DATA USAGE:
Historical decisions are provided as REFERENCE ONLY:
• They show how rationales were structured
• They demonstrate what factors were considered
• They are NOT authoritative - the BU may have changed
• Your decision may differ from history if the current BU description 
  no longer matches the historical reasoning

OUTPUT REQUIREMENTS:
• Cite specific quotes from the CURRENT BU description
• Structure rationale clearly with evidence
• If your decision differs from historical, explain why
</system>

<policy>
<id>POL-DP-001</id>
<name>Data Protection Policy</name>
<description>
This policy establishes requirements for protecting personally 
identifiable information (PII) and sensitive data across the 
organization. It applies to all systems, processes, and personnel 
that handle protected data categories as defined in Section 2.
</description>
<scope>
All business units that process, store, or transmit PII or 
sensitive business data.
</scope>
</policy>

<procedures>
<procedure>
<id>PROC-DP-001</id>
<name>Data Classification Procedure</name>
<description>
Defines how data must be classified based on sensitivity level.
PII includes: Social Security Numbers, financial account numbers,
health information, and biometric data.
</description>
</procedure>

<procedure>
<id>PROC-DP-003</id>
<name>Encryption Implementation Procedure</name>
<description>
All systems storing PII must implement AES-256 encryption at rest.
Data in transit must use TLS 1.2 or higher.
</description>
</procedure>
</procedures>

<controls>
<control>
<id>CTL-DP-007</id>
<name>Encryption at Rest Control</name>
<objective>
Ensure all PII is encrypted when stored in any system or database.
</objective>
<activities>
- Enable database-level encryption
- Encrypt file storage containing PII
- Manage encryption keys via approved key management system
</activities>
</control>
</controls>

<requirement_to_assess>
<id>REQ-DP-007</id>
<text>
All systems processing Personally Identifiable Information (PII) 
must implement encryption at rest and in transit.
</text>
<category>Data Security</category>
</requirement_to_assess>

<business_unit>
<id>BU-PAYROLL</id>
<name>Payroll Operations</name>

<description>
Manages employee compensation processing including salary calculations, 
tax withholdings, direct deposit setup, and year-end W-2 generation.
</description>

<responsibilities>
- Process bi-weekly payroll for 5,000 employees
- Maintain employee bank account information for direct deposit
- Calculate and submit federal and state tax withholdings
- Generate W-2 and 1099 tax documents annually
- Interface with ADP payroll system for processing
- Respond to employee payroll inquiries
</responsibilities>

<systems_used>
- ADP Workforce Now (payroll processing)
- Internal HR data feed (employee demographics)
- Bank integration APIs (direct deposit)
</systems_used>

NOTE: This description reflects the CURRENT state of this business unit.
Base your decision on THIS description.
</business_unit>

<historical_reference>
The following are previous assessments provided as REFERENCE for 
rationale structure and reasoning patterns. These are NOT authoritative - 
the business unit may have changed since these were recorded.

<previous_decision>
<match_type>exact_match</match_type>
<requirement>REQ-DP-007</requirement>
<business_unit>Payroll Operations</business_unit>
<assessed_date>2024-03-15</assessed_date>
<decision>APPLICABLE</decision>
<rationale>
Payroll handles employee SSNs for tax reporting and bank account 
numbers for direct deposit. These are explicitly listed as PII in 
Section 2.1 of the policy. The ADP system stores this data, requiring 
encryption per this requirement.
</rationale>
</previous_decision>

<previous_decision>
<match_type>same_requirement</match_type>
<requirement>REQ-DP-007</requirement>
<business_unit>Human Resources</business_unit>
<assessed_date>2024-03-15</assessed_date>
<decision>APPLICABLE</decision>
<rationale>
HR manages employee records in Workday including SSNs and home 
addresses. Per their charter, HR is responsible for 'secure maintenance 
of personnel files.' SSNs and addresses constitute PII under Section 2.1, 
triggering the encryption requirement.
</rationale>
</previous_decision>

<previous_decision>
<match_type>same_requirement</match_type>
<requirement>REQ-DP-007</requirement>
<business_unit>Marketing</business_unit>
<assessed_date>2024-03-15</assessed_date>
<decision>NOT APPLICABLE</decision>
<rationale>
Marketing manages campaign analytics and content creation. Their 
systems (HubSpot, Adobe) contain business contact info but not PII 
as defined in Section 2.1. Business email addresses alone are not 
classified as PII per this policy.
</rationale>
</previous_decision>

</historical_reference>

<task>
Assess whether requirement REQ-DP-007 applies to Payroll Operations.

Analyze step by step:
1. What in this requirement triggers applicability? 
   (What activities, data types, or systems make a BU subject to this?)

2. Does the CURRENT Payroll Operations description show evidence of 
   these triggers? Quote specific text.

3. Review historical decisions:
   - What reasoning pattern was used?
   - Does the CURRENT BU description still support that reasoning?
   - If your decision differs from history, explain what changed.

4. Make your determination with clear evidence.
</task>

<output_format>
Respond with this exact JSON structure:

{
  "requirement_id": "REQ-DP-007",
  "business_unit_id": "BU-PAYROLL",
  "is_applicable": true or false,
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "rationale": {
    "requirement_triggers": "What specifically triggers applicability",
    "current_bu_evidence": "Analysis of CURRENT BU description with quotes",
    "supporting_evidence": [
      {
        "source": "BU_DESCRIPTION or PROCEDURE or CONTROL",
        "quote": "Exact quote from document",
        "relevance": "Why this supports the decision"
      }
    ],
    "historical_comparison": {
      "prior_decision": "APPLICABLE or NOT_APPLICABLE",
      "current_decision_aligns": true or false,
      "explanation": "Why decision aligns or differs from history"
    },
    "conclusion": "2-3 sentence summary"
  }
}
</output_format>
```

---

## Prompt Template: WITHOUT Historical Data

```xml
<system>
You are a Policy Compliance Analyst determining whether a policy 
requirement applies to a business unit.

DECISION AUTHORITY:
Your decision MUST be based on the business unit description - 
this is the source of truth for what the BU currently does.

NO HISTORICAL DATA AVAILABLE:
There are no previous assessments for this requirement/BU combination 
or similar combinations. This is normal for new policies or business 
units that haven't been assessed before.

You will reason from first principles using the provided documents.

OUTPUT REQUIREMENTS:
• Cite specific quotes from the BU description
• Reference procedures and controls where relevant
• Structure rationale clearly with evidence
• Note any assumptions or ambiguities
</system>

<policy>
<id>POL-DP-001</id>
<name>Data Protection Policy</name>
<description>
This policy establishes requirements for protecting personally 
identifiable information (PII) and sensitive data across the 
organization. It applies to all systems, processes, and personnel 
that handle protected data categories as defined in Section 2.
</description>
<scope>
All business units that process, store, or transmit PII or 
sensitive business data.
</scope>
</policy>

<procedures>
<procedure>
<id>PROC-DP-001</id>
<name>Data Classification Procedure</name>
<description>
Defines how data must be classified based on sensitivity level.
PII includes: Social Security Numbers, financial account numbers,
health information, and biometric data.
</description>
</procedure>

<procedure>
<id>PROC-DP-003</id>
<name>Encryption Implementation Procedure</name>
<description>
All systems storing PII must implement AES-256 encryption at rest.
Data in transit must use TLS 1.2 or higher.
</description>
</procedure>
</procedures>

<controls>
<control>
<id>CTL-DP-007</id>
<name>Encryption at Rest Control</name>
<objective>
Ensure all PII is encrypted when stored in any system or database.
</objective>
<activities>
- Enable database-level encryption
- Encrypt file storage containing PII
- Manage encryption keys via approved key management system
</activities>
</control>
</controls>

<requirement_to_assess>
<id>REQ-DP-007</id>
<text>
All systems processing Personally Identifiable Information (PII) 
must implement encryption at rest and in transit.
</text>
<category>Data Security</category>
</requirement_to_assess>

<business_unit>
<id>BU-PAYROLL</id>
<name>Payroll Operations</name>

<description>
Manages employee compensation processing including salary calculations, 
tax withholdings, direct deposit setup, and year-end W-2 generation.
</description>

<responsibilities>
- Process bi-weekly payroll for 5,000 employees
- Maintain employee bank account information for direct deposit
- Calculate and submit federal and state tax withholdings
- Generate W-2 and 1099 tax documents annually
- Interface with ADP payroll system for processing
- Respond to employee payroll inquiries
</responsibilities>

<systems_used>
- ADP Workforce Now (payroll processing)
- Internal HR data feed (employee demographics)
- Bank integration APIs (direct deposit)
</systems_used>
</business_unit>

<task>
Assess whether requirement REQ-DP-007 applies to Payroll Operations.

No historical assessments exist for reference. Reason from the 
documents provided.

Analyze step by step:
1. What in this requirement triggers applicability?
   (What activities, data types, or systems make a BU subject to this?)

2. Review the policy scope and procedures:
   - What is defined as PII?
   - What conditions must be met?

3. Examine the Payroll Operations description:
   - Quote specific text that shows relevant activities or data
   - Does this BU handle data types that match the PII definition?

4. Make your determination:
   - Cite specific evidence
   - Note any assumptions you're making
   - Flag any ambiguities

</task>

<output_format>
Respond with this exact JSON structure:

{
  "requirement_id": "REQ-DP-007",
  "business_unit_id": "BU-PAYROLL",
  "is_applicable": true or false,
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "rationale": {
    "requirement_triggers": "What specifically triggers applicability",
    "pii_definition_applied": "What counts as PII per the policy/procedures",
    "current_bu_evidence": "Analysis of BU description with quotes",
    "supporting_evidence": [
      {
        "source": "BU_DESCRIPTION or PROCEDURE or CONTROL",
        "quote": "Exact quote from document",
        "relevance": "Why this supports the decision"
      }
    ],
    "assumptions": ["List any assumptions made"],
    "ambiguities": ["List any unclear areas"],
    "conclusion": "2-3 sentence summary"
  }
}
</output_format>
```

---

## Prompt Comparison Summary

| Section | WITH History | WITHOUT History |
|---------|--------------|-----------------|
| **System instructions** | Emphasizes history is reference only | Emphasizes reasoning from first principles |
| **Policy context** | Same | Same |
| **Procedures** | Same | Same |
| **Controls** | Same | Same |
| **Requirement** | Same | Same |
| **Business Unit** | Same | Same |
| **Historical reference** | 1-5 prior decisions with rationales | Section omitted entirely |
| **Task instructions** | Includes "compare to historical" step | Includes "note assumptions" step |
| **Output format** | Has `historical_comparison` field | Has `assumptions` and `ambiguities` fields |

---

## Code Implementation

### Data Classes

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Policy:
    id: str
    name: str
    description: str
    scope: str
    version: Optional[str] = None

@dataclass
class Requirement:
    id: str
    policy_id: str
    text: str
    category: Optional[str] = None

@dataclass
class Procedure:
    id: str
    name: str
    description: str
    steps: Optional[str] = None

@dataclass
class Control:
    id: str
    name: str
    objective: str
    activities: Optional[str] = None

@dataclass
class BusinessUnit:
    id: str
    name: str
    description: str
    responsibilities: str
    functions: Optional[str] = None
    data_types_handled: Optional[str] = None
    systems_used: Optional[str] = None

@dataclass
class HistoricalDecision:
    requirement_id: str
    requirement_text: str
    business_unit_id: str
    business_unit_name: str
    is_applicable: bool
    rationale: str
    assessed_date: datetime
    match_type: str  # 'exact_match', 'same_requirement', 'same_bu'

@dataclass
class AssessmentResult:
    requirement_id: str
    business_unit_id: str
    is_applicable: bool
    confidence: str
    rationale: dict
    history_was_available: bool
```

### Database Access Layer

```python
import psycopg2
from typing import List, Optional

class DatabaseAccess:
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
    
    def get_policy(self, policy_id: str) -> Policy:
        """Fetch policy by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, description, scope, version FROM policies WHERE id = %s",
            (policy_id,)
        )
        row = cursor.fetchone()
        return Policy(
            id=row[0],
            name=row[1],
            description=row[2],
            scope=row[3],
            version=row[4]
        )
    
    def get_requirements(self, policy_id: str) -> List[Requirement]:
        """Fetch all requirements for a policy."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, policy_id, requirement_text, category 
               FROM requirements 
               WHERE policy_id = %s 
               ORDER BY sequence_number""",
            (policy_id,)
        )
        return [
            Requirement(id=row[0], policy_id=row[1], text=row[2], category=row[3])
            for row in cursor.fetchall()
        ]
    
    def get_procedures_for_policy(self, policy_id: str) -> List[Procedure]:
        """Fetch all procedures linked to a policy."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT p.id, p.name, p.description, p.steps
               FROM procedures p
               JOIN policy_procedures pp ON p.id = pp.procedure_id
               WHERE pp.policy_id = %s""",
            (policy_id,)
        )
        return [
            Procedure(id=row[0], name=row[1], description=row[2], steps=row[3])
            for row in cursor.fetchall()
        ]
    
    def get_controls_for_procedures(self, procedure_ids: List[str]) -> List[Control]:
        """Fetch all controls linked to given procedures."""
        if not procedure_ids:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT DISTINCT c.id, c.name, c.objective, c.activities
               FROM controls c
               JOIN procedure_controls pc ON c.id = pc.control_id
               WHERE pc.procedure_id = ANY(%s)""",
            (procedure_ids,)
        )
        return [
            Control(id=row[0], name=row[1], objective=row[2], activities=row[3])
            for row in cursor.fetchall()
        ]
    
    def get_all_business_units(self) -> List[BusinessUnit]:
        """Fetch all business units."""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT id, name, description, responsibilities, 
                      functions, data_types_handled, systems_used
               FROM business_units"""
        )
        return [
            BusinessUnit(
                id=row[0], name=row[1], description=row[2],
                responsibilities=row[3], functions=row[4],
                data_types_handled=row[5], systems_used=row[6]
            )
            for row in cursor.fetchall()
        ]
    
    def save_assessment(self, result: AssessmentResult, 
                        policy_id: str, policy_version: str,
                        requirement_text: str, bu_name: str,
                        vetted_by: str) -> None:
        """Save verified assessment to historical database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO historical_applicability 
               (policy_id, policy_version, requirement_id, requirement_text,
                business_unit_id, business_unit_name, is_applicable, rationale,
                confidence, llm_original_decision, llm_original_rationale,
                was_modified, vetted_by, vetted_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
               ON CONFLICT (policy_id, requirement_id, business_unit_id, policy_version)
               DO UPDATE SET
                   is_applicable = EXCLUDED.is_applicable,
                   rationale = EXCLUDED.rationale,
                   confidence = EXCLUDED.confidence,
                   was_modified = EXCLUDED.was_modified,
                   vetted_by = EXCLUDED.vetted_by,
                   vetted_date = NOW()""",
            (policy_id, policy_version, result.requirement_id, requirement_text,
             result.business_unit_id, bu_name, result.is_applicable,
             str(result.rationale), result.confidence, result.is_applicable,
             str(result.rationale), False, vetted_by)
        )
        self.conn.commit()
```

### Historical Lookup

```python
class HistoricalLookup:
    def __init__(self, db: DatabaseAccess):
        self.db = db
    
    def find_historical_reference(
        self,
        requirement_id: str,
        business_unit_id: str,
        max_results: int = 5
    ) -> List[HistoricalDecision]:
        """
        Find historical rationales as reasoning examples.
        Returns empty list if nothing found - that's OK.
        """
        results = []
        seen_keys = set()
        
        cursor = self.db.conn.cursor()
        
        # ─────────────────────────────────────────────────────────
        # Query 1: Exact match (this requirement + this BU)
        # ─────────────────────────────────────────────────────────
        cursor.execute(
            """SELECT requirement_id, requirement_text, business_unit_id,
                      business_unit_name, is_applicable, rationale, vetted_date
               FROM historical_applicability 
               WHERE requirement_id = %s AND business_unit_id = %s
               ORDER BY vetted_date DESC
               LIMIT 1""",
            (requirement_id, business_unit_id)
        )
        
        row = cursor.fetchone()
        if row:
            results.append(HistoricalDecision(
                requirement_id=row[0],
                requirement_text=row[1],
                business_unit_id=row[2],
                business_unit_name=row[3],
                is_applicable=row[4],
                rationale=row[5],
                assessed_date=row[6],
                match_type="exact_match"
            ))
            seen_keys.add((row[0], row[2]))
        
        # ─────────────────────────────────────────────────────────
        # Query 2: Same requirement, different BUs
        # ─────────────────────────────────────────────────────────
        cursor.execute(
            """SELECT requirement_id, requirement_text, business_unit_id,
                      business_unit_name, is_applicable, rationale, vetted_date
               FROM historical_applicability 
               WHERE requirement_id = %s AND business_unit_id != %s
               ORDER BY vetted_date DESC
               LIMIT 3""",
            (requirement_id, business_unit_id)
        )
        
        for row in cursor.fetchall():
            key = (row[0], row[2])
            if key not in seen_keys:
                results.append(HistoricalDecision(
                    requirement_id=row[0],
                    requirement_text=row[1],
                    business_unit_id=row[2],
                    business_unit_name=row[3],
                    is_applicable=row[4],
                    rationale=row[5],
                    assessed_date=row[6],
                    match_type="same_requirement"
                ))
                seen_keys.add(key)
        
        # ─────────────────────────────────────────────────────────
        # Query 3: Same BU, different requirements
        # ─────────────────────────────────────────────────────────
        cursor.execute(
            """SELECT requirement_id, requirement_text, business_unit_id,
                      business_unit_name, is_applicable, rationale, vetted_date
               FROM historical_applicability 
               WHERE business_unit_id = %s AND requirement_id != %s
               ORDER BY vetted_date DESC
               LIMIT 2""",
            (business_unit_id, requirement_id)
        )
        
        for row in cursor.fetchall():
            key = (row[0], row[2])
            if key not in seen_keys:
                results.append(HistoricalDecision(
                    requirement_id=row[0],
                    requirement_text=row[1],
                    business_unit_id=row[2],
                    business_unit_name=row[3],
                    is_applicable=row[4],
                    rationale=row[5],
                    assessed_date=row[6],
                    match_type="same_bu"
                ))
                seen_keys.add(key)
        
        # Return up to max_results (may be empty - that's fine)
        return results[:max_results]
```

### Prompt Builder

```python
class PromptBuilder:
    """Builds assessment prompts with or without historical data."""
    
    def build_prompt(
        self,
        policy: Policy,
        requirement: Requirement,
        business_unit: BusinessUnit,
        procedures: List[Procedure],
        controls: List[Control],
        historical_data: List[HistoricalDecision]
    ) -> str:
        """
        Build the complete assessment prompt.
        Uses different templates based on historical data availability.
        """
        
        # System instructions vary based on history availability
        if historical_data:
            system_section = self._build_system_with_history()
        else:
            system_section = self._build_system_without_history()
        
        # These sections are always the same
        policy_section = self._build_policy_section(policy)
        procedures_section = self._build_procedures_section(procedures)
        controls_section = self._build_controls_section(controls)
        requirement_section = self._build_requirement_section(requirement)
        bu_section = self._build_bu_section(business_unit)
        
        # Historical section only if data exists
        if historical_data:
            historical_section = self._build_historical_section(historical_data)
            task_section = self._build_task_with_history(requirement, business_unit)
            output_section = self._build_output_with_history()
        else:
            historical_section = ""
            task_section = self._build_task_without_history(requirement, business_unit)
            output_section = self._build_output_without_history()
        
        # Assemble full prompt
        prompt = f"""<system>
{system_section}
</system>

{policy_section}

{procedures_section}

{controls_section}

{requirement_section}

{bu_section}

{historical_section}

{task_section}

{output_section}
"""
        return prompt
    
    def _build_system_with_history(self) -> str:
        return """You are a Policy Compliance Analyst determining whether a policy 
requirement applies to a business unit.

DECISION AUTHORITY:
Your decision MUST be based on the CURRENT business unit description - 
this is the source of truth. Business units change over time, so 
historical decisions may no longer apply.

HISTORICAL DATA USAGE:
Historical decisions are provided as REFERENCE ONLY:
• They show how rationales were structured
• They demonstrate what factors were considered
• They are NOT authoritative - the BU may have changed
• Your decision may differ from history if the current BU description 
  no longer matches the historical reasoning

OUTPUT REQUIREMENTS:
• Cite specific quotes from the CURRENT BU description
• Structure rationale clearly with evidence
• If your decision differs from historical, explain why"""
    
    def _build_system_without_history(self) -> str:
        return """You are a Policy Compliance Analyst determining whether a policy 
requirement applies to a business unit.

DECISION AUTHORITY:
Your decision MUST be based on the business unit description - 
this is the source of truth for what the BU currently does.

NO HISTORICAL DATA AVAILABLE:
There are no previous assessments for this requirement/BU combination 
or similar combinations. This is normal for new policies or business 
units that haven't been assessed before.

You will reason from first principles using the provided documents.

OUTPUT REQUIREMENTS:
• Cite specific quotes from the BU description
• Reference procedures and controls where relevant
• Structure rationale clearly with evidence
• Note any assumptions or ambiguities"""
    
    def _build_policy_section(self, policy: Policy) -> str:
        return f"""<policy>
<id>{policy.id}</id>
<name>{policy.name}</name>
<description>
{policy.description}
</description>
<scope>
{policy.scope}
</scope>
</policy>"""
    
    def _build_procedures_section(self, procedures: List[Procedure]) -> str:
        if not procedures:
            return "<procedures>\nNo procedures linked to this policy.\n</procedures>"
        
        sections = ["<procedures>"]
        for proc in procedures:
            sections.append(f"""<procedure>
<id>{proc.id}</id>
<name>{proc.name}</name>
<description>
{proc.description}
</description>
</procedure>""")
        sections.append("</procedures>")
        return "\n".join(sections)
    
    def _build_controls_section(self, controls: List[Control]) -> str:
        if not controls:
            return "<controls>\nNo controls linked to this policy.\n</controls>"
        
        sections = ["<controls>"]
        for ctrl in controls:
            sections.append(f"""<control>
<id>{ctrl.id}</id>
<name>{ctrl.name}</name>
<objective>
{ctrl.objective}
</objective>
<activities>
{ctrl.activities}
</activities>
</control>""")
        sections.append("</controls>")
        return "\n".join(sections)
    
    def _build_requirement_section(self, requirement: Requirement) -> str:
        return f"""<requirement_to_assess>
<id>{requirement.id}</id>
<text>
{requirement.text}
</text>
<category>{requirement.category or 'General'}</category>
</requirement_to_assess>"""
    
    def _build_bu_section(self, bu: BusinessUnit) -> str:
        return f"""<business_unit>
<id>{bu.id}</id>
<name>{bu.name}</name>

<description>
{bu.description}
</description>

<responsibilities>
{bu.responsibilities}
</responsibilities>

<systems_used>
{bu.systems_used or 'Not specified'}
</systems_used>

NOTE: This description reflects the CURRENT state of this business unit.
Base your decision on THIS description.
</business_unit>"""
    
    def _build_historical_section(self, historical: List[HistoricalDecision]) -> str:
        sections = ["""<historical_reference>
The following are previous assessments provided as REFERENCE for 
rationale structure and reasoning patterns. These are NOT authoritative - 
the business unit may have changed since these were recorded.
"""]
        
        for hist in historical:
            decision_str = "APPLICABLE" if hist.is_applicable else "NOT APPLICABLE"
            sections.append(f"""<previous_decision>
<match_type>{hist.match_type}</match_type>
<requirement>{hist.requirement_id}</requirement>
<business_unit>{hist.business_unit_name}</business_unit>
<assessed_date>{hist.assessed_date.strftime('%Y-%m-%d')}</assessed_date>
<decision>{decision_str}</decision>
<rationale>
{hist.rationale}
</rationale>
</previous_decision>""")
        
        sections.append("\n</historical_reference>")
        return "\n".join(sections)
    
    def _build_task_with_history(self, req: Requirement, bu: BusinessUnit) -> str:
        return f"""<task>
Assess whether requirement {req.id} applies to {bu.name}.

Analyze step by step:
1. What in this requirement triggers applicability? 
   (What activities, data types, or systems make a BU subject to this?)

2. Does the CURRENT {bu.name} description show evidence of 
   these triggers? Quote specific text.

3. Review historical decisions:
   - What reasoning pattern was used?
   - Does the CURRENT BU description still support that reasoning?
   - If your decision differs from history, explain what changed.

4. Make your determination with clear evidence.
</task>"""
    
    def _build_task_without_history(self, req: Requirement, bu: BusinessUnit) -> str:
        return f"""<task>
Assess whether requirement {req.id} applies to {bu.name}.

No historical assessments exist for reference. Reason from the 
documents provided.

Analyze step by step:
1. What in this requirement triggers applicability?
   (What activities, data types, or systems make a BU subject to this?)

2. Review the policy scope and procedures:
   - What is defined as protected data or covered activities?
   - What conditions must be met?

3. Examine the {bu.name} description:
   - Quote specific text that shows relevant activities or data
   - Does this BU's activities match the requirement triggers?

4. Make your determination:
   - Cite specific evidence
   - Note any assumptions you're making
   - Flag any ambiguities
</task>"""
    
    def _build_output_with_history(self) -> str:
        return """<output_format>
Respond with this exact JSON structure:

{
  "requirement_id": "...",
  "business_unit_id": "...",
  "is_applicable": true or false,
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "rationale": {
    "requirement_triggers": "What specifically triggers applicability",
    "current_bu_evidence": "Analysis of CURRENT BU description with quotes",
    "supporting_evidence": [
      {
        "source": "BU_DESCRIPTION or PROCEDURE or CONTROL",
        "quote": "Exact quote from document",
        "relevance": "Why this supports the decision"
      }
    ],
    "historical_comparison": {
      "prior_decision": "APPLICABLE or NOT_APPLICABLE or NO_EXACT_MATCH",
      "current_decision_aligns": true or false,
      "explanation": "Why decision aligns or differs from history"
    },
    "conclusion": "2-3 sentence summary"
  }
}
</output_format>"""
    
    def _build_output_without_history(self) -> str:
        return """<output_format>
Respond with this exact JSON structure:

{
  "requirement_id": "...",
  "business_unit_id": "...",
  "is_applicable": true or false,
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "rationale": {
    "requirement_triggers": "What specifically triggers applicability",
    "pii_definition_applied": "What counts as protected data per policy",
    "current_bu_evidence": "Analysis of BU description with quotes",
    "supporting_evidence": [
      {
        "source": "BU_DESCRIPTION or PROCEDURE or CONTROL",
        "quote": "Exact quote from document",
        "relevance": "Why this supports the decision"
      }
    ],
    "assumptions": ["List any assumptions made"],
    "ambiguities": ["List any unclear areas"],
    "conclusion": "2-3 sentence summary"
  }
}
</output_format>"""
```

### Main Processing Engine

```python
import json
from typing import List
from anthropic import Anthropic

class PolicyApplicabilityEngine:
    """Main engine for processing policy applicability assessments."""
    
    def __init__(self, db: DatabaseAccess, llm_client: Anthropic):
        self.db = db
        self.llm = llm_client
        self.historical_lookup = HistoricalLookup(db)
        self.prompt_builder = PromptBuilder()
    
    def process_policy_change(self, policy_id: str) -> List[AssessmentResult]:
        """
        Process a policy change notification.
        Assesses all requirements against all business units.
        
        Args:
            policy_id: The ID of the changed policy
            
        Returns:
            List of assessment results for expert review
        """
        
        # ─────────────────────────────────────────────────────────────
        # STEP 1: Fetch all context (done once, reused for all assessments)
        # ─────────────────────────────────────────────────────────────
        print(f"Fetching policy context for {policy_id}...")
        
        policy = self.db.get_policy(policy_id)
        requirements = self.db.get_requirements(policy_id)
        procedures = self.db.get_procedures_for_policy(policy_id)
        procedure_ids = [p.id for p in procedures]
        controls = self.db.get_controls_for_procedures(procedure_ids)
        business_units = self.db.get_all_business_units()
        
        print(f"  - Policy: {policy.name}")
        print(f"  - Requirements: {len(requirements)}")
        print(f"  - Procedures: {len(procedures)}")
        print(f"  - Controls: {len(controls)}")
        print(f"  - Business Units: {len(business_units)}")
        print(f"  - Total assessments: {len(requirements) * len(business_units)}")
        
        results = []
        
        # ─────────────────────────────────────────────────────────────
        # STEP 2: Loop through each (Requirement × Business Unit) pair
        # ─────────────────────────────────────────────────────────────
        total = len(requirements) * len(business_units)
        current = 0
        
        for requirement in requirements:
            for bu in business_units:
                current += 1
                print(f"\nProcessing {current}/{total}: {requirement.id} × {bu.name}")
                
                # ─────────────────────────────────────────────────────
                # STEP 2a: Historical lookup (simple SQL queries)
                # ─────────────────────────────────────────────────────
                historical_data = self.historical_lookup.find_historical_reference(
                    requirement_id=requirement.id,
                    business_unit_id=bu.id
                )
                
                history_status = f"Found {len(historical_data)} historical examples" \
                    if historical_data else "No historical data"
                print(f"  - Historical lookup: {history_status}")
                
                # ─────────────────────────────────────────────────────
                # STEP 2b: Build prompt (with or without history)
                # ─────────────────────────────────────────────────────
                prompt = self.prompt_builder.build_prompt(
                    policy=policy,
                    requirement=requirement,
                    business_unit=bu,
                    procedures=procedures,
                    controls=controls,
                    historical_data=historical_data
                )
                
                # ─────────────────────────────────────────────────────
                # STEP 2c: Call LLM
                # ─────────────────────────────────────────────────────
                print(f"  - Calling LLM...")
                response = self._call_llm(prompt)
                
                # ─────────────────────────────────────────────────────
                # STEP 2d: Parse response
                # ─────────────────────────────────────────────────────
                assessment = self._parse_response(
                    response=response,
                    requirement_id=requirement.id,
                    business_unit_id=bu.id,
                    history_available=len(historical_data) > 0
                )
                
                print(f"  - Result: {'APPLICABLE' if assessment.is_applicable else 'NOT APPLICABLE'} "
                      f"(Confidence: {assessment.confidence})")
                
                results.append(assessment)
        
        # ─────────────────────────────────────────────────────────────
        # STEP 3: Return results for expert review
        # ─────────────────────────────────────────────────────────────
        print(f"\n{'='*60}")
        print(f"Processing complete. {len(results)} assessments generated.")
        print(f"Ready for expert review.")
        
        return results
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API with the given prompt."""
        message = self.llm.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0,  # Deterministic output
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def _parse_response(
        self, 
        response: str,
        requirement_id: str,
        business_unit_id: str,
        history_available: bool
    ) -> AssessmentResult:
        """Parse the LLM response into an AssessmentResult."""
        
        # Extract JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        
        try:
            data = json.loads(json_str.strip())
            return AssessmentResult(
                requirement_id=data.get("requirement_id", requirement_id),
                business_unit_id=data.get("business_unit_id", business_unit_id),
                is_applicable=data.get("is_applicable", False),
                confidence=data.get("confidence", "LOW"),
                rationale=data.get("rationale", {}),
                history_was_available=history_available
            )
        except json.JSONDecodeError as e:
            # Return a low-confidence result if parsing fails
            return AssessmentResult(
                requirement_id=requirement_id,
                business_unit_id=business_unit_id,
                is_applicable=False,
                confidence="LOW",
                rationale={"error": f"Failed to parse LLM response: {e}", "raw": response},
                history_was_available=history_available
            )


def main():
    """Main entry point for processing a policy change."""
    
    # Configuration
    DB_CONNECTION = "postgresql://user:password@localhost/policy_db"
    ANTHROPIC_API_KEY = "your-api-key"
    
    # Initialize components
    db = DatabaseAccess(DB_CONNECTION)
    llm_client = Anthropic(api_key=ANTHROPIC_API_KEY)
    engine = PolicyApplicabilityEngine(db, llm_client)
    
    # Process policy change (policy ID would come from email trigger)
    policy_id = "POL-DP-001"
    
    print(f"Processing policy change for: {policy_id}")
    print("="*60)
    
    results = engine.process_policy_change(policy_id)
    
    # Output results for expert review
    print("\n" + "="*60)
    print("ASSESSMENT RESULTS")
    print("="*60)
    
    # Group by business unit
    by_bu = {}
    for result in results:
        if result.business_unit_id not in by_bu:
            by_bu[result.business_unit_id] = []
        by_bu[result.business_unit_id].append(result)
    
    for bu_id, bu_results in by_bu.items():
        applicable = [r for r in bu_results if r.is_applicable]
        not_applicable = [r for r in bu_results if not r.is_applicable]
        
        print(f"\n{bu_id}:")
        print(f"  Applicable: {len(applicable)} requirements")
        print(f"  Not Applicable: {len(not_applicable)} requirements")
        print(f"  Low Confidence (needs review): {len([r for r in bu_results if r.confidence == 'LOW'])}")


if __name__ == "__main__":
    main()
```

### Parallel Processing (Optional Optimization)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

class ParallelPolicyEngine(PolicyApplicabilityEngine):
    """Extended engine with parallel processing support."""
    
    async def process_policy_change_parallel(
        self, 
        policy_id: str,
        max_concurrent: int = 10
    ) -> List[AssessmentResult]:
        """
        Process policy change with parallel LLM calls.
        
        Args:
            policy_id: The ID of the changed policy
            max_concurrent: Maximum concurrent LLM calls
            
        Returns:
            List of assessment results
        """
        
        # Fetch all context (same as before)
        policy = self.db.get_policy(policy_id)
        requirements = self.db.get_requirements(policy_id)
        procedures = self.db.get_procedures_for_policy(policy_id)
        controls = self.db.get_controls_for_procedures([p.id for p in procedures])
        business_units = self.db.get_all_business_units()
        
        # Build all assessment tasks
        tasks = [
            (req, bu)
            for req in requirements
            for bu in business_units
        ]
        
        # Process with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def assess_with_limit(req: Requirement, bu: BusinessUnit) -> AssessmentResult:
            async with semaphore:
                return await self._assess_single_async(
                    policy, req, bu, procedures, controls
                )
        
        # Run all assessments concurrently
        results = await asyncio.gather(*[
            assess_with_limit(req, bu) for req, bu in tasks
        ])
        
        return list(results)
    
    async def _assess_single_async(
        self,
        policy: Policy,
        requirement: Requirement,
        bu: BusinessUnit,
        procedures: List[Procedure],
        controls: List[Control]
    ) -> AssessmentResult:
        """Async version of single assessment."""
        
        # Historical lookup (sync - database query)
        historical_data = self.historical_lookup.find_historical_reference(
            requirement_id=requirement.id,
            business_unit_id=bu.id
        )
        
        # Build prompt
        prompt = self.prompt_builder.build_prompt(
            policy=policy,
            requirement=requirement,
            business_unit=bu,
            procedures=procedures,
            controls=controls,
            historical_data=historical_data
        )
        
        # Async LLM call
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._call_llm, prompt
        )
        
        # Parse response
        return self._parse_response(
            response=response,
            requirement_id=requirement.id,
            business_unit_id=bu.id,
            history_available=len(historical_data) > 0
        )
```

---

## Expert Review Workflow

### Review Interface Mockup

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXPERT REVIEW INTERFACE                               │
│                                                                          │
│  Policy: Data Protection Policy v2.3                                    │
│  Requirement: REQ-DP-007 - PII Encryption                               │
│  Business Unit: Payroll Operations                                       │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  LLM ASSESSMENT:                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Decision: ● APPLICABLE  ○ NOT APPLICABLE                        │   │
│  │                                                                  │   │
│  │ Confidence: HIGH                                                 │   │
│  │                                                                  │   │
│  │ Rationale:                                                       │   │
│  │ "Payroll Operations manages employee compensation including     │   │
│  │  direct deposit setup which requires bank account numbers.      │   │
│  │  Per their description, they also handle 'tax withholdings'     │   │
│  │  and 'W-2 generation' which involves SSNs. Both bank account   │   │
│  │  numbers and SSNs are PII under Section 2.1 of this policy,    │   │
│  │  triggering the encryption requirement."                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                          │
│  EXPERT ACTION:                                                         │
│                                                                          │
│  ○ Approve as-is                                                        │
│  ○ Approve with modified rationale                                      │
│  ○ Change decision to NOT APPLICABLE                                    │
│                                                                          │
│  Modified Rationale (optional):                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  [ Save & Next ]  [ Skip ]  [ Flag for Discussion ]                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Review Workflow

1. **Expert receives assessment batch** for a policy change
2. **For each assessment:**
   - Review LLM's decision and rationale
   - Compare against current BU description (shown alongside)
   - Either approve or modify
3. **Approved assessments** are saved to historical database
4. **Modified assessments** are saved with both original and corrected versions
5. **Flagged items** go to team discussion

---

## Continuous Improvement Loop

### The Feedback Mechanism

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONTINUOUS IMPROVEMENT LOOP                           │
│                                                                          │
│   Round 1: New Policy or First Assessment                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  • No historical data exists                                     │   │
│   │  • LLM reasons from first principles                            │   │
│   │  • Expert reviews and corrects as needed                        │   │
│   │  • Verified decisions saved to database ✓                       │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   Round 2: Policy Updated (months/years later)                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  • Historical data now exists (from Round 1)                    │   │
│   │  • LLM uses historical rationales as reference                  │   │
│   │  • Reasoning patterns are more consistent                       │   │
│   │  • Expert review is faster (fewer corrections needed)           │   │
│   │  • Updated decisions saved to database ✓                        │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   Round 3+: Mature System                                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  • Rich historical data across many policies and BUs            │   │
│   │  • LLM outputs are highly consistent with org patterns          │   │
│   │  • Expert review becomes validation rather than correction      │   │
│   │  • System handles new BUs and policies with good accuracy       │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### What Improves Over Time

| Aspect | Early State | Mature State |
|--------|-------------|--------------|
| Historical coverage | Sparse | Comprehensive |
| LLM consistency | Variable | Highly consistent |
| Rationale quality | Good but generic | Matches org patterns |
| Expert review time | Significant | Minimal validation |
| New BU handling | From scratch | Analogous examples available |

### Tracking Improvement

```sql
-- Query to track system improvement over time
SELECT 
    DATE_TRUNC('month', vetted_date) as month,
    COUNT(*) as total_assessments,
    SUM(CASE WHEN was_modified THEN 1 ELSE 0 END) as modified_count,
    ROUND(
        100.0 * SUM(CASE WHEN was_modified THEN 1 ELSE 0 END) / COUNT(*), 
        2
    ) as modification_rate_pct
FROM historical_applicability
GROUP BY DATE_TRUNC('month', vetted_date)
ORDER BY month;
```

Expected trend: `modification_rate_pct` decreases over time as system learns.

---

## Summary

### Key Design Decisions Recap

| Decision | Rationale |
|----------|-----------|
| **Context Engineering over RAG** | Known document relationships, bounded context, better rationale quality |
| **Simple SQL for historical lookup** | Sufficient for finding exact matches and similar examples |
| **Human-in-the-loop verification** | Quality control, builds training data, maintains accountability |
| **Historical as reference only** | BUs change; current description is authoritative |
| **Requirement-by-requirement processing** | Clear audit trail, focused reasoning per decision |

### Benefits of This Approach

1. **Simplicity:** No vector database, no embeddings, no RAG infrastructure
2. **Transparency:** Clear prompts, deterministic processing, auditable decisions
3. **Quality:** Human verification ensures accuracy
4. **Improvement:** Every review cycle improves future assessments
5. **Maintainability:** Standard database + LLM API, easy to debug and extend

### When to Revisit This Design

Consider adding RAG if:
- Historical database exceeds 10,000+ decisions
- Need cross-policy pattern analysis
- Require semantic search for ambiguous lookups
- Documents become too large for context window

Until then, this context engineering approach provides a robust, maintainable solution for policy applicability assessment.

---

## Appendix: Technology Stack

| Component | Recommended | Alternatives |
|-----------|-------------|--------------|
| Database | PostgreSQL | MySQL, SQLite (dev) |
| LLM | Claude API | OpenAI GPT-4, Azure OpenAI |
| Backend | Python 3.10+ | Node.js, Go |
| Review UI | React, Vue, or simple Flask/Django | Spreadsheet for MVP |
| Hosting | AWS, GCP, Azure | On-premise |

---

*Document prepared for technical review and implementation planning.*
