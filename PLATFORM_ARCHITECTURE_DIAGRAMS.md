# CT Data Intake Platform - Architecture Diagrams

This document provides visual representations of the CT Data Intake Platform architecture, showing how it functions as an umbrella platform supporting multiple customizable intake applications.

---

## 1. Platform Overview (Umbrella Architecture)

**Key Concept:** Single codebase deployed multiple times, each deployment configured for a specific intake type.

The CT Data Intake Platform serves as a centralized umbrella that houses shared infrastructure while enabling independent intake applications to operate with their own configurations.

```mermaid
flowchart TB
    subgraph PLATFORM["CT Data Intake Platform"]
        direction TB

        subgraph SHARED["Shared Infrastructure"]
            direction LR
            CODEBASE["Single Codebase<br/>Next.js + TypeScript"]
            AGENTS["8 Shared Agents<br/>LangGraph Powered"]
            CHROMA[("Chroma Vector DB<br/>Semantic Search")]
        end

        subgraph INTAKES["Intake Applications (Separately Deployed)"]
            direction LR
            CS["Customer<br/>Support"]
            GI["Gen AI<br/>Intake"]
            AR["Analytics<br/>Requests"]
            EVM["EVM<br/>Pipeline"]
            FG["Federated<br/>Graph"]
        end

        SHARED --> INTAKES
    end

    USER((CT User)) --> PLATFORM
    PLATFORM --> OUTPUT[("Outputs: CSV, PDF, API, DB")]

    style PLATFORM fill:#1a1a2e,stroke:#D71E2B,stroke-width:4px,color:#fff
    style SHARED fill:#16213e,stroke:#FFCD41,stroke-width:2px,color:#fff
    style INTAKES fill:#0f3460,stroke:#FFCD41,stroke-width:2px,color:#fff
```

### What This Shows:
- **Umbrella Platform:** The outer container represents the CT Data Intake Platform
- **Shared Infrastructure:** Single codebase, 8 agents, and vector database serve all intakes
- **Multiple Intake Apps:** Each deployment (Customer Support, Gen AI, Analytics, etc.) runs independently
- **Unified Outputs:** All intakes produce standardized outputs (CSV, PDF, API calls, database records)

---

## 2. Configuration Customization Per Intake

**Key Concept:** No code changes required to add new intake types. Everything is configured via 6 YAML files.

Each intake application loads its own set of configuration files at startup, determined by the `INTAKE_TYPE` environment variable.

```mermaid
flowchart LR
    subgraph CONFIG["6 Configuration Files<br/>(Customizable Per Intake)"]
        direction TB
        SVC["service.yaml<br/>Identity & Settings"]
        QST["questions.yaml<br/>Question Flow & Criteria"]
        SCH["schema.yaml<br/>Data Field Definitions"]
        MAP["mappings.yaml<br/>Field Mapping Rules"]
        CMP["compliance.yaml<br/>Validation & Policy Rules"]
        PRM["prompts.yaml<br/>LLM Prompt Templates"]
    end

    subgraph INTAKE1["Gen AI Intake<br/>genai-intake.ct.wellsfargo.com"]
        C1["10 Questions<br/>39 Data Fields<br/>Full Compliance Check<br/>AI Recommendations"]
    end

    subgraph INTAKE2["Customer Support<br/>support.ct.wellsfargo.com"]
        C2["6 Questions<br/>18 Data Fields<br/>Basic Validation<br/>Ticket Routing"]
    end

    subgraph INTAKE3["Analytics Requests<br/>analytics.ct.wellsfargo.com"]
        C3["8 Questions<br/>25 Data Fields<br/>Data Governance<br/>Cost Estimation"]
    end

    subgraph INTAKE4["EVM Pipeline<br/>evm.ct.wellsfargo.com"]
        C4["12 Questions<br/>45 Data Fields<br/>Pipeline Validation<br/>Reuse Detection"]
    end

    CONFIG -->|"INTAKE_TYPE=genai-ideas"| INTAKE1
    CONFIG -->|"INTAKE_TYPE=support-tickets"| INTAKE2
    CONFIG -->|"INTAKE_TYPE=analytics"| INTAKE3
    CONFIG -->|"INTAKE_TYPE=evm-pipeline"| INTAKE4

    style CONFIG fill:#2d4059,stroke:#FFCD41,stroke-width:2px,color:#fff
    style INTAKE1 fill:#1a1a2e,stroke:#D71E2B,stroke-width:2px,color:#fff
    style INTAKE2 fill:#1a1a2e,stroke:#D71E2B,stroke-width:2px,color:#fff
    style INTAKE3 fill:#1a1a2e,stroke:#D71E2B,stroke-width:2px,color:#fff
    style INTAKE4 fill:#1a1a2e,stroke:#D71E2B,stroke-width:2px,color:#fff
```

### Configuration Files Explained:

| File | Purpose | Example Customization |
|------|---------|----------------------|
| `service.yaml` | Service identity, branding, URLs | Logo, colors, deployment URL |
| `questions.yaml` | Question sequence and criteria | Number of questions, validation rules |
| `schema.yaml` | Data field definitions | Field names, types, required flags |
| `mappings.yaml` | Conversation-to-data mapping | How answers map to output fields |
| `compliance.yaml` | Policy and validation rules | Security checks, data governance |
| `prompts.yaml` | LLM prompt templates | Custom AI behavior per intake |

### Adding a New Intake Type:

1. Create a new folder: `/config/services/{new-intake-type}/`
2. Copy and customize the 6 YAML files
3. Deploy with `INTAKE_TYPE=new-intake-type`
4. No code changes required!

---

## 3. Agent Architecture & End-to-End Flow

**Key Concept:** 8 specialized agents work together, each configurable via the intake's configuration files.

The agents are organized into layers, each responsible for a specific part of the intake workflow.

```mermaid
flowchart TD
    USER((User)) --> |"1. Start Intake"| ORCH

    subgraph AGENTS["8 Shared Agents (Configuration-Driven via LangGraph)"]
        direction TB

        subgraph LAYER1["Orchestration Layer"]
            ORCH["Orchestrator Agent<br/>Routes & Coordinates Workflow"]
        end

        subgraph LAYER2["Conversation Layer"]
            CONV["Conversation Agent<br/>Dynamic Q&A Management"]
            VAL["Validation Agent<br/>Response Criteria Checking"]
        end

        subgraph LAYER3["Compliance Layer"]
            COMP["Compliance Agent<br/>Policy & Requirement Validation<br/>(Chroma Vector DB)"]
        end

        subgraph LAYER4["Processing Layer"]
            EXT["Extraction Agent<br/>Conversation to Data Mapping"]
            REC["Recommendation Agent<br/>AI-Powered Suggestions"]
        end

        subgraph LAYER5["Persistence Layer"]
            STOR["Storage Agent<br/>Multi-Format Output"]
            AUD["Audit Agent<br/>Complete Decision Logging"]
        end
    end

    ORCH --> |"2. Start Conversation"| CONV
    CONV <--> |"3. Validate Responses"| VAL
    VAL --> |"4. Check Compliance"| COMP
    COMP --> |"5. Report Status"| ORCH
    ORCH --> |"6. Process Data"| EXT
    ORCH --> |"6. Generate Suggestions"| REC
    EXT --> |"7. Save"| STOR
    REC --> STOR
    STOR --> |"8. Log"| AUD

    AUD --> |"9. Complete"| OUTPUT

    subgraph OUTPUT["Output Destinations"]
        direction LR
        CSV["CSV Files"]
        PDF["PDF Forms"]
        API["External APIs"]
        DB[("Databases")]
    end

    style AGENTS fill:#0f3460,stroke:#FFCD41,stroke-width:3px,color:#fff
    style LAYER1 fill:#1a1a2e,stroke:#D71E2B,stroke-width:2px,color:#fff
    style LAYER2 fill:#1a1a2e,stroke:#333,stroke-width:1px,color:#fff
    style LAYER3 fill:#1a1a2e,stroke:#333,stroke-width:1px,color:#fff
    style LAYER4 fill:#1a1a2e,stroke:#333,stroke-width:1px,color:#fff
    style LAYER5 fill:#1a1a2e,stroke:#333,stroke-width:1px,color:#fff
    style OUTPUT fill:#2d4059,stroke:#FFCD41,stroke-width:2px,color:#fff
```

### Agent Responsibilities:

| Layer | Agent | Responsibility | Configured By |
|-------|-------|----------------|---------------|
| Orchestration | **Orchestrator** | Routes requests, coordinates workflow | `service.yaml` |
| Conversation | **Conversation** | Manages dynamic Q&A dialogue | `questions.yaml`, `prompts.yaml` |
| Conversation | **Validation** | Checks response criteria | `questions.yaml` |
| Compliance | **Compliance** | Validates against policies | `compliance.yaml` |
| Processing | **Extraction** | Maps conversation to data fields | `mappings.yaml`, `schema.yaml` |
| Processing | **Recommendation** | Generates AI suggestions | `prompts.yaml` |
| Persistence | **Storage** | Saves to CSV, PDF, DB, APIs | `schema.yaml` |
| Persistence | **Audit** | Logs all decisions for compliance | `service.yaml` |

### End-to-End Flow:

1. **User Starts:** Selects intake type, begins submission
2. **Conversation:** Agent asks questions based on `questions.yaml`
3. **Validation:** Each response validated against criteria
4. **Compliance:** Policies checked via Chroma vector DB
5. **Orchestration:** Status reported, workflow continues
6. **Processing:** Extraction and Recommendation run in parallel
7. **Persistence:** Data saved to configured outputs
8. **Audit:** Complete decision trail logged
9. **Complete:** User receives confirmation and outputs

---

## Summary: Why This Architecture?

| Benefit | How It's Achieved |
|---------|-------------------|
| **Speed** | Reduce request-to-approval from weeks to days/hours |
| **Reusability** | Single codebase, multiple deployments |
| **No Code Changes** | 6 YAML files configure everything |
| **Governance** | Built-in compliance validation and audit trails |
| **Flexibility** | Each intake customized independently |
| **Visibility** | Unified dashboard across all CT initiatives |

---

## Related Documentation

- [Agentic Architecture Details](../AGENTIC_ARCHITECTURE.md) - Deep dive into agent implementation
- [Requirements Specification](../REQUIREMENTS.md) - Complete technical requirements
- [Project Plan](../projectplan.md) - Implementation status and roadmap
