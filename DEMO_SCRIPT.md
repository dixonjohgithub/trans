# AI Intake Assistant - Demo Script & Example Answers

## Demo Overview
This document provides example answers for demonstrating the AI Intake Assistant in **static mode**. The workflow guides users through 11 questions across 5 stages to capture a complete GenAI idea.

---

## Demo Scenario
**Use Case**: Conversational AI Chatbot for SSRS Report Data Access
**Target**: Enable business users to query SQL Server Reporting Services data using natural language instead of navigating complex reports

---

## Workflow Stages

### Stage 1: Introduction (Question 1)

#### Question 1: Tell us about your GenAI idea
**What to demonstrate**: The initial idea capture

**Example Answer**:
```
We want to build a conversational AI chatbot that allows business users to ask questions about our SSRS report data in plain English. Currently, business users struggle to get quick answers from SQL Server Reporting Services reports - they have to open multiple reports, apply filters, navigate complex dashboards, and manually calculate numbers. The process is time-consuming, requires technical know-how, and often leads to frustrated users requesting help from our BI team. The chatbot would let users simply ask questions like "What was the total loan disbursement in Q2?" or "Show me the top 5 branches by revenue" and get instant answers pulled from our SSRS datasets in real-time.
```

**Why this works**:
- Clear problem statement (complex SSRS navigation, time-consuming)
- Specific examples of natural language queries
- Explains the AI capability needed (conversational interface to data)
- Mentions the intended outcome (instant answers, reduced BI team burden)

---

### Stage 2: Business Case (Questions 2-5)

#### Question 2: Solution Name
**What to demonstrate**: Naming the opportunity

**Example Answer**:
```
SSRS DataTalk Assistant
```

**Alternative options**:
- ReportChat AI
- Business Intelligence Conversational Interface
- QuickQuery SSRS Bot
- AskData Chatbot

---

#### Question 3: Business Problem
**What to demonstrate**: Detailed problem exploration with criteria validation

**Example Answer**:
```
Business users across our organization spend 4-6 hours per week navigating SSRS reports to answer executive questions and prepare presentations. The current process requires opening multiple reports (we have 150+ SSRS reports), applying various filters, downloading data to Excel, and manually calculating totals or trends. This is time-consuming, error-prone, and requires technical expertise to know which report contains what data. Our BI team fields 50-80 ad-hoc data requests per week, distracting them from strategic work. Executives often make decisions based on stale data because getting current numbers is too cumbersome. This affects 200+ business users including branch managers, product managers, and executives who need quick data insights.
```

**Why this works**:
- ✅ Describes customer/business pain point (time waste, manual work, delayed decisions)
- ✅ Explains why current process is problematic (slow, requires technical expertise, error-prone)
- ✅ Indicates scope/impact (200+ users, 50-80 requests/week, 4-6 hours/week per user)

**If system asks follow-up**: "You mentioned that users need technical expertise. Can you provide more detail about what specific challenges they face?"

**Follow-up Answer**:
```
Users struggle with knowing which of our 150+ reports contains the data they need, understanding complex filter parameters, and interpreting report layouts that were designed for technical audiences. They often pull data from the wrong time period or business unit, leading to incorrect analysis. Many users resort to asking the BI team for help, which creates bottlenecks and delays.
```

---

#### Question 4: AI Solution Approach
**What to demonstrate**: How AI solves the problem

**Example Answer**:
```
The chatbot will use natural language processing (NLP) to understand user questions like "What was total loan disbursement in Q2?" or "Show me top 5 branches by revenue." The AI will translate these questions into SQL queries, connect to our SSRS report datasets and underlying databases, execute the queries, and return results in a conversational format - as text, charts, or tables. For complex questions, it will suggest clarifications ("Which product line?" or "This year or last year?"). The chatbot reduces data retrieval time from 15-30 minutes (opening reports, filtering, calculating) to under 30 seconds. Users no longer need to know which report to use or how to apply filters - they just ask in plain English. This eliminates the 50-80 weekly BI team requests for ad-hoc data and empowers users with self-service analytics.
```

**Why this works**:
- ✅ Describes AI approach (NLP for question understanding, SQL query generation)
- ✅ Explains improvements (15-30 min → 30 seconds, eliminates 50-80 weekly requests)
- ✅ Connects back to problem (complex navigation, BI team burden, slow access)

---

#### Question 5: Target Users & Impact
**What to demonstrate**: Quantifiable benefits

**Example Answer**:
```
Primary users are 200+ business users including 80 branch managers, 60 product managers, 40 executives, and 20 analysts who regularly need SSRS data for decision-making and reporting. Secondary users are 8 BI team members who currently handle ad-hoc requests. We expect to save each business user 3-4 hours per week (reducing report navigation from 15-30 minutes to 30 seconds per query), totaling 600-800 hours saved weekly. This translates to $400K annually in productivity gains. We'll reduce BI team ad-hoc request volume by 70% (from 50-80 requests to 15-25), freeing up 25 hours per week for the BI team to focus on strategic analytics projects. Decision-making speed will improve as executives get real-time data instead of waiting hours or days.
```

**Why this works**:
- ✅ Identifies specific user groups (200+ users: 80 branch mgrs, 60 product mgrs, 40 execs, 20 analysts)
- ✅ Provides user numbers
- ✅ Quantifies benefits (600-800 hours/week saved, $400K annually, 70% reduction in requests)

---

### Stage 3: Technical Details (Questions 6-7)

#### Question 6: Data Sources
**What to demonstrate**: Data availability and access

**Example Answer**:
```
The chatbot will connect to our SQL Server Reporting Services (SSRS) datasets and underlying SQL Server databases. We have 150+ SSRS reports pulling from 4 main databases: Loan Management System (LMS), Customer Relationship Management (CRM), Branch Operations Database, and Financial Performance Warehouse. These databases contain 5+ years of historical data including loan transactions, customer demographics, branch metrics, and financial KPIs. All data is stored on on-premises SQL Server 2019 instances with nightly ETL jobs refreshing the reporting warehouse. The chatbot will use read-only database connections with role-based access control to ensure users only see data they're authorized to access.
```

**Why this works**:
- ✅ Identifies specific data sources (SSRS datasets, 4 main databases with names)
- ✅ Indicates storage location and volume (150+ reports, 5+ years historical data)
- ✅ Mentions data format and security (SQL Server, read-only access, RBAC)

---

#### Question 7: Technical Feasibility
**What to demonstrate**: Execution capability

**Example Answer**:
```
Yes - we have the capability to execute this. Our IT team has experience with chatbot development using Azure Bot Framework and has already deployed 2 chatbots for HR and IT support. We have 2 AI/ML engineers familiar with NLP and LLMs, 3 backend developers who know SQL Server well, 1 database architect, and 2 BI developers who understand our SSRS environment. The chatbot will integrate with our existing SSRS infrastructure using SQL Server connection strings and the SSRS REST API for report metadata. We already have Azure OpenAI Service access for GPT-4. The main technical challenge will be training the AI to generate accurate SQL queries for our complex database schema and handling ambiguous user questions, which we'll address through schema documentation, query validation, and user feedback loops.
```

**Why this works**:
- ✅ Addresses technical capability (Azure Bot Framework, 2 prior chatbots)
- ✅ Mentions tools/platforms (Azure Bot Framework, Azure OpenAI, SSRS REST API)
- ✅ Identifies skills (2 AI engineers, 3 backend devs, 1 DB architect, 2 BI devs)
- Acknowledges challenges (complex schemas, ambiguous questions) with solutions

---

### Stage 4: Feasibility (Question 8)

#### Question 8: Timeline & Investment
**What to demonstrate**: Realistic planning

**Example Answer**:
```
We estimate 3-4 months for an MVP that handles the top 20 most-asked questions across 3 core databases (LMS, CRM, Branch Operations). Full production deployment covering all 4 databases and 150+ reports would take 6-8 months. For the MVP, we need 3 FTEs (1 AI/ML engineer for NLP model, 1 backend developer for chatbot integration, 1 BI developer for database schema mapping) for 4 months. Full deployment would require 5 FTEs including a QA engineer and DevOps engineer. Budget estimate is $180-220K for MVP (staff costs + Azure Bot Framework + Azure OpenAI API usage) and $450-550K for full deployment including production infrastructure, security hardening, user training, and change management.
```

**Why this works**:
- ✅ Provides timeline (3-4 months MVP, 6-8 months full)
- ✅ Indicates team size (3 FTEs for MVP, 5 for full)
- ✅ Mentions budget ($180-220K MVP, $450-550K full)

---

### Stage 5: Risk Assessment (Questions 9-11)

#### Question 9: Risks & Challenges
**What to demonstrate**: Honest risk assessment

**Example Answer**:
```
Several risks: (1) AI-generated SQL queries may be inaccurate or return wrong results if the user question is ambiguous, potentially leading to incorrect business decisions. (2) Complex database schema across 4 systems - the AI may struggle to understand table relationships and generate efficient queries without extensive training. (3) Data security concerns - need to ensure the chatbot respects role-based access controls and doesn't expose sensitive data to unauthorized users. (4) User adoption challenges - business users may be skeptical of AI-generated answers and prefer the "manual but trusted" approach. (5) Performance issues - poorly optimized queries generated by the AI could slow down production databases during business hours.
```

**Why this works**:
- ✅ Identifies multiple risks (technical, security, organizational, performance)
- ✅ Shows thoughtful consideration
- ✅ Honest and realistic

---

#### Question 10: Mitigation Strategies
**What to demonstrate**: Risk management approach

**Example Answer**:
```
To address these risks: (1) Implement query validation and result confidence scoring - the chatbot will ask clarifying questions when queries are ambiguous, and flag results with confidence levels (High/Medium/Low). Include a "Show me the SQL" option so users can verify the generated query. (2) Create comprehensive database schema documentation and provide the AI with detailed metadata about tables, relationships, and business logic. Start with 3 well-documented databases before expanding to the 4th. (3) Implement role-based access control (RBAC) from day one - the chatbot will inherit the user's database permissions and audit all queries. Work with InfoSec to review the security model. (4) Run a 6-week pilot with 20 volunteer users (power users who are comfortable with data), gather feedback, and share success stories before broader rollout. (5) Use read-only database replicas for chatbot queries to avoid impacting production performance, and implement query timeout limits (30 seconds max).
```

**Why this works**:
- ✅ Proposes specific mitigation for each risk
- ✅ Shows phased approach (pilot with power users, gradual expansion)
- ✅ Involves stakeholders (InfoSec, volunteer users, power users)

---

#### Question 11: Build/Buy/Partner
**What to demonstrate**: Strategic approach decision

**Example Answer**:
```
Hybrid approach: Buy the core conversational AI platform (Azure Bot Framework + Azure OpenAI Service for GPT-4) and build custom NLP-to-SQL translation logic and SSRS integration in-house. The chatbot interface and LLM are commodity capabilities that are mature and well-supported by Microsoft Azure, so no need to build from scratch. However, our specific requirements - understanding our database schemas, generating Wells Fargo-specific SQL queries, integrating with SSRS security model, and implementing our unique business logic - require custom development. This approach reduces time-to-market by 2-3 months, leverages enterprise-grade AI services with built-in security and compliance, and gives us full control over data access and query generation logic.
```

**Why this works**:
- ✅ Selects clear approach (Hybrid: Buy Azure Bot + OpenAI, Build SQL generation)
- ✅ Provides rationale (leverage proven services, faster time-to-market, security)
- ✅ Shows strategic thinking

---

## Demo Tips

### 1. Pacing
- **Introduction (Q1)**: 30 seconds - Set the context quickly
- **Business Case (Q2-5)**: 3-4 minutes - Most important section
- **Technical Details (Q6-7)**: 2-3 minutes - Show feasibility
- **Feasibility (Q8)**: 1-2 minutes - Realistic planning
- **Risk Assessment (Q9-11)**: 2-3 minutes - Show maturity
- **Total time**: 10-12 minutes for complete workflow

### 2. What to Highlight
- **Static Mode Indicator**: Point out the "Static Mode" badge showing no API keys needed
- **Progress Tracking**: Show the step indicator (1 of 5) advancing
- **Circular Progress**: Highlight the overall progress percentage increasing
- **Clean UI**: Emphasize Wells Fargo branding and professional appearance

### 3. Follow-up Questions
If the system generates follow-up questions (in AI mode), demonstrate:
- The criteria validation system working
- How it asks for more detail when answers are incomplete
- Maximum 2 follow-ups per question to avoid user fatigue

### 4. Review Page
After completing all questions, the review page should show:
- Complete idea summary
- All collected data organized by category
- AI-generated recommendations (in AI modes)
- PDF download option
- Submit button

---

## Alternative Demo Scenarios

### Scenario 2: Mortgage Document Processing
**Idea**: AI-powered document extraction system for mortgage applications (pay stubs, tax returns, bank statements)
**Key benefits**: Reduce processing time from 3-4 hours to 15-20 minutes, 98% accuracy, $500K annual savings

### Scenario 3: Customer Service Chatbot
**Idea**: AI-powered chatbot for retail banking FAQs (account balance, transaction history, card activation)
**Key benefits**: 24/7 availability, reduce call center volume by 40%, instant responses

### Scenario 4: Fraud Detection Enhancement
**Idea**: ML model to identify fraudulent transactions in real-time using pattern analysis
**Key benefits**: Reduce false positives by 60%, catch fraud 48 hours earlier, save $2M annually

### Scenario 5: Investment Portfolio Summarization
**Idea**: GenAI system that creates personalized investment summaries for wealth management clients
**Key benefits**: Save advisors 2 hours per client review, improve client understanding, increase engagement

---

## Common Questions & Answers

**Q: "What if I don't know how to answer a question?"**
A: In AI-enabled modes (OpenAI/Ollama), the system offers AI assistance. In static mode, use the example responses as guidance.

**Q: "Can I go back and change answers?"**
A: Yes, you can edit any previous answer in the conversation flow.

**Q: "How long does the workflow take?"**
A: Typically 10-15 minutes for a complete submission with thoughtful answers.

**Q: "What happens after submission?"**
A: The idea is saved to the CSV database and a PDF intake form is generated for review by the GenAI team.

---

## Success Metrics

After the demo, participants should understand:
- ✅ How the conversational flow guides idea capture
- ✅ What level of detail is expected for each question
- ✅ How the system validates and ensures complete submissions
- ✅ The value of structured idea intake vs. free-form submissions

---

*Last Updated: 2025-11-05*
*Version: 1.0 - Static Mode Demo*
