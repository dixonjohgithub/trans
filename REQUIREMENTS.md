# Wells Fargo Universal Intake Platform - Requirements Document

**Document Version:** 2.0
**Created:** 2025-11-17
**Last Updated:** 2025-11-17
**Status:** Active Development
**Owner:** Wells Fargo AI Intake Development Team

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Requirements](#business-requirements)
3. [Functional Requirements](#functional-requirements)
4. [Non-Functional Requirements](#non-functional-requirements)
5. [Technical Requirements](#technical-requirements)
6. [Architecture](#architecture)
7. [Data Requirements](#data-requirements)
8. [Security & Compliance Requirements](#security--compliance-requirements)
9. [Deployment Requirements](#deployment-requirements)
10. [Testing Requirements](#testing-requirements)
11. [Success Criteria](#success-criteria)
12. [Out of Scope](#out-of-scope)

---

## Executive Summary

### Project Objective

Transform Wells Fargo's fragmented intake processes into a unified, AI-guided conversational platform that automatically maps employee responses to structured data across multiple service types (GenAI ideas, analytics requests, automation proposals, support tickets). The configuration-driven architecture enables rapid expansion to new intake types without code changes, deploys in three modes to accommodate any environment, and costs $0-$40 annually per 500 submissions while ensuring complete audit trails.

### Use Case

Wells Fargo employees across departments use the platform to submit GenAI ideas, analytics requests, automation proposals, and support tickets through an AI-guided conversational interface that asks clarifying questions and automatically maps their responses to structured data—completing submissions in 10-15 minutes instead of hours. The system adapts to any deployment environment (air-gapped, restricted networks, or cloud-connected) and generates audit-ready forms with complete decision logs, reducing submission time by 60-70% while ensuring 100% field completion and data quality.

### Experimentation Overview

The platform serves as an experimentation testbed for production-grade AI techniques including prompt engineering with GPT-5 for contextual question generation and response validation, embeddings-based semantic similarity for duplicate detection (planned), and decision logging infrastructure that supports future exploration of RAG (Retrieval-Augmented Generation), vector databases, and autonomous agent architectures. The current implementation deliberately uses direct LLM API calls rather than agents to establish a predictable baseline, enabling Wells Fargo to measure performance improvements as more advanced techniques like multi-agent orchestration, vector-based knowledge retrieval, and hybrid RAG systems are incrementally introduced.

---

## Business Requirements

### BR-1: Multi-Service Support

**Priority:** HIGH
**Status:** Partial (1 of 4 services implemented)

The platform MUST support multiple intake service types:
- GenAI Ideas submission (✅ Implemented)
- Analytics Support requests (📋 Planned)
- Automation Intake proposals (📋 Planned)
- General Support tickets (📋 Planned)

Each service type SHALL be independently configurable without impacting other services.

### BR-2: Deployment Flexibility

**Priority:** HIGH
**Status:** Complete

The platform MUST support three deployment modes:

1. **Static Mode**
   - Pre-defined responses, no external AI APIs
   - Cost: $0/year
   - Use case: Demos, testing, air-gapped environments

2. **Ollama Mode**
   - Local open-source AI (GPT-OSS 20B)
   - Cost: $0/year
   - Use case: Restricted network environments

3. **OpenAI Mode**
   - Cloud-based GPT-5
   - Cost: ~$40/year per 500 submissions
   - Use case: Production with best AI quality

Mode switching MUST be achievable via single environment variable change without code modifications.

### BR-3: Time Savings

**Priority:** HIGH
**Status:** Complete

The platform MUST reduce submission completion time by 60-70% compared to manual form completion:
- Target: 10-15 minutes per submission (vs. 30-60 minutes manual)
- AI response time: <15 seconds per interaction

### BR-4: Data Quality

**Priority:** HIGH
**Status:** Complete

The platform MUST ensure:
- 100% field completion rate (all required fields populated)
- Automated validation of response quality
- Intelligent follow-up questions for incomplete responses (max 2 per question)

### BR-5: Cost Efficiency

**Priority:** MEDIUM
**Status:** Complete

The platform MUST maintain low operational costs:
- Static/Ollama modes: $0/year
- OpenAI mode: <$0.25 per submission
- No expensive infrastructure dependencies

### BR-6: Audit Trail

**Priority:** HIGH
**Status:** Complete

The platform MUST log all AI decisions with:
- Complete input/output context
- Timestamps and session IDs
- Token usage and execution time
- User feedback mechanism (for future quality assurance)

---

## Functional Requirements

### FR-1: Conversational Interface

**Priority:** HIGH
**Status:** Complete

#### FR-1.1: Question Flow Management
- System SHALL present questions in a structured sequence (e.g., Q1-Q10)
- System SHALL track user progress through question flow
- System SHALL allow users to review previous answers
- System SHALL provide progress indicators

#### FR-1.2: Response Validation
- System SHALL validate responses against defined criteria
- System SHALL identify missing or incomplete information
- System SHALL generate up to 2 follow-up questions per main question
- System SHALL provide clear feedback on what information is needed

#### FR-1.3: "I Don't Know" Assistance
- System SHALL detect uncertainty expressions ("I don't know", "not sure", "unclear")
- System SHALL generate contextual suggestions based on previous answers
- System SHALL offer examples relevant to the user's idea
- System SHALL allow users to skip questions they cannot answer

### FR-2: Intelligent Field Mapping

**Priority:** HIGH
**Status:** Complete

#### FR-2.1: Conversation-to-Data Mapping
- System SHALL automatically map conversational responses to structured CSV fields
- System SHALL extract implicit information (AI task, method, output) from responses
- System SHALL populate 39+ fields from 10-question conversation
- System SHALL handle missing fields gracefully

#### FR-2.2: AI-Powered Recommendations
- System SHALL generate 4 intelligent recommendations per submission:
  - Suggested technical approach
  - Suggested KPIs approach
  - Suggested build/buy/partner strategy
  - Suggested investment (timeline, people, cost)

### FR-3: Multi-Format Export

**Priority:** HIGH
**Status:** Complete

#### FR-3.1: PDF Generation
- System SHALL generate 2-page Wells Fargo branded PDF intake forms
- System SHALL include all collected data fields
- System SHALL use Wells Fargo logo and color scheme (#D71E2B, #FFCD41)
- System SHALL allow download before final submission

#### FR-3.2: CSV Export
- System SHALL append submissions to CSV file with proper escaping
- System SHALL maintain data integrity across concurrent submissions
- System SHALL support Excel/Google Sheets compatibility

### FR-4: Service Configuration Management

**Priority:** HIGH
**Status:** Partial (framework complete, 1 service configured)

#### FR-4.1: Question Configuration
- Each service SHALL have independent question configuration file
- Configuration SHALL define: question text, validation criteria, examples
- Configuration SHALL specify follow-up rules and max follow-ups

#### FR-4.2: Schema Configuration
- Each service SHALL have independent data dictionary
- Schema SHALL define: field names, types, descriptions, required flags
- Schema SHALL support both user-provided and AI-generated fields

#### FR-4.3: Mapping Configuration
- Each service SHALL have independent field mapping logic
- Mapping SHALL transform conversation responses to structured data
- Mapping SHALL support custom extraction rules per service

### FR-5: User Experience

**Priority:** HIGH
**Status:** Complete

#### FR-5.1: Landing Page
- System SHALL display service tiles for all available intake types
- System SHALL provide clear descriptions for each service
- System SHALL use Wells Fargo branding and imagery

#### FR-5.2: Accessibility
- System SHALL comply with WCAG 2.1 AA accessibility standards
- System SHALL support keyboard navigation
- System SHALL provide proper ARIA labels and semantic HTML
- System SHALL work on screen readers

#### FR-5.3: Responsive Design
- System SHALL work on desktop (1920x1080 minimum)
- System SHALL work on tablet (768px minimum)
- System SHALL work on mobile (375px minimum)

### FR-6: Decision Logging

**Priority:** HIGH
**Status:** Complete

#### FR-6.1: AI Decision Capture
- System SHALL log every AI API call with full context
- System SHALL capture: decision type, input, output, confidence
- System SHALL record token usage and execution time
- System SHALL store logs in CSV format with proper structure

#### FR-6.2: Audit Trail
- System SHALL maintain immutable decision logs
- System SHALL associate logs with user sessions
- System SHALL enable post-hoc analysis of AI decisions
- System SHALL support compliance audits

---

## Non-Functional Requirements

### NFR-1: Performance

**Priority:** HIGH
**Status:** Complete

- AI response generation: <15 seconds (95th percentile)
- Page load time: <3 seconds (initial load)
- Subsequent interactions: <2 seconds
- PDF generation: <3 seconds
- CSV append operation: <500ms

### NFR-2: Scalability

**Priority:** MEDIUM
**Status:** Complete (for current volume)

- Support 500 submissions/year initially
- CSV storage suitable for <1000 submissions
- PostgreSQL migration path available for higher volumes
- Add new service type in <1 week (configuration only)

### NFR-3: Reliability

**Priority:** HIGH
**Status:** Complete

- System uptime: 99.5% (planned)
- Graceful degradation when AI service unavailable
- Automatic retry logic for transient failures
- Session state preservation across browser refreshes

### NFR-4: Maintainability

**Priority:** MEDIUM
**Status:** Complete

- TypeScript for type safety
- Modular architecture with clear separation of concerns
- Comprehensive inline documentation
- Configuration-driven design minimizes code changes

### NFR-5: Usability

**Priority:** HIGH
**Status:** Complete

- Minimal training required (<15 minutes)
- Intuitive conversational interface
- Clear error messages and guidance
- Consistent user experience across all services

### NFR-6: Compatibility

**Priority:** MEDIUM
**Status:** Complete

- Windows 10+, macOS 11+, Linux (Ubuntu 20.04+)
- Modern browsers: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- Node.js 18+ for server deployment
- Cross-platform via cross-env package

---

## Technical Requirements

### TR-1: Technology Stack

**Priority:** HIGH
**Status:** Complete

#### TR-1.1: Core Application
- Next.js 14.2.3 (full-stack React framework)
- React 18.3.1 (UI library)
- TypeScript 5.5.4 (type-safe development)
- Node.js 18+ LTS (runtime)

#### TR-1.2: AI Integration
- OpenAI SDK 4.67.1 (GPT-5 support)
- Ollama compatible API (local AI support)
- Static mode (no external dependencies)

#### TR-1.3: Document Generation
- jsPDF 3.0.3 (PDF generation)
- jspdf-autotable 5.0.2 (table layouts)

#### TR-1.4: Testing
- Jest 30.2.0 (unit testing)
- Playwright 1.56.0 (visual regression)
- jest-axe 10.0.0 (accessibility testing)

### TR-2: AI Service Integration

**Priority:** HIGH
**Status:** Complete

#### TR-2.1: OpenAI Mode
- GPT-5 model for question generation and validation
- text-embedding-3-large for duplicate detection (planned)
- Proper API key management via environment variables
- Rate limiting and error handling

#### TR-2.2: Ollama Mode
- GPT-OSS 20B model support
- OpenAI-compatible API endpoints
- Local model server at http://localhost:11434
- Minimum 16GB RAM requirement

#### TR-2.3: Static Mode
- Pre-defined question flow
- No external API dependencies
- Hardcoded responses for testing/demos

### TR-3: Data Storage

**Priority:** HIGH
**Status:** Complete

#### TR-3.1: CSV Storage
- Main submissions: `./data/ai_intake_ideas.csv`
- Decision logs: `./data/decision_logs.csv`
- Proper CSV escaping and formatting
- Concurrent write handling

#### TR-3.2: Session Management
- In-memory session state during conversation
- Session timeout: 30 minutes
- Session IDs using UUID v4

#### TR-3.3: PostgreSQL (Optional)
- Migration path for production deployments
- Database schema design available
- Connection pooling and error handling

### TR-4: Configuration Management

**Priority:** HIGH
**Status:** Complete

#### TR-4.1: Environment Variables
- `.env.example` template provided
- Support for all three AI modes
- Corporate proxy/SSL configuration options
- Port and host binding configuration

#### TR-4.2: Question Configuration
- TypeScript configuration files
- Question criteria with validation rules
- Example responses for guidance
- Extensible for new service types

#### TR-4.3: Schema Configuration
- Markdown data dictionaries
- Field definitions with types and descriptions
- CSV column ordering and formatting rules

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER LAYER                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │         Wells Fargo Employees (Internal Users)                │  │
│  │  Desktop (Chrome/Firefox/Edge) | Tablet | Mobile              │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
└───────────────────────────┼──────────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (Next.js Frontend)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Landing    │  │ Conversation │  │    Review    │             │
│  │     Page     │─▶│   Flow UI    │─▶│     Page     │             │
│  │ (4 Services) │  │ (Chat-like)  │  │ (PDF Export) │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│         │                  │                  │                      │
│         │    React Components (TypeScript)    │                      │
│         │  - ServiceTiles  - ProgressBar      │                      │
│         │  - ChatInterface - ValidationUI     │                      │
│         └──────────────────┴──────────────────┘                      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │ API Calls (REST)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER (Next.js API Routes)               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     API Route Handlers                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │  │
│  │  │ /api/openai/    │  │  /api/data/     │  │ /api/health/ │ │  │
│  │  │ - generate-     │  │  - submit-idea  │  │ - health     │ │  │
│  │  │   question-v2   │  │  - export-form  │  │ - openai     │ │  │
│  │  │ - analyze       │  │  - check-dup    │  │              │ │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────────────┘ │  │
│  └───────────┼────────────────────┼──────────────────────────────┘  │
│              │                    │                                  │
│  ┌───────────┼────────────────────┼──────────────────────────────┐  │
│  │           │    BUSINESS LOGIC LAYER                           │  │
│  │  ┌────────▼─────────┐  ┌───────▼──────────┐  ┌────────────┐ │  │
│  │  │ Conversation     │  │  Data Mapping    │  │ Decision   │ │  │
│  │  │ Engine           │  │  Service         │  │ Logger     │ │  │
│  │  │ - Validation     │  │  - CSV Mapper    │  │ - Audit    │ │  │
│  │  │ - Follow-ups     │  │  - Recommender   │  │ - Tracking │ │  │
│  │  │ - "Don't Know"   │  │  - PDF Generator │  │            │ │  │
│  │  └────────┬─────────┘  └───────┬──────────┘  └─────┬──────┘ │  │
│  └───────────┼────────────────────┼─────────────────────┼────────┘  │
└──────────────┼────────────────────┼─────────────────────┼───────────┘
               │                    │                     │
               ▼                    ▼                     ▼
┌──────────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│    AI SERVICE        │  │  DATA STORAGE    │  │  LOGGING STORAGE   │
│      LAYER           │  │     LAYER        │  │      LAYER         │
│                      │  │                  │  │                    │
│  ┌────────────────┐ │  │  ┌────────────┐ │  │  ┌──────────────┐ │
│  │ MODE SELECTOR  │ │  │  │ CSV Files  │ │  │  │ Decision Logs│ │
│  │ ┌────────────┐ │ │  │  │ ───────────│ │  │  │ (CSV)        │ │
│  │ │ Static     │◄┼─┼──┼──│ • ideas.csv│ │  │  │ • log_id     │ │
│  │ │ (No API)   │ │ │  │  │ • data_    │ │  │  │ • timestamp  │ │
│  │ └────────────┘ │ │  │  │   dict.csv │ │  │  │ • context    │ │
│  │                │ │  │  └────────────┘ │  │  │ • response   │ │
│  │ ┌────────────┐ │ │  │       OR        │  │  │ • tokens     │ │
│  │ │ Ollama     │◄┼─┼──┼─ ┌────────────┐ │  │  └──────────────┘ │
│  │ │ (Local AI) │ │ │  │  │ PostgreSQL │ │  │                    │
│  │ │ :11434     │ │ │  │  │ • ideas    │ │  │  ┌──────────────┐ │
│  │ └────────────┘ │ │  │  │ • sessions │ │  │  │ App Logs     │ │
│  │                │ │  │  │ • logs     │ │  │  │ (./logs/)    │ │
│  │ ┌────────────┐ │ │  │  └────────────┘ │  │  │ • errors     │ │
│  │ │ OpenAI     │◄┼─┼─┐│                  │  │  │ • access     │ │
│  │ │ GPT-5 API  │ │ │ ││                  │  │  │ • debug      │ │
│  │ │ (Cloud)    │ │ │ ││                  │  │  └──────────────┘ │
│  │ └────────────┘ │ │ ││                  │  │                    │
│  └────────────────┘ │ ││                  │  └────────────────────┘
│                     │ ││                  │
│  ┌────────────────┐ │ ││                  │
│  │ LLM Functions  │ │ ││                  │
│  │ ──────────────│ │ ││                  │
│  │ • Question Gen │ │ ││                  │
│  │ • Validation   │ │ ││                  │
│  │ • Field Map    │ │ ││                  │
│  │ • Recommender  │ │ ││                  │
│  │ • Embeddings   │ │ ││  (Planned)       │
│  └────────────────┘ │ ││                  │
└─────────────────────┘ │└──────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │   EXTERNAL SERVICES    │
           │   ─────────────────    │
           │   • api.openai.com     │
           │     (GPT-5, Embeddings)│
           │   • Corporate Proxy    │
           │     (if behind firewall)│
           └────────────────────────┘
```

### Configuration Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    CONFIGURATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LAYER 1: Service Configuration                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │ GenAI    │  │Analytics │  │Automation│  │ Support │ │  │
│  │  │ Ideas    │  │ Support  │  │ Intake   │  │ Requests│ │  │
│  │  │ (Active) │  │(Planned) │  │(Planned) │  │(Planned)│ │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │  │
│  └───────┼─────────────┼─────────────┼──────────────┼───────┘  │
│          │             │             │              │           │
│  ┌───────┼─────────────┼─────────────┼──────────────┼───────┐  │
│  │  LAYER 2: Question Flow Configuration                    │  │
│  │  ┌────▼─────────────▼─────────────▼──────────────▼────┐ │  │
│  │  │ questionCriteria_[service].ts                       │ │  │
│  │  │ • Question sequence (Q1-Q10)                        │ │  │
│  │  │ • Validation criteria arrays                        │ │  │
│  │  │ • Example responses                                 │ │  │
│  │  │ • Follow-up rules (max 2)                           │ │  │
│  │  │ • "I don't know" triggers                           │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────┬───────────────────────────┘  │
│                                 │                               │
│  ┌──────────────────────────────┼───────────────────────────┐  │
│  │  LAYER 3: Data Schema Configuration                      │  │
│  │  ┌──────────────────────────▼────────────────────────┐  │  │
│  │  │ data_dictionary_[service].md                       │  │  │
│  │  │ • Field names, types, descriptions                 │  │  │
│  │  │ • CSV column structure (39+ fields)                │  │  │
│  │  │ • Required vs. optional flags                      │  │  │
│  │  │ • AI-generated field markers                       │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  │  ┌───────────────────────────────────────────────────┐   │  │
│  │  │ csvMapper_[service].ts                             │   │  │
│  │  │ • Conversation → Structured data mapping           │   │  │
│  │  │ • Field extraction logic                           │   │  │
│  │  │ • AI recommendation generation                     │   │  │
│  │  └───────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────┬───────────────────────────┘  │
│                                 │                               │
│  ┌──────────────────────────────┼───────────────────────────┐  │
│  │  LAYER 4: Deployment Mode Configuration                  │  │
│  │  ┌──────────────────────────▼────────────────────────┐  │  │
│  │  │ .env (Environment Variables)                       │  │  │
│  │  │ NEXT_PUBLIC_AI_MODE=static|openai|ollama          │  │  │
│  │  │ ────────────────────────────────────────────────  │  │  │
│  │  │ • OPENAI_API_KEY (if openai mode)                 │  │  │
│  │  │ • OLLAMA_BASE_URL (if ollama mode)                │  │  │
│  │  │ • APP_PORT, HOST                                  │  │  │
│  │  │ • Performance tuning flags                        │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION FLOW                     │
└──────────────────────────────────────────────────────────────────┘

1. USER ENTERS PLATFORM
   │
   ▼
┌─────────────────────┐
│  Landing Page       │  User sees 4 service tiles
│  (4 Service Tiles)  │  Selects one (e.g., GenAI Ideas)
└──────────┬──────────┘
           │
           ▼
2. SERVICE SELECTION
   │
   ▼
┌─────────────────────┐
│  Load Service Config│  System loads:
│  ─────────────────  │  • questionCriteria_genai.ts
│  • Questions        │  • data_dictionary_genai.md
│  • Schema           │  • csvMapper_genai.ts
│  • Validation Rules │
└──────────┬──────────┘
           │
           ▼
3. CONVERSATION BEGINS
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│  QUESTION-ANSWER CYCLE (Repeat Q1-Q10)                      │
│                                                              │
│  ┌──────────────────┐                                       │
│  │ Present Question │  System: "What is the business        │
│  │     (Q1-Q10)     │           problem you want to solve?" │
│  └────────┬─────────┘                                       │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │ User Responds    │  User: "Customer service agents       │
│  │                  │         spend too much time..."       │
│  └────────┬─────────┘                                       │
│           │                                                  │
│           ▼                                                  │
│  ┌──────────────────┐                                       │
│  │ Uncertainty?     │  Check: "I don't know" / "not sure"?  │
│  │                  │                                        │
│  └────────┬─────────┘                                       │
│           │                                                  │
│      ┌────┴────┐                                            │
│      │         │                                            │
│     YES       NO                                            │
│      │         │                                            │
│      ▼         ▼                                            │
│  ┌──────┐  ┌──────────────────┐                            │
│  │ AI   │  │ Validate Against │                            │
│  │ Help │  │ Criteria         │                            │
│  │      │  │ • Complete?      │                            │
│  └──┬───┘  │ • Missing info?  │                            │
│     │      └────────┬─────────┘                            │
│     │               │                                       │
│     │          ┌────┴────┐                                 │
│     │          │         │                                 │
│     │        PASS      FAIL                                │
│     │          │         │                                 │
│     │          │         ▼                                 │
│     │          │  ┌────────────────┐                       │
│     │          │  │ Generate       │  Max 2 follow-ups     │
│     │          │  │ Follow-up Q    │  per main question    │
│     │          │  └───────┬────────┘                       │
│     │          │          │                                │
│     └──────────┴──────────┘                                │
│                │                                            │
│                ▼                                            │
│  ┌──────────────────┐                                      │
│  │ Move to Next Q   │  Repeat for Q2, Q3, ..., Q10         │
│  └──────────────────┘                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
           │
           ▼
4. CONVERSATION COMPLETE (All Q1-Q10 answered)
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│  DATA PROCESSING                                            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Step 1: Intelligent Field Mapping (LLM)              │ │
│  │ ────────────────────────────────────────────────     │ │
│  │ Input: Full conversation history (Q1-Q10)            │ │
│  │ Process: LLM analyzes and maps to 39 CSV fields     │ │
│  │ Output: Structured data object                       │ │
│  │                                                       │ │
│  │ Example Mapping:                                     │ │
│  │ Q2 response → problem_statement                      │ │
│  │ Q3 response → ai_solution_approach                   │ │
│  │ Q4 response → core_kpis, efficiency_metrics          │ │
│  │ Extracted   → ai_task, ai_method, ai_output          │ │
│  └────────────────────────┬─────────────────────────────┘ │
│                           │                               │
│                           ▼                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Step 2: AI Recommendations (LLM)                     │ │
│  │ ────────────────────────────────────────────────     │ │
│  │ Generate 4 intelligent suggestions:                  │ │
│  │ • suggested_approach (Build/Buy/Partner)             │ │
│  │ • suggested_kpis_approach                            │ │
│  │ • suggested_build_buy_approach                       │ │
│  │ • suggested_investment_approach                      │ │
│  └────────────────────────┬─────────────────────────────┘ │
│                           │                               │
│                           ▼                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Step 3: Decision Logging                             │ │
│  │ ────────────────────────────────────────────────     │ │
│  │ Log all AI decisions to decision_logs.csv:           │ │
│  │ • Field mapping decisions                            │ │
│  │ • Recommendation generation                          │ │
│  │ • Token usage, execution time                        │ │
│  │ • Input/output context                               │ │
│  └────────────────────────┬─────────────────────────────┘ │
└────────────────────────────┼──────────────────────────────┘
                            │
                            ▼
5. REVIEW & EXPORT
   │
   ▼
┌─────────────────────┐
│  Review Page        │  User sees all collected data
│  ─────────────      │
│  • 39 fields filled │  Options:
│  • AI suggestions   │  1. Download PDF (Wells Fargo form)
│  • Edit if needed   │  2. Submit to CSV
└──────────┬──────────┘
           │
      ┌────┴────┐
      │         │
  DOWNLOAD    SUBMIT
      │         │
      ▼         ▼
┌──────────┐ ┌────────────────┐
│ PDF Gen  │ │ Append to CSV  │
│ (jsPDF)  │ │ (ideas.csv)    │
└──────────┘ └────────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Confirmation  │
              │ & Thank You   │
              └───────────────┘
```

---

## Data Requirements

### DR-1: Data Schema

**Priority:** HIGH
**Status:** Complete (GenAI service)

#### DR-1.1: GenAI Ideas Schema
The system SHALL support a 39-field CSV schema organized as:

**Identity Fields (4):**
- opportunity_id (UUID)
- opportunity_name (text)
- opportunity_type (classification)
- owner_sponsor (text)

**Problem & Solution Fields (8):**
- problem_statement
- current_process_issues
- ai_solution_approach
- improvement_description
- ai_task (AI-extracted)
- ai_method (AI-extracted)
- ai_output (AI-extracted)
- suggested_approach (AI-generated)

**Business Impact Fields (3):**
- core_kpis
- efficiency_metrics
- suggested_kpis_approach (AI-generated)

**Feasibility Fields (6):**
- can_we_execute
- can_we_execute_rationale
- data_availability
- data_availability_rationale
- integration_capability
- integration_capability_rationale

**Build/Buy Fields (4):**
- overall_approach
- approach_rationale
- hybrid_approach
- suggested_build_buy_approach (AI-generated)

**Investment Fields (4):**
- investment_people
- investment_cost
- investment_timeline
- suggested_investment_approach (AI-generated)

**Risk Fields (2):**
- risks_list
- mitigation_strategies

**Metadata Fields (8):**
- submission_date
- submission_status
- similarity_scores (JSON)
- conversation_history (JSON)
- decision_log_ids (JSON array)
- form_version
- last_modified
- other_details

### DR-2: Decision Log Schema

**Priority:** HIGH
**Status:** Complete

Decision logs SHALL capture:
- log_id (UUID)
- timestamp (ISO 8601)
- session_id
- decision_type (enum: question_generation, validation, classification, field_mapping, recommendation)
- input_context (JSON)
- llm_response (text)
- confidence_score (0-1)
- token_usage (JSON: prompt, completion, total)
- execution_time_ms
- user_feedback (nullable)

### DR-3: Data Retention

**Priority:** MEDIUM
**Status:** Defined

- Idea submissions: Retained indefinitely
- Decision logs: 1 year minimum (audit compliance)
- Session data: Auto-expire after 24 hours
- CSV files: Daily backups recommended

### DR-4: Data Privacy

**Priority:** HIGH
**Status:** Complete

- No PII required for submissions
- User IDs can be Wells Fargo employee IDs
- All data stored on internal infrastructure only
- No data sent to external services except OpenAI API (if using OpenAI mode)

---

## Security & Compliance Requirements

### SCR-1: Authentication & Authorization

**Priority:** MEDIUM
**Status:** Out of scope for MVP (planned for Phase 3)

- System SHALL be accessible only from Wells Fargo internal network
- Future: Integration with Wells Fargo SSO/Active Directory
- Future: Role-based access control (RBAC)

### SCR-2: API Key Security

**Priority:** HIGH
**Status:** Complete

- API keys MUST be stored in environment variables only
- API keys MUST NOT be committed to version control
- Separate keys MUST be used for dev/staging/production
- Keys MUST be rotated quarterly (recommended)

### SCR-3: Data Encryption

**Priority:** HIGH
**Status:** Complete

- All web traffic MUST use HTTPS (TLS 1.2+ minimum)
- API communication MUST use encrypted channels
- CSV files MAY be encrypted at rest (optional for MVP)

### SCR-4: Audit Trail

**Priority:** HIGH
**Status:** Complete

- System MUST log all AI decisions with full context
- Logs MUST be immutable once written
- Logs MUST include timestamps, user sessions, and execution details
- Logs MUST support compliance audits

### SCR-5: Corporate Network Compliance

**Priority:** HIGH
**Status:** Complete

- System MUST support corporate proxy configurations
- System MUST handle self-signed SSL certificates
- System MUST work behind Wells Fargo firewall
- Configuration options provided via NODE_TLS_REJECT_UNAUTHORIZED and NODE_EXTRA_CA_CERTS

### SCR-6: Data Sovereignty

**Priority:** MEDIUM
**Status:** Partial

- CSV storage keeps all data on-premises (✅)
- OpenAI mode sends conversation data to external API (⚠️)
- Ollama/Static modes keep all data internal (✅)
- Future: Enterprise OpenAI agreement with data residency guarantees

---

## Deployment Requirements

### DEP-1: Environment Requirements

**Priority:** HIGH
**Status:** Complete

#### DEP-1.1: Development Environment
- Node.js 18+ LTS
- 8GB RAM minimum
- 500MB disk space (excluding node_modules)
- Modern browser for testing

#### DEP-1.2: Production Environment
- Wells Fargo internal server/VM (Windows Server 2019+ or Ubuntu 20.04+)
- 8GB RAM minimum (16GB recommended)
- 50GB disk space
- Port 3073 (or 443 for production) accessible internally
- Internal DNS entry (recommended)

#### DEP-1.3: AI Mode Requirements

**Static Mode:**
- No additional requirements

**Ollama Mode:**
- Ollama installation
- GPT-OSS 20B model (~12GB download)
- 16GB RAM minimum
- Local model server running

**OpenAI Mode:**
- OpenAI API key
- Internet access to api.openai.com
- Corporate proxy configuration (if applicable)

### DEP-2: Network Requirements

**Priority:** HIGH
**Status:** Complete

- Internal firewall rules: Allow inbound on port 3073 (or configured port)
- Outbound access to api.openai.com (if using OpenAI mode)
- DNS resolution for internal access
- Support for corporate proxy (if applicable)

### DEP-3: Deployment Process

**Priority:** MEDIUM
**Status:** Documented

1. Copy application files to server
2. Create `.env` file from template
3. Run `npm install`
4. Run `npm run build`
5. Start with `npm start` or PM2
6. Configure firewall rules
7. Test from internal network
8. Set up monitoring

### DEP-4: Monitoring & Maintenance

**Priority:** MEDIUM
**Status:** Defined

- Health check endpoint: `/api/health`
- OpenAI health check: `/api/health/openai` (if applicable)
- Log rotation for `./logs/` directory
- Daily backup of `./data/` directory
- Monthly dependency updates
- Quarterly security reviews

---

## Testing Requirements

### TEST-1: Unit Testing

**Priority:** HIGH
**Status:** Complete

- Component tests using Jest and React Testing Library
- 22 tests passing with 100% component coverage
- Test coverage for all critical business logic
- Mock external dependencies (OpenAI API, file system)

### TEST-2: Accessibility Testing

**Priority:** HIGH
**Status:** Complete

- Automated accessibility testing with jest-axe
- 11 tests verifying WCAG 2.1 AA compliance
- Manual screen reader testing (recommended)
- Keyboard navigation verification

### TEST-3: Visual Regression Testing

**Priority:** MEDIUM
**Status:** Complete

- Playwright visual regression tests
- 8 baseline snapshots captured
- Coverage: Landing page, conversation flow, review page
- Responsive views tested (desktop, tablet, mobile)

### TEST-4: Integration Testing

**Priority:** HIGH
**Status:** Partial

- End-to-end conversation flow testing (manual)
- CSV append operations (manual)
- PDF generation verification (manual)
- Future: Automated E2E tests with Cypress/Playwright

### TEST-5: Performance Testing

**Priority:** MEDIUM
**Status:** Defined

- AI response time benchmarking
- Page load time testing
- Concurrent user simulation (planned)
- Token usage monitoring

### TEST-6: Security Testing

**Priority:** HIGH
**Status:** Defined

- API key exposure checks (automated via lint rules)
- XSS/injection vulnerability testing (planned)
- SSL/TLS configuration verification
- Corporate network penetration testing (coordinate with Wells Fargo IT Security)

---

## Success Criteria

### SC-1: Functional Success

**Status:** ✅ ACHIEVED (for GenAI service)

- [x] Conversational flow guides user through all required questions
- [x] Response validation with intelligent follow-ups (max 2 per question)
- [x] "I Don't Know" assistance generates contextual suggestions
- [x] 39 fields automatically populated from conversation
- [x] AI-powered recommendations generated (4 per submission)
- [x] PDF generation produces Wells Fargo branded forms
- [x] CSV export appends data with proper formatting
- [x] Decision logging captures all AI interactions

### SC-2: Performance Success

**Status:** ✅ ACHIEVED

- [x] AI response time <15 seconds (optimized to 10-15s)
- [x] Page load time <3 seconds
- [x] PDF generation <3 seconds
- [x] 60-70% reduction in submission time vs. manual forms

### SC-3: Quality Success

**Status:** ✅ ACHIEVED

- [x] 100% field completion rate (all required fields populated)
- [x] WCAG 2.1 AA accessibility compliance
- [x] Cross-platform compatibility (Windows/Mac/Linux)
- [x] Cross-browser compatibility (Chrome/Firefox/Safari/Edge)

### SC-4: Cost Success

**Status:** ✅ ACHIEVED

- [x] Static mode: $0/year operational cost
- [x] Ollama mode: $0/year operational cost
- [x] OpenAI mode: <$0.25 per submission ($0.03-$0.25 range)
- [x] No expensive infrastructure dependencies

### SC-5: Scalability Success

**Status:** ✅ ACHIEVED

- [x] Configuration-driven architecture supports multiple service types
- [x] Add new service in <1 week (configuration only)
- [x] CSV storage suitable for 500-1000 submissions
- [x] PostgreSQL migration path available for higher volumes

### SC-6: User Experience Success

**Status:** ✅ ACHIEVED (pending user feedback)

- [x] Intuitive conversational interface
- [x] Clear progress indicators
- [x] Helpful AI guidance for uncertain users
- [x] Minimal training required (<15 minutes)
- [ ] User satisfaction >80% (to be measured post-deployment)

---

## Out of Scope

The following items are explicitly OUT OF SCOPE for the current phase:

### Phase 1 Exclusions

- ❌ Duplicate detection using embeddings (Task 3.0 - Phase 2)
- ❌ Analytics Support service implementation (Phase 2)
- ❌ Automation Intake service implementation (Phase 2)
- ❌ Support Request service implementation (Phase 2)
- ❌ Admin dashboard with analytics (Phase 3)
- ❌ User authentication/SSO integration (Phase 3)
- ❌ PostgreSQL database migration (Optional - as needed)
- ❌ Docker containerization (Optional - not required)
- ❌ Word (.docx) export (PDF only for MVP)
- ❌ Mobile applications (Web-based only)
- ❌ Real-time collaboration features
- ❌ External system integrations (beyond CSV/DB)
- ❌ Multi-language support (English only)
- ❌ Advanced analytics/reporting dashboards
- ❌ Automated email notifications
- ❌ Version control for submissions (edit history)
- ❌ Workflow/approval processes

### Technology Exploration (Future)

Items planned for future experimentation:
- RAG (Retrieval-Augmented Generation) for knowledge retrieval
- Vector databases (Pinecone, Weaviate) for semantic search
- Autonomous agent architectures for complex workflows
- Multi-agent orchestration systems
- Advanced prompt chaining and optimization
- Fine-tuned models for Wells Fargo specific use cases

---

## Appendix A: Glossary

- **AI Mode**: Deployment configuration (Static, Ollama, OpenAI)
- **Criteria Validation**: Checking if response meets defined requirements
- **CSV Mapper**: Service that transforms conversation to structured data
- **Decision Log**: Audit record of AI decision with full context
- **Field Mapping**: Process of extracting data from conversation to CSV fields
- **Follow-up Question**: AI-generated clarifying question (max 2 per main question)
- **LLM**: Large Language Model (e.g., GPT-5)
- **Ollama**: Local AI model server for open-source models
- **Question Criteria**: Validation rules defining what information is needed
- **Service Tile**: UI entry point for specific intake type
- **Static Mode**: No-AI mode using pre-defined responses

---

## Appendix B: Reference Documents

- `projectplan.md` - Development roadmap and task tracking
- `approach.md` - Complete technical approach (1210 lines)
- `README.md` - Setup and deployment guide
- `PLATFORM_OBJECTIVE.md` - High-level project objective
- `data/data_dictionary.md` - 39-field CSV schema definition
- `src/config/questionCriteria.ts` - Question configuration
- `tasks/prd-genai-idea-assistant.md` - Detailed Product Requirements

---

**Document Status:** APPROVED
**Next Review Date:** 2026-01-15
**Version History:**
- v1.0 (2025-10-14): Initial draft
- v2.0 (2025-11-17): Updated with platform vision and architecture diagrams

---

*End of Requirements Document*
