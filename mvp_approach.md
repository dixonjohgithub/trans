# AI-Powered GenAI Idea Assistant: Technical Approach & Implementation

**Document Version:** 1.0
**Created:** October 2025
**Author:** AI Intake Development Team
**Status:** Prototype/MVP Implementation

---

## Executive Summary

The **AI-Powered GenAI Idea Assistant** is a web application that streamlines the GenAI idea submission process using conversational AI. This document outlines the technical approach, complete technology stack, and requirements for deploying the prototype in other Wells Fargo environments.

### Solution Type
**Prompt Engineering + Context Engineering Approach**

This prototype leverages **direct Large Language Model (LLM) API calls** with carefully crafted prompts and conversation history management. It is NOT an autonomous agent-based system, but rather a controlled, predictable application that uses AI for specific, well-defined tasks.

**Critical Feature**: The prototype includes **three deployment modes** to work in different environments:

- **Static Mode**: No AI, no external APIs, $0 cost (immediate deployment)
- **Ollama Mode**: Local AI (gpt-oss:20b), no external APIs, $0 cost (2-3 day setup)
- **OpenAI Mode**: Cloud AI (GPT-5), requires OpenAI API, $250-$1K/year (2-4 week setup)

This flexibility means stakeholders can start with Static mode immediately and upgrade to AI-powered modes when approvals are obtained.

---

## Table of Contents

1. [Solution Overview](#solution-overview)
2. [Technical Approach](#technical-approach)
3. [Complete Technology Stack](#complete-technology-stack)
4. [Architecture](#architecture)
5. [Deployment Requirements](#deployment-requirements)
6. [Access & Resource Requirements](#access--resource-requirements)
7. [Configuration Guide](#configuration-guide)
8. [Cost Considerations](#cost-considerations)
9. [Security & Compliance](#security--compliance)

---

## Solution Overview

### What It Does

The AI Intake Assistant provides:

1. **Conversational Question Flow**: Guides users through 10 structured questions to collect GenAI idea details
2. **Intelligent Follow-ups**: Uses AI to generate contextual follow-up questions when responses need clarification (max 2 per question)
3. **"I Don't Know" Assistance**: When users say "I don't know" or express uncertainty, the AI generates contextual suggestions based on previous answers to help them respond
4. **Intelligent Field Mapping**: Uses LLM to automatically map conversation responses to correct CSV fields (39 fields)
5. **AI Recommendations**: Generates AI-powered recommendations for solution approach, timeline, team size, and cost
6. **PDF Form Generation**: Auto-generates Wells Fargo 2-page intake forms in PDF format
7. **CSV Data Storage**: Saves submissions to CSV files for easy viewing and import into Excel/Google Sheets
8. **Decision Logging**: Complete audit trail of all AI decisions for transparency

**Note**: Duplicate detection using embeddings is planned for a future phase (Task 3.0) and is NOT currently implemented.

### Multiple Deployment Modes

The prototype supports **three deployment modes** to accommodate different environments and constraints:

| Mode | Description | Use Case | External Dependencies |
|------|-------------|----------|----------------------|
| **Static** | Pre-defined responses, no AI API calls | Demo, testing, offline environments | None - fully self-contained |
| **OpenAI** | Cloud-based GPT-5 via OpenAI API | Production with OpenAI access | OpenAI API key + internet |
| **Ollama (GPT-OSS)** | Local open-source model (gpt-oss:20b) | Environments without external API access | Local Ollama installation |

**Key Benefit**: The same application code supports all three modes - just change the `NEXT_PUBLIC_AI_MODE` environment variable. This allows deployment in restricted environments or for testing without API costs.

### Key Metrics & Features

- **Average Completion Time**: 10-15 seconds per AI response (with optimizations)
- **Question Sequence**: Static 10-question flow (Q1-Q10)
- **Follow-up Limit**: Maximum 2 follow-ups per question
- **"I Don't Know" Support**: AI generates contextual suggestions when users are uncertain
- **CSV Fields Mapped**: 39 fields automatically populated from conversation
- **AI Recommendations**: 4 intelligent suggestions per submission (approach, timeline, team, cost)
- **User Interface**: WCAG 2.1 AA accessible, mobile-responsive
- **Data Format**: CSV export compatible with Excel/Google Sheets
- **PDF Generation**: 2-page intake form

---

## Technical Approach

### 1. Prompt Engineering

The core of this solution is **careful prompt design** for each AI interaction:

#### Question Generation (Follow-ups)
```
System Role: "You are helping collect information for a GenAI idea.
Generate a follow-up question based on the context provided."

Context Provided:
- Previous Q&A history (last 6 messages for performance)
- Current question criteria (what we need to know)
- User's incomplete response
- Missing criteria identified

Output: Natural, contextual follow-up question (1-2 sentences)
```

#### Criteria Validation
```
System Role: "Evaluate if the user's response meets all specified criteria."

Context Provided:
- The question asked
- User's response
- Required criteria checklist
- Example of good response

Output: JSON with met/missing criteria and reasoning
```

#### Intelligent Field Mapping
```
System Role: "You are a data mapping expert. Analyze the conversation and
extract information to populate CSV fields."

Context Provided:
- Data dictionary (39 CSV field definitions)
- Complete conversation history
- User's responses to all 10 questions

Output: JSON mapping user responses to correct CSV fields (e.g.,
"opportunity_name", "problem_statement", "ai_solution_approach", etc.)
```

#### "I Don't Know" AI Assistance
```
System Role: "Help the user by generating contextual suggestions based on their
previous answers."

Triggered When User Says:
- "I don't know"
- "Not sure"
- "Unsure"
- "No idea"
- "Not certain"
- "Unclear"

Context Provided:
- Current question and its criteria
- All previous user responses (Q1-current)
- Example of a good response
- User's idea/problem description

Output: JSON with AI-generated suggestions:
{
  "suggestion": "Based on your idea about [X], consider:
  1) [Specific suggestion related to their idea]
  2) [Actionable recommendation]
  3) [Concrete example from context]"
}

Example:
Q: "What data is available?"
User: "I don't know"
AI Suggestion: "Based on your customer service chatbot idea, consider:
1) Customer interaction logs from your ticketing system
2) Historical chat transcripts (anonymized)
3) FAQ documentation and knowledge base articles
You could start by auditing existing data sources in your department."
```

#### AI Recommendations Generation
```
System Role: "Generate intelligent recommendations for this GenAI opportunity."

Context Provided:
- All collected user data
- Mapped CSV fields

Output: JSON with 4 recommendations:
- suggested_overall_approach: "Build" | "Buy" | "Partner"
- suggested_investment_timeline: e.g., "6-9 months"
- suggested_investment_people: e.g., "3-5 FTEs"
- suggested_investment_cost: e.g., "$150K-$250K"
```

### 2. Context Engineering

The application manages conversation context carefully:

#### Performance Optimizations
- **Conversation History Limiting**: Only sends last 6 messages to LLM (saves 2-4 seconds)
- **Static Question Sequence**: Pre-defined Q1-Q10 flow (eliminates 17-28s topic-checking overhead)
- **Conditional AI Usage**: Only calls LLM when response validation fails or user indicates uncertainty

#### Context Structure
```javascript
{
  sessionId: "unique-session-identifier",
  conversationHistory: [
    { questionId: "Q1", question: "...", answer: "..." },
    { questionId: "Q2", question: "...", answer: "..." }
    // Last 6 only sent to LLM
  ],
  userData: {
    idea_title: "...",
    business_problem: "...",
    // All collected data
  },
  currentStep: 5,
  completedQuestions: ["Q1", "Q2", "Q3", "Q4"]
}
```

### 3. Decision Logging Architecture

**Every AI interaction is logged** for audit trail compliance:

```javascript
{
  log_id: "uuid-v4",
  timestamp: "2025-10-22T10:30:00Z",
  session_id: "session-xyz",
  decision_type: "question_generation | criteria_validation | classification",
  input_context: { /* Full context sent to LLM */ },
  llm_response: "...",
  confidence_score: 0.85,
  token_usage: { prompt: 120, completion: 45, total: 165 },
  execution_time_ms: 1234,
  user_feedback: null // Can be populated later
}
```

Logs stored in: `./data/decision_logs.csv` or PostgreSQL (optional)

### 4. Why NOT Agent-Based?

This prototype **deliberately avoids autonomous agents** for several reasons:

| Requirement | LLM API Approach ✅ | Agent Approach ❌ |
|-------------|---------------------|-------------------|
| **Predictability** | Deterministic flow | Autonomous decisions |
| **Audit Trail** | All decisions logged | Agent behavior complex to trace |
| **Cost Control** | Precise API call limits | Variable agent reasoning costs |
| **Development Speed** | Simple REST APIs | Complex orchestration |
| **User Control** | Human-in-the-loop | Opaque agent actions |
| **Compliance** | Clear decision points | Harder to audit |

**Architecture Decision**: Use "Simple GenAI" (direct API calls) to help stakeholders understand more complex architectures without implementing that complexity ourselves.

---

## Complete Technology Stack

### Core Application Layer

| Technology | Version | Purpose | License |
|------------|---------|---------|---------|
| **Next.js** | 14.2.3 | Full-stack React framework with API routes | MIT |
| **React** | 18.3.1 | UI library | MIT |
| **TypeScript** | 5.5.4 | Type-safe JavaScript | Apache 2.0 |
| **Node.js** | 18+ (LTS) | JavaScript runtime | MIT |

**Rationale**: Next.js provides built-in routing, API routes, SSR/SSG, and excellent developer experience for rapid MVP development.

---

### AI & Machine Learning

The prototype supports **three AI modes** with different technology requirements:

#### Mode 1: Static (No External APIs)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Pre-defined Responses** | Built-in | Static question flow with hardcoded responses |
| **No AI Required** | N/A | Fully functional demo mode without API calls |

**Use Case**: Testing, demos, environments without external API access
**Cost**: $0 (no external dependencies)

#### Mode 2: OpenAI (Cloud-based)

| Technology | Version | Purpose | Cost Model |
|------------|---------|---------|------------|
| **OpenAI GPT-5** | Latest (gpt-5) | Question generation, criteria validation, field mapping, recommendations | Pay-per-token |
| **OpenAI Node.js SDK** | 4.67.1 | Official OpenAI client library | Free (MIT) |

**API Usage Patterns**:
- **Question Generation**: ~150 tokens/call (only when follow-ups needed, max 2 per question)
- **Criteria Validation**: ~200 tokens/call (only when validation fails)
- **"I Don't Know" Assistance**: ~300 tokens/call (when user expresses uncertainty)
- **Field Mapping**: ~800 tokens/call (once per submission, maps all conversation to CSV)
- **AI Recommendations**: ~400 tokens/call (once per submission, generates 4 suggestions)

**Typical Submission Scenarios**:

*Scenario 1: Expert User (minimal AI assistance)*
- Follow-up generation: 1 call × 150 tokens = 150 tokens
- Criteria validation: 1 call × 200 tokens = 200 tokens
- Field mapping: 1 call × 800 tokens = 800 tokens
- Recommendations: 1 call × 400 tokens = 400 tokens
- **Total**: ~1,550 tokens (~$0.03 - $0.08)

*Scenario 2: Average User (some assistance needed)*
- Follow-up generation: 3 calls × 150 tokens = 450 tokens
- Criteria validation: 3 calls × 200 tokens = 600 tokens
- "I Don't Know" help: 1 call × 300 tokens = 300 tokens
- Field mapping: 1 call × 800 tokens = 800 tokens
- Recommendations: 1 call × 400 tokens = 400 tokens
- **Total**: ~2,550 tokens (~$0.05 - $0.15)

*Scenario 3: Novice User (frequent assistance)*
- Follow-up generation: 5 calls × 150 tokens = 750 tokens
- Criteria validation: 5 calls × 200 tokens = 1,000 tokens
- "I Don't Know" help: 3 calls × 300 tokens = 900 tokens
- Field mapping: 1 call × 800 tokens = 800 tokens
- Recommendations: 1 call × 400 tokens = 400 tokens
- **Total**: ~3,850 tokens (~$0.08 - $0.25)

**Cost Estimate**: $0.03 - $0.25 per completed idea submission (based on GPT-5 pricing)

#### Mode 3: Ollama (Local Open-Source)

| Technology | Version | Purpose | Cost Model |
|------------|---------|---------|------------|
| **Ollama** | Latest | Local model server | Free (MIT) |
| **GPT-OSS** | 20B parameters | Open-source language model (gpt-oss:20b) | Free (one-time download) |
| **OpenAI-Compatible API** | N/A | Ollama provides OpenAI-compatible endpoints | Free |

**Requirements**:
- Ollama installed locally (https://ollama.ai)
- gpt-oss:20b model downloaded (~12GB disk space)
- Minimum 16GB RAM for acceptable performance

**Cost Estimate**: $0 (runs locally, one-time setup)

---

### Data Storage

| Technology | Use Case | Rationale |
|------------|----------|-----------|
| **CSV Files** | All data storage | Simple, portable, human-readable, no database setup required |
| **JSON Files** | Session data, decision logs | Native JavaScript format for complex nested data structures |

**Storage Locations**:
- Main idea submissions: `./data/ai_intake_ideas.csv`
- AI decision logs: `./data/decision_logs.csv`
- Session state: In-memory (not persisted between restarts)

**Benefits of CSV Approach**:
- ✅ Zero database configuration required
- ✅ Easy to inspect and edit manually
- ✅ Simple backup (just copy ./data folder)
- ✅ Works across all platforms (Windows/Mac/Linux)
- ✅ Can import into Excel/Google Sheets for analysis

**Note**: For production deployments requiring >1000 submissions, Wells Fargo IT may choose to migrate to PostgreSQL or another enterprise database. The current CSV implementation is suitable for prototypes and MVPs.

---

### Development & Testing

| Technology | Purpose | Coverage |
|------------|---------|----------|
| **Jest** | Unit testing | 22 tests, 100% component coverage |
| **Playwright** | Visual regression testing | 8 tests with baseline snapshots |
| **axe-core** | Accessibility testing | 11 tests, WCAG 2.1 AA compliance |
| **ESLint** | Code linting | TypeScript-aware rules |
| **cross-env** | Cross-platform env vars | Windows/Mac/Linux compatibility |

---

### UI & Styling

| Technology | Purpose |
|------------|---------|
| **Tailwind CSS** | Utility-first CSS framework |
| **Custom CSS Modules** | Component-scoped styling |
| **Brand Colors** | #D71E2B (red), #FFCD41 (yellow) |

---

### Document Generation

| Technology | Version | Purpose | Output Format |
|------------|---------|---------|---------------|
| **jsPDF** | 3.0.3 | Client-side PDF generation | .pdf |
| **jspdf-autotable** | 5.0.2 | Table and structured layouts in PDFs | .pdf |
| **react-markdown** | 10.1.0 | Markdown rendering for display | HTML |

**Features**:
- Branded intake form
- Includes all collected data (39 fields)
- Logo and color scheme
- Downloadable from review page before submission

---

### Deployment & Infrastructure

| Technology | Purpose | Notes |
|------------|---------|-------|
| **Docker** (Optional) | Containerization | Consistent environments, not required for MVP |
| **Docker Compose** (Optional) | Multi-container orchestration | Simplified local development |
| **Windows/Mac/Linux** | Development platforms | Cross-platform compatible via cross-env |

---

### Dependency Management

```json
{
  "dependencies": {
    "next": "14.2.3",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "typescript": "5.5.4",
    "openai": "4.67.1",
    "dotenv": "16.4.5",
    "jspdf": "3.0.3",
    "jspdf-autotable": "5.0.2",
    "react-markdown": "10.1.0",
    "uuid": "13.0.0"
  },
  "devDependencies": {
    "@playwright/test": "1.56.0",
    "@testing-library/react": "16.3.0",
    "@testing-library/jest-dom": "6.9.1",
    "jest": "30.2.0",
    "jest-axe": "10.0.0",
    "cross-env": "10.1.0"
  }
}
```

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│  (Next.js Frontend - React Components - Port 3073)          │
│  - Landing Page / Service Tiles                             │
│  - Conversational Flow UI                                   │
│  - Progress Indicators / Step Tracking                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ HTTP Requests
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  (Next.js API Routes - Server-Side Logic)                   │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ /api/openai/       │  │ /api/data/         │            │
│  │  - generate-       │  │  - submit-idea     │            │
│  │    question-v2     │  │  - check-duplicate │            │
│  │  - analyze         │  │  - export-form     │            │
│  └────────┬───────────┘  └────────┬───────────┘            │
│           │                       │                          │
└───────────┼───────────────────────┼──────────────────────────┘
            │                       │
            ▼                       ▼
┌───────────────────────┐  ┌───────────────────────┐
│   OPENAI API LAYER    │  │   DATA STORAGE        │
│  (External Service)   │  │   (CSV/PostgreSQL)    │
│                       │  │                       │
│  ┌─────────────────┐ │  │  ┌─────────────────┐ │
│  │ GPT-5 API       │ │  │  │ CSV Files       │ │
│  │  - Question Gen │ │  │  │  - Ideas        │ │
│  │  - Validation   │ │  │  │  - Decisions    │ │
│  │  - Classification│ │  │  │  - Sessions    │ │
│  └─────────────────┘ │  │  └─────────────────┘ │
│                       │  │         OR            │
│  ┌─────────────────┐ │  │  ┌─────────────────┐ │
│  │ Embeddings API  │ │  │  │ PostgreSQL DB   │ │
│  │  - Duplicate    │ │  │  │  (Optional)     │ │
│  │    Detection    │ │  │  │                 │ │
│  └─────────────────┘ │  │  └─────────────────┘ │
└───────────────────────┘  └───────────────────────┘
            │
            ▼
┌───────────────────────┐
│   DECISION LOGGING    │
│  (Audit Trail)        │
│  - All LLM calls      │
│  - Token usage        │
│  - Response times     │
└───────────────────────┘
```

### Data Flow

1. **User submits response** → React component captures input
2. **Frontend validation** → Basic checks (non-empty, length limits)
3. **API call to Next.js backend** → `/api/openai/generate-question-v2`
4. **Uncertainty detection** → Check if user said "I don't know"
   - If yes → Generate AI-assisted suggestions based on context
   - If no → Continue to criteria validation
5. **Criteria validation** → Evaluate if response meets question criteria
   - If met → Move to next question
   - If not met → Generate contextual follow-up question (max 2 per question)
6. **Context preparation** → Last 6 messages + current question criteria
7. **LLM API call** → OpenAI GPT-5 or Ollama (only when AI assistance needed)
8. **Response processing** → Parse JSON, extract follow-up or move forward
9. **Decision logging** → Save all AI interactions to CSV with full context
10. **Submission processing** (after Q10 complete):
    - **Field mapping** → LLM maps all responses to 39 CSV fields
    - **AI recommendations** → Generate 4 intelligent suggestions
    - **CSV storage** → Append to dummy_data.csv
    - **PDF generation** → User can download 2-page intake form

**Note**: Duplicate detection is NOT part of the current flow. Planned for Task 3.0.

---

## Deployment Requirements

### Minimum System Requirements

| Resource | Requirement | Notes |
|----------|-------------|-------|
| **Operating System** | Windows 10+, macOS 11+, Linux (Ubuntu 20.04+) | Cross-platform compatible |
| **Node.js** | Version 18+ (LTS recommended) | Required for Next.js |
| **RAM** | 4GB minimum, 8GB recommended | For development/testing |
| **Disk Space** | 500MB for application, 1GB for dependencies | |
| **Network** | Internet connection for OpenAI API | Must reach api.openai.com |
| **Ports** | 3073 (configurable via .env) | For web server |

### Production Deployment Requirements

| Resource | Specification | Purpose |
|----------|---------------|---------|
| **Web Server** | Nginx/IIS | Reverse proxy, SSL termination |
| **Application Server** | Node.js 18+ process manager (PM2) | Process management |
| **Database** (Optional) | PostgreSQL 13+ | For production data storage |
| **SSL Certificate** | Valid TLS certificate | HTTPS encryption |
| **Firewall Rules** | Port 443 (HTTPS) open internally | Internal network access only |
| **Load Balancer** (Optional) | For high availability | Multiple instances |

---

## Access & Resource Requirements

### What You Need to Deploy in Another Environment

**IMPORTANT**: Requirements depend on which AI mode you choose to deploy.

#### 1. AI Service Access (Choose One)

You have **three options** for AI functionality:

##### Option A: Static Mode (No External Dependencies) ✅ EASIEST

**What**: No external AI service required - uses pre-defined responses

**Requirements**: NONE

**Pros**:
- ✅ Zero setup complexity
- ✅ No external API dependencies
- ✅ No recurring costs
- ✅ Works in air-gapped environments

**Cons**:
- ❌ No intelligent follow-up questions
- ❌ Limited to static question flow

**Best For**: Demos, testing, highly restricted environments

##### Option B: OpenAI API Access (Cloud-based) ☁️

**What**: OpenAI Platform API key with access to:
- GPT-5 model (`gpt-5`)
- Embeddings model (`text-embedding-3-large`)

**How to Obtain**:
1. IT must establish an **OpenAI Enterprise Agreement** OR use existing contract
2. Create an **organization** in OpenAI platform (https://platform.openai.com)
3. Generate an **API key** with appropriate usage limits
4. Set up **billing account** with payment method
5. Configure **rate limits** (recommended: 10 requests/minute for MVP)

**Cost Model**:
- GPT-5: ~$0.01-0.03 per 1K tokens (pricing subject to OpenAI changes)
- Embeddings: ~$0.0001 per 1K tokens
- **Estimated cost per idea**: $0.50 - $2.00

**Security Considerations**:
- Store API key in environment variables (NEVER in code)
- Use separate keys for dev/staging/production
- Implement request logging for audit trail
- Set spending limits to prevent runaway costs

**Best For**: Production deployments with budget for cloud AI services

##### Option C: Ollama (Local Open-Source Model) 🏠

**What**: Local installation of Ollama with GPT-OSS model

**How to Obtain**:
1. Download and install **Ollama** from https://ollama.ai
2. Install the model: `ollama pull gpt-oss:20b`
3. Start Ollama service: `ollama serve`
4. No API key needed - runs locally

**Requirements**:
- 16GB RAM minimum (32GB recommended)
- ~12GB disk space for model
- CPU or GPU for inference (GPU faster but not required)

**Cost Model**:
- One-time setup: $0
- Ongoing costs: $0 (electricity only)

**Performance**:
- Slower than GPT-5 (5-10 seconds vs 1-2 seconds per call)
- Quality may be lower than GPT-5
- All features work (follow-ups, field mapping, recommendations)

**Best For**: Environments without external API access, cost-sensitive deployments, air-gapped networks

---

#### 2. Internal Server/VM (REQUIRED)

**What**: Windows Server or Linux VM for hosting the application

**Specifications**:
- **OS**: Windows Server 2019+ OR Ubuntu Server 20.04+
- **CPU**: 2 cores minimum (4+ for production)
- **RAM**: 8GB minimum (16GB+ for production)
- **Storage**: 50GB minimum
- **Network**: Internal network access
- **Permissions**: Ability to install Node.js, open ports

**How to Obtain**:
1. Submit IT infrastructure request through IT Service Management
2. Specify: "Node.js web application hosting for AI Intake Assistant prototype"
3. Request Node.js 18+ pre-installation OR admin rights to install
4. Request port 3073 (or 443 for production) to be opened for internal access

---

#### 3. Network Configuration

**Firewall Rules Needed**:

| Direction | Protocol | Port | Source | Destination | Purpose |
|-----------|----------|------|--------|-------------|---------|
| Outbound | HTTPS | 443 | App Server | api.openai.com | OpenAI API calls |
| Inbound | HTTP/HTTPS | 3073/443 | Internal network | App Server | User access |

**Corporate Proxy Configuration** (if applicable):

If Wells Fargo uses a corporate proxy for outbound traffic:

```bash
# Set in .env file
NODE_TLS_REJECT_UNAUTHORIZED=0  # Only for dev behind corporate proxy
# OR install corporate root certificate
NODE_EXTRA_CA_CERTS=/path/to/wellsfargo-root-cert.pem
```

**DNS Configuration**:
- Request internal DNS entry for easier access
- Alternative: Use server IP address directly (e.g., `http://10.123.45.67:3073`)

---

#### 4. Optional: PostgreSQL Database

**For Production Deployments** (CSV files sufficient for prototype):

**What**: PostgreSQL 13+ database instance

**How to Obtain**:
1. Request through Database Services
2. Specify: "PostgreSQL database for AI Intake application data storage"
3. Required database size: 1GB minimum (scales with usage)
4. Request database credentials and connection details

**Alternative**: Continue using CSV files (adequate for <1000 submissions)

---

#### 5. Software Installation Requirements

**On the deployment server, install**:

```bash
# Node.js (v18+)
# Download from: https://nodejs.org/en/download/

# Verify installation
node --version  # Should show v18.x.x or higher
npm --version   # Should show v9.x.x or higher

# Optional: Process Manager (for production)
npm install -g pm2

# Optional: Docker (if using containerized deployment)
# Install Docker Desktop or Docker Engine
```

---

## Configuration Guide

### Step-by-Step Deployment

#### Step 1: Copy Application Files

```bash
# Copy the entire project folder to the server
# Total size: ~500MB (including node_modules)

# Project structure:
AI_Intake/
├── src/                  # Application source code
├── public/               # Static assets (images, logos)
├── data/                 # CSV data storage (create if missing)
├── logs/                 # Application logs (create if missing)
├── package.json          # Dependencies
├── .env.example          # Template configuration
└── README.md             # Documentation
```

#### Step 2: Configure Environment Variables

```bash
# Copy template to .env
cp .env.example .env

# Edit .env with your values
nano .env  # or notepad .env on Windows
```

**Required Configuration** (all modes):

```bash
# === REQUIRED SETTINGS ===

# Application Port
APP_PORT=3073

# Host binding (for internal network access)
HOST=0.0.0.0  # Bind to all interfaces for network access

# === AI MODE CONFIGURATION (Choose One) ===
# Options: "static" | "openai" | "ollama"
NEXT_PUBLIC_AI_MODE=static  # Start with static for testing
```

**Additional Configuration for OpenAI Mode**:

```bash
# OpenAI API Configuration (only if NEXT_PUBLIC_AI_MODE=openai)
OPENAI_API_KEY=sk-proj-xxxxxxxxxx  # YOUR OPENAI API KEY HERE
OPENAI_MODEL=gpt-5
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

**Additional Configuration for Ollama Mode**:

```bash
# Ollama Configuration (only if NEXT_PUBLIC_AI_MODE=ollama)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gpt-oss:20b  # Must match installed model
OLLAMA_API_KEY=ollama  # Dummy key (Ollama ignores this)
```

**Optional Performance Settings**:

```bash
# Application Settings
NODE_ENV=production  # Use "production" for deployment

# Performance Optimization
ENABLE_SEMANTIC_DUPLICATE_CHECK=false  # Disable for 10-15s speedup
CONVERSATION_HISTORY_LIMIT=6           # Limit to last 6 messages

# Corporate Network (if behind proxy with self-signed certificates)
NODE_TLS_REJECT_UNAUTHORIZED=0  # Only if behind corporate proxy
# Or use corporate certificate:
# NODE_EXTRA_CA_CERTS=/path/to/root-cert.pem
```

**Example Configurations**:

```bash
# Configuration 1: Static Mode (No AI, no external dependencies)
NEXT_PUBLIC_AI_MODE=static
APP_PORT=3073
HOST=0.0.0.0

# Configuration 2: OpenAI Mode (Cloud AI)
NEXT_PUBLIC_AI_MODE=openai
OPENAI_API_KEY=sk-proj-abc123...
APP_PORT=3073
HOST=0.0.0.0

# Configuration 3: Ollama Mode (Local AI)
NEXT_PUBLIC_AI_MODE=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gpt-oss:20b
APP_PORT=3073
HOST=0.0.0.0
```

#### Step 3: Install Dependencies

```bash
# Navigate to project directory
cd /path/to/AI_Intake

# Install all dependencies (takes 2-5 minutes)
npm install

# Verify installation
npm list --depth=0
```

#### Step 4: Create Data Directories

```bash
# Create required directories (if missing)
mkdir -p data
mkdir -p logs

# Verify permissions (Linux/Mac)
chmod 755 data
chmod 755 logs
```

#### Step 5: Build for Production

```bash
# Build optimized production bundle
npm run build

# This creates a .next/ directory with compiled code
# Takes 1-3 minutes
```

#### Step 6: Start the Application

**Option A: Direct Start (Development/Testing)**
```bash
# Start the server
npm start

# Application will be available at:
# http://your-server-ip:3073
# Example: http://10.123.45.67:3073
```

**Option B: Production with PM2 (Recommended)**
```bash
# Install PM2 globally
npm install -g pm2

# Start application with PM2
pm2 start npm --name "ai-intake" -- start

# Configure auto-restart on server reboot
pm2 startup
pm2 save

# View logs
pm2 logs ai-intake

# Monitor status
pm2 status
```

#### Step 7: Verify Deployment

```bash
# Test health endpoint
curl http://localhost:3073/api/health
# Should return: {"status":"healthy"}

# For OpenAI mode only:
curl http://localhost:3073/api/health/openai
# Should return: {"status":"connected","model":"gpt-5"}

# For Ollama mode only (verify Ollama is running):
curl http://localhost:11434/api/version
# Should return Ollama version info

# Access from another computer on the network
# http://YOUR_SERVER_IP:3073
# Example: http://10.123.45.67:3073
```

#### Step 8: Configure Firewall (If Needed)

**Windows Server:**
```powershell
# Open PowerShell as Administrator
New-NetFirewallRule -DisplayName "AI Intake Assistant" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 3073 `
  -Action Allow `
  -Profile Domain,Private
```

**Linux (Ubuntu):**
```bash
# Allow port 3073 from internal network only
sudo ufw allow from 10.0.0.0/8 to any port 3073
sudo ufw reload
```

---

## Cost Considerations

### One-Time Setup Costs by Mode

| Mode | Setup Cost | Notes |
|------|------------|-------|
| **Static** | $0 | No dependencies, instant deployment |
| **OpenAI** | $0 | Free to create OpenAI account |
| **Ollama** | $0 | Free download (~12GB, may take 1-2 hours) |
| **Server/VM** | Internal | Wells Fargo IT infrastructure (all modes) |

### Ongoing Operational Costs by Mode

#### Static Mode
| Item | Cost |
|------|------|
| **AI API Calls** | $0 (no external API) |
| **Server Hosting** | Internal (absorbed by IT) |
| **Total Annual Cost** | **$0** |

#### OpenAI Mode
| Item | Cost |
|------|------|
| **OpenAI API Usage** | $0.03 - $0.25 per idea (varies by user expertise) |
| **Server Hosting** | Internal (absorbed by IT) |
| **Estimated Annual Cost (500 ideas/year)** | **$15 - $125** |

**Cost Breakdown by User Type** (500 submissions/year):
- 50% Expert users (minimal help): 250 × $0.05 = $12.50
- 40% Average users (some help): 200 × $0.10 = $20.00
- 10% Novice users (frequent help): 50 × $0.15 = $7.50
- **Realistic Annual Cost**: ~$40/year

#### Ollama Mode
| Item | Cost |
|------|------|
| **AI API Calls** | $0 (runs locally) |
| **Server Hosting** | Internal (absorbed by IT) |
| **Additional Compute** | Minimal (higher CPU/RAM usage) |
| **Total Annual Cost** | **~$0** (electricity only) |

### Cost Optimization Tips (OpenAI Mode Only)

1. **Reduce API Calls**:
   - Set `ENABLE_SEMANTIC_DUPLICATE_CHECK=false` to skip embedding API calls (-$0.10/idea)
   - Use stricter validation to reduce follow-up questions (-$0.20/idea)

2. **Set API Rate Limits**:
   - Configure OpenAI organization limits (e.g., 10 requests/minute)
   - Prevents unexpected cost spikes from heavy usage

3. **Monitor Usage**:
   - Review OpenAI usage dashboard monthly
   - Set up billing alerts for unusual activity

4. **Consider Hybrid Approach**:
   - Use **Static mode** for demos and testing ($0)
   - Use **OpenAI mode** only for production submissions
   - Switch modes via environment variable (no code changes)

### Cost Comparison Summary

For **500 ideas/year**:
- **Static Mode**: $0/year (no AI capabilities)
- **Ollama Mode**: $0/year (local AI, slower performance)
- **OpenAI Mode**: ~$40/year realistic estimate (range: $15-$125 depending on user mix)

**Why So Affordable?**
- Only calls AI when needed (not every interaction)
- "I Don't Know" assistance helps novice users without repeated calls
- Field mapping done once at the end (not per-question)
- Efficient context management (last 6 messages only)

---

## Security & Compliance

### Data Security

| Aspect | Implementation |
|--------|----------------|
| **API Key Storage** | Environment variables only, NEVER in code or version control |
| **Data Encryption** | HTTPS for all traffic (TLS 1.2+) |
| **Access Control** | Internal network only, no public internet access |
| **Audit Logging** | All AI decisions logged with timestamps and user sessions |
| **Session Management** | Secure session IDs, 30-minute timeout |

### Compliance Considerations

**Audit Trail Requirements**:
- ✅ All LLM API calls logged to `data/decision_logs.csv`
- ✅ Timestamps, user sessions, input/output captured
- ✅ Token usage tracked for cost analysis
- ✅ User feedback mechanism for quality assurance

**Data Retention**:
- Idea submissions: Retained indefinitely (business need)
- Decision logs: Recommended 1-year retention for audit purposes
- Session data: Auto-expire after 24 hours


---

## Support & Maintenance

### Monitoring Recommendations

1. **Application Health**:
   - Monitor `/api/health` endpoint (should return 200 OK)
   - Track response times (should be <3 seconds)
   - Alert on high error rates

2. **OpenAI API Status**:
   - Monitor `/api/health/openai` endpoint
   - Track API quota usage via OpenAI dashboard
   - Set up billing alerts

3. **Storage Capacity**:
   - Monitor CSV file sizes (if using CSV storage)
   - Database disk usage (if using PostgreSQL)
   - Log rotation for `./logs/` directory

### Common Issues & Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Self-signed certificate error" | Corporate proxy | Set `NODE_TLS_REJECT_UNAUTHORIZED=0` in .env |
| "Port already in use" | Another app using port 3073 | Change `APP_PORT` in .env |
| "OpenAI API error" | Invalid API key | Verify `OPENAI_API_KEY` in .env |
| "Slow response times" | High conversation history | Reduce `CONVERSATION_HISTORY_LIMIT` to 4 |
| Can't access from other computers | Firewall blocking | Open port 3073 in firewall rules |

### Maintenance Tasks

**Weekly**:
- Review application logs for errors
- Check OpenAI API usage and costs

**Monthly**:
- Backup `./data/` directory
- Review decision logs for quality assurance
- Update dependencies: `npm update`

**Quarterly**:
- Review and archive old decision logs
- Performance optimization review
- Security patch updates

---

## Next Steps for Deployment

### Pre-Deployment Checklist

**All Modes** (Required):
- [ ] internal server/VM provisioned
- [ ] Node.js 18+ installed on server
- [ ] Application files copied to server
- [ ] `npm install` completed successfully
- [ ] `.env` file created and configured
- [ ] `npm run build` completed successfully
- [ ] Port 3073 accessible from internal network
- [ ] Health check passing: `curl http://localhost:3073/api/health`
- [ ] Application accessible from other computers: `http://SERVER_IP:3073`

**Additional for Static Mode**:
- [ ] `NEXT_PUBLIC_AI_MODE=static` set in `.env`
- [ ] Application tested with static responses

**Additional for Ollama Mode**:
- [ ] Ollama installed: `https://ollama.ai`
- [ ] Model downloaded: `ollama pull gpt-oss:20b`
- [ ] Ollama service running: `ollama serve`
- [ ] `NEXT_PUBLIC_AI_MODE=ollama` set in `.env`
- [ ] Ollama health check: `curl http://localhost:11434/api/version`

**Additional for OpenAI Mode**:
- [ ] OpenAI API key obtained
- [ ] API key tested via: `curl http://localhost:3073/api/health/openai`
- [ ] `NEXT_PUBLIC_AI_MODE=openai` set in `.env`
- [ ] Network access to api.openai.com verified
- [ ] Corporate proxy configured (if behind firewall)
- [ ] OpenAI billing limits set

**Final Steps**:
- [ ] Monitoring and log rotation configured
- [ ] Stakeholder demo scheduled
- [ ] User training materials prepared

### Recommended Deployment Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| **Infrastructure Setup** | 1-2 weeks | Server provisioning, network config, OpenAI account |
| **Application Deployment** | 2-3 days | Install dependencies, configure, test |
| **User Acceptance Testing** | 1-2 weeks | Internal testing, feedback gathering |
| **Production Rollout** | 1 day | Final deployment, monitoring setup |

---

## Conclusion

The **AI-Powered GenAI Idea Assistant** prototype demonstrates a **prompt engineering and context engineering approach** using direct LLM API calls rather than autonomous agents. This architecture provides:

✅ **Predictable, auditable behavior** for enterprise compliance
✅ **Cost-effective AI usage** with controlled API calls
✅ **Fast development and deployment** using standard web technologies
✅ **Scalable foundation** for future enhancements
✅ **Flexible deployment options** with three AI modes

### Key Innovation: Multiple Deployment Modes

The prototype supports **three AI modes** to accommodate different environments:

| Mode | Setup Complexity | Annual Cost (500 ideas) | AI Features | Best For |
|------|------------------|------------------------|-------------|----------|
| **Static** | ⭐ Easiest | $0 | None (pre-defined flow) | Demos, testing, air-gapped |
| **Ollama (GPT-OSS)** | ⭐⭐ Medium | $0 | All features (slower) | No external API access |
| **OpenAI** | ⭐⭐⭐ Complex | ~$40 (range: $15-$125) | All features (best quality) | Production with budget |

**This means stakeholders can**:
- Start with **Static mode** for immediate demos (no dependencies, $0 cost)
- Upgrade to **Ollama mode** if external APIs are restricted (free, local AI)
- Move to **OpenAI mode** when budget and API access are approved (best quality)

**All with the same codebase** - just change one environment variable!

### Minimum Requirements to Deploy

**For Static Mode** (simplest):
1. ✅ Internal server/VM with Node.js 18+
2. ✅ Port 3073 opened for internal network access
3. ✅ Configuration (.env file with `NEXT_PUBLIC_AI_MODE=static`)

**For Ollama Mode** (no external APIs):
1. ✅ Everything from Static mode, plus:
2. ✅ Ollama installation with gpt-oss:20b model
3. ✅ 16GB RAM minimum

**For OpenAI Mode** (full AI capabilities):
1. ✅ Everything from Static mode, plus:
2. ✅ OpenAI API access (GPT-5)
3. ✅ Network access to api.openai.com
4. ✅ Budget for API usage (~$40/year for 500 submissions)

### Deployment Timeline

| Scenario | Setup Time | What's Included |
|----------|------------|-----------------|
| **Static Mode** | 1 day | Server setup + app deployment |
| **Ollama Mode** | 2-3 days | Static + Ollama installation |
| **OpenAI Mode** | 2-4 weeks | Static + OpenAI contract + API setup |

### Summary

**What was built**:
- ✅ Next.js 14 web application (TypeScript + React)
- ✅ Three AI modes: Static, Ollama (GPT-OSS), OpenAI (GPT-5)
- ✅ CSV-based data storage with 39 fields (no database required)
- ✅ 10-question conversational flow with intelligent follow-ups (max 2 per question)
- ✅ Criteria validation for response quality
- ✅ **"I Don't Know" assistance** - AI generates contextual suggestions based on previous answers
- ✅ **Intelligent field mapping** using LLM (conversation → 39 CSV fields)
- ✅ **AI-powered recommendations** (4 suggestions per submission: approach, timeline, team, cost)
- ✅ PDF form generation (2-page intake form)
- ✅ Decision logging infrastructure for audit trail
- ✅ Cross-platform support (Windows/Mac/Linux)
- ✅ WCAG 2.1 AA accessible UI
- ✅ Unit, accessibility, and visual regression tests

**What was NOT built** (planned for future phases):
- ❌ Duplicate detection using embeddings (Task 3.0 - future)
- ❌ Idea classification/categorization (future)
- ❌ PostgreSQL database integration (CSV works for MVP)
- ❌ Docker containerization (not required)
- ❌ Admin dashboard (not needed for MVP)
- ❌ Analytics dashboard (not needed for MVP)
- ❌ Word (.docx) export (PDF only)

**Maintenance Effort**: <5 hours/month (log review, updates, backups)

For questions or support, refer to README.md or contact the development team.

---

**Document End**
