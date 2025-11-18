## 1. Overview

### What is the Agentic Framework?

The Universal Intake Platform uses an **agentic framework** - a system where autonomous AI agents collaborate to process user submissions. Each agent has:

- **Specialized Role:** Focus on a specific task (conversation, validation, compliance, extraction, etc.)
- **Decision-Making Capability:** Makes intelligent decisions based on configuration and context
- **Tool Access:** Uses specific tools (LLM clients, databases, file systems) to accomplish tasks
- **Communication Protocol:** Coordinates with other agents via events or direct calls

### Two Distinct Workflows

The platform operates through two separate workflows that serve different purposes and users:

**Workflow 1: Configuration & Setup (Admin)** - A one-time setup process where administrators or business analysts create intake configurations by defining questions, validation rules, compliance requirements, and output mappings through YAML/JSON files.

**Workflow 2: Runtime Submission (End Users)** - The ongoing operational workflow where end users submit requests through the configured intake, and the agentic system processes their submissions through all validation, compliance, and storage steps.

---

### Workflow 1: Configuration & Setup (Admin Phase)

This workflow is executed once when creating a new intake type or updating an existing one.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        ADMIN / DEVELOPER / BUSINESS ANALYST                   │
│                         Creates New Intake Configuration                      │
│                                                                               │
│  Examples: Customer Support | GenAI Ideas | HR Onboarding | Procurement     │
└───────────────────────────────────┬───────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────────────┐
        │         CREATE 6 CONFIGURATION FILES (YAML/JSON)          │
        │                                                           │
        │  1. service.yaml                                         │
        │     • Intake name, description, version                  │
        │     • UI settings, branding, messages                    │
        │     • Feature flags (compliance, duplicates, etc.)       │
        │                                                           │
        │  2. questions.yaml                                       │
        │     • Question flow and sequence                         │
        │     • Validation criteria per question                   │
        │     • Examples and help text                             │
        │     • Max follow-ups, "I don't know" handling           │
        │                                                           │
        │  3. schema.yaml                                          │
        │     • Output field definitions (39 fields, etc.)         │
        │     • Field types, required/optional                     │
        │     • Descriptions and constraints                       │
        │                                                           │
        │  4. mappings.yaml                                        │
        │     • Question → Field mappings                          │
        │     • Pattern extraction rules                           │
        │     • LLM-based extraction prompts                       │
        │     • AI-generated field instructions                    │
        │                                                           │
        │  5. compliance.yaml                                      │
        │     • Global compliance requirements                     │
        │     • Question-level policy checks                       │
        │     • Vector DB similarity thresholds                    │
        │     • Source document references                         │
        │                                                           │
        │  6. prompts.yaml                                         │
        │     • LLM system prompts                                 │
        │     • Validation prompt templates                        │
        │     • Extraction prompt templates                        │
        │     • Recommendation prompt templates                    │
        └───────────────────────┬───────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────────────┐
        │              VALIDATE CONFIGURATION FILES                  │
        │                                                           │
        │  • JSON/YAML schema validation                           │
        │  • Cross-reference checking (questions ↔ mappings)       │
        │  • Prompt template variable validation                   │
        │  • Compliance document path verification                 │
        │  • Field definition completeness check                   │
        └───────────────────────┬───────────────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────────────┐
        │         SET ENVIRONMENT VARIABLE & DEPLOY                 │
        │                                                           │
        │  INTAKE_TYPE=customer-support                            │
        │  INTAKE_TYPE=genai-ideas                                 │
        │  INTAKE_TYPE=hr-onboarding                               │
        │  INTAKE_TYPE=procurement-requests                        │
        │                                                           │
        │  Deploy to: customer-support.company.com                 │
        │             genai-intake.company.com                     │
        │             hr-onboarding.company.com                    │
        └───────────────────────┬───────────────────────────────────┘
                                │
                                ▼
                   ┌────────────────────────────┐
                   │   ✅ INTAKE READY FOR      │
                   │      END USER SUBMISSIONS  │
                   └────────────────────────────┘
                                │
                                │ Transitions to Workflow 2 ─────────►
```

**Key Points:**

- **Who**: Platform administrators, developers, business analysts
- **When**: One-time setup or when updating intake configuration
- **Output**: A fully configured intake system ready for end users
- **Flexibility**: Same codebase, different configs = different intake types
- **No Code Changes**: All customization happens through configuration files

---

### Workflow 2: Runtime Submission (End User Phase)

This workflow runs continuously once the intake is configured and deployed.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        USER SUBMISSION (Any Domain)                           │
│  • Customer Support Tickets    • GenAI Ideas         • Analytics Requests    │
│  • Automation Proposals         • HR Onboarding      • Procurement Intakes   │
│  • Bug Reports                  • Feature Requests   • Compliance Forms       │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
            ┌─────────────────────────────────────────────────────┐
            │          CONFIGURATION FILES (YAML/JSON)             │
            │  • service.yaml    • questions.yaml  • schema.yaml  │
            │  • mappings.yaml   • compliance.yaml • prompts.yaml │
            └──────────────────────┬──────────────────────────────┘
                                   │ Loaded by INTAKE_TYPE env var
                                   ▼
                        ┌──────────────────────┐
                        │  ORCHESTRATOR AGENT  │
                        │  Master Coordinator  │
                        │  • Routes requests   │
                        │  • Manages workflow  │
                        └──────────┬───────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌────────────────┐       ┌────────────────┐       ┌────────────────┐
│  CONVERSATION  │◄─────▶│   VALIDATION   │       │   COMPLIANCE   │
│     AGENT      │       │     AGENT      │       │     AGENT      │
│ • Manages Q&A  │       │ • Checks       │       │ • Policy       │
│ • Follow-ups   │       │   criteria     │       │   validation   │
│ • AI assistance│       │ • LLM checking │       │ • Vector DB    │
└────────┬───────┘       └────────┬───────┘       └────────┬───────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │ All questions complete
                                  ▼
        ┌─────────────────────────────────────────────────┐
        │            PARALLEL PROCESSING LAYER             │
        └─────────────────────────────────────────────────┘
                  │               │               │
        ┌─────────┼───────────────┼───────────────┼─────────┐
        ▼         ▼               ▼               ▼         ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│EXTRACTION│ │RECOMMEND-│ │ STORAGE  │ │  AUDIT   │ │ CHROMA   │
│  AGENT   │ │  ATION   │ │  AGENT   │ │  AGENT   │ │VECTOR DB │
│          │ │  AGENT   │ │          │ │          │ │          │
│• Maps to │ │• Suggests│ │• Persists│ │• Logs all│ │• Semantic│
│  schema  │ │  actions │ │  data    │ │  decisions│ │  search  │
│• Pattern │ │• AI      │ │• Multi   │ │• Complete│ │• Policy  │
│  matching│ │  insights│ │  format  │ │  trail   │ │  docs    │
└─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └──────────┘
      │            │            │            │
      └────────────┴────────────┴────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            OUTPUT DESTINATIONS                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  LOCAL FILES     │  │  API INTEGRATIONS│  │  DATABASES       │          │
│  │  • CSV           │  │  • Jira          │  │  • PostgreSQL    │          │
│  │  • JSON          │  │  • ServiceNow    │  │  • MongoDB       │          │
│  │  • PDF           │  │  • Custom APIs   │  │  • SQL Server    │          │
│  │  • Excel         │  │  • Webhooks      │  │  • Vector DBs    │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

**1. Orchestrator Agent** - Master coordinator that routes requests between agents, manages workflow state, and ensures proper sequencing of operations.

**2. Conversation Agent** - Manages interactive Q&A dialogue, generates follow-up questions, and provides AI-powered assistance when users need help.

**3. Validation Agent** - Checks user responses against configured criteria, performs LLM-based validation for complex requirements, and ensures data quality.

**4. Compliance Agent** - Validates submissions against organizational policies using vector database semantic matching and LLM-based reasoning.

**5. Extraction Agent** - Maps conversational data to structured schema fields using direct mappings, pattern matching, and AI-powered extraction.

**6. Recommendation Agent** - Generates AI-powered suggestions, identifies potential improvements, and provides intelligent insights based on submission context.

**7. Storage Agent** - Persists data to multiple destinations (local files, databases, APIs) based on configuration, supporting CSV, JSON, PDF, and database outputs.

**8. Audit Agent** - Maintains complete audit trail of all decisions, LLM calls, validations, and data transformations for compliance and debugging.

---