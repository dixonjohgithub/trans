````markdown
# Why Open-Ended Agentic Discovery Fails and How to Design Guided Agentic Discovery Systems

---

## 1. Introduction

Many enterprises are exploring **Agentic AI Discovery**—AI systems that autonomously mine data from internal platforms (e.g., Workday, ServiceNow, SharePoint, RAUs, Tech Spend) to identify potential automation or AI use cases.  

While this approach sounds innovative, **open-ended discovery**—granting AI broad access to multiple systems without predefined goals—often fails to generate meaningful or actionable insights. This document outlines **why unguided approaches fail**, how **guided agentic discovery** corrects those shortcomings, and what a **comprehensive use case definition** requires.

---

## 2. Why Open-Ended Agentic Discovery Fails

### 2.1. No Domain Context
When AI agents access multiple enterprise systems without a defined **business domain**, they lack the context to evaluate what matters.  
- **Problem:** AI surfaces patterns (“many tickets mention ‘delay’”) without understanding whether that delay is meaningful or costly.  
- **Result:** Noise is mistaken for insight.  

> Example: Mining ServiceNow + Workday + SharePoint simultaneously may find “repeated approval mentions” but cannot distinguish if they relate to HR onboarding, IT access, or procurement workflows.

---

### 2.2. No Defined KPIs or Success Criteria
Without predefined metrics, discovery becomes subjective. The AI cannot measure whether a pattern is good or bad.  
- **Problem:** “Average ticket resolution time is 3 days” — Is that acceptable or inefficient?  
- **Result:** No measurable ROI or clear business case emerges.  

> Without KPIs (e.g., “reduce MTTR from 3 days to 1 day”), the AI has no way to link its discovery to value.

---

### 2.3. Data Without Intent = Irrelevance
Data pulled from systems like Workday or SharePoint contain diverse operational information. Without a hypothesis or objective, AI lacks an **intent filter**.  
- **Problem:** The AI highlights anomalies that may have no business relevance.  
- **Result:** Analysts must spend more time filtering AI findings than solving real problems.

---

### 2.4. Lack of Governance and Prioritization
Unguided exploration typically involves:
- Broad system access
- Undefined data use boundaries
- Overlapping signals from different systems

This creates governance and security risks, while also producing **duplicate, low-value discoveries**.

---

### 2.5. “AI in Search of a Problem” Syndrome
The most significant failure mode is when AI generates outputs that **sound interesting but have no owner or actionable path**.  
- No alignment to business goals  
- No stakeholder buy-in  
- No measure of success or feasibility  

> The result is a showcase of patterns—without transformation.

---

## 3. Transitioning to Guided Agentic Discovery

Guided discovery reframes AI not as an autonomous explorer, but as a **decision-support partner** operating within structured domains, metrics, and governance boundaries.

### 3.1. Core Principles

| Principle | Description |
|------------|--------------|
| **Domain Anchoring** | Define one business domain per discovery cycle (e.g., HR, IT, Finance, Compliance). |
| **Hypothesis-Driven** | Start with a clear assumption or question (e.g., “Access approval bottlenecks delay onboarding”). |
| **KPI-Aligned** | Tie discoveries to quantifiable success criteria. |
| **Governed Data Access** | Connect only to the systems required for that domain’s hypothesis. |
| **Business Case Outputs** | Every discovery must produce a measurable problem statement and an actionable proposal. |

---

## 4. Architecture Overview: Guided Agentic Discovery

### 4.1. Domain Configuration

Each domain has:
- Defined KPIs and success thresholds  
- Approved systems and connectors  
- Historical baseline data  
- Responsible business owner and SME  

**Example: HR Domain Configuration**
```yaml
domain: Human Resources
primary_systems:
  - Workday
  - ServiceNow
kpis:
  - time_to_productivity_days
  - approval_cycle_time
  - onboarding_completion_rate
success_thresholds:
  time_to_productivity_days: < 3
  onboarding_completion_rate: > 95%
business_owner: VP_HR_Operations
````

---

### 4.2. Agent Layers and Roles

| Agent                 | Purpose                                                                            | Key Output                                   |
| --------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------- |
| **Pattern Agent**     | Finds recurring events, bottlenecks, or anomalies within defined domain boundaries | Frequency tables, root-cause clusters        |
| **KPI Agent**         | Maps findings to defined metrics and baseline thresholds                           | Metric deviation reports, KPI delta analysis |
| **Feasibility Agent** | Assesses data accessibility, process readiness, and integration paths              | Feasibility index (Low/Medium/High)          |
| **Value Agent**       | Estimates time/cost savings or risk reduction                                      | ROI projection and impact score              |
| **Storycraft Agent**  | Converts validated insights into human-readable business cases                     | Business case template with supporting data  |

---

## 5. Example: Comprehensive HR Use Case

### **Title:** Onboarding Process Optimization through AI-Driven Access Orchestration

---

### **1. Problem Definition**

**Observation:** New employee onboarding is delayed by manual approval and system access processes.
**Impact:** Delays reduce productivity and increase operational overhead.

**Hypothesis:**

> Automating system access approvals and pre-generating requests can reduce onboarding delays and improve productivity.

---

### **2. Domain Context**

| Aspect           | Description                                                                              |
| ---------------- | ---------------------------------------------------------------------------------------- |
| **Domain**       | Human Resources                                                                          |
| **Process**      | Onboarding & Access Management                                                           |
| **Data Sources** | Workday (Onboarding Workflow), ServiceNow (Access Tickets), SharePoint (Access Policies) |
| **Stakeholders** | HR Operations, IT Access Management, Security Compliance                                 |

---

### **3. Baseline Metrics & KPIs**

| KPI                         | Current Value | Target Value | Success Criteria       |
| --------------------------- | ------------- | ------------ | ---------------------- |
| Time to Productivity (Days) | 8.5 days      | ≤ 5 days     | 40% reduction          |
| Access Request Cycle Time   | 5.2 days      | ≤ 2 days     | 60% reduction          |
| Onboarding Completion Rate  | 82%           | ≥ 95%        | Completion improvement |
| Manual Ticket Volume        | 420/month     | ≤ 200/month  | 50% reduction          |

---

### **4. Data Access and Feasibility**

| Source         | Data Retrieved                                | Feasibility                                  |
| -------------- | --------------------------------------------- | -------------------------------------------- |
| **Workday**    | Onboarding tasks, step completion times       | API access confirmed                         |
| **ServiceNow** | Access request tickets, resolution timestamps | Moderate; requires data-sharing agreement    |
| **SharePoint** | Policy documents on access governance         | Low sensitivity; read-only access sufficient |

---

### **5. Agent Findings**

**Pattern Agent:**

* 43% of new hires experience >5-day delay due to pending access approvals.
* 64% of delays involve the same 3 systems (VPN, Payroll, CRM).

**KPI Agent:**

* Median onboarding completion = 8.5 days → exceeds 5-day goal by 70%.
* Access approval backlog correlates with 0.35 productivity index drop.

**Feasibility Agent:**

* APIs available for auto-triggering access workflows in ServiceNow.
* Compliance check confirms automation permissible with approval logs.

**Value Agent:**

* Estimated 3.5-day reduction per hire → 30K staff-hours saved annually.
* Cost avoidance: ~$420,000 in lost productivity recovered per year.

---

### **6. Proposed Solution**

**AI Onboarding Orchestration Agent**

* Predicts system access needs based on job role and department.
* Pre-generates ServiceNow access tickets upon Workday hire event.
* Tracks approval chain, sends reminders, and verifies access completion.

---

### **7. Measurable Success Criteria**

| Success Metric                         | Measurement Method   | Review Interval |
| -------------------------------------- | -------------------- | --------------- |
| 30% reduction in onboarding time       | Workday task logs    | Monthly         |
| 50% reduction in manual access tickets | ServiceNow analytics | Monthly         |
| >90% access approval compliance        | Access audit logs    | Quarterly       |
| 95% user satisfaction                  | HR survey data       | Biannual        |

---

### **8. Output: Business Case Summary**

| Element              | Description                                                                       |
| -------------------- | --------------------------------------------------------------------------------- |
| **Problem**          | Access approval delays increase onboarding cycle time and cost.                   |
| **Evidence**         | Data correlation from Workday + ServiceNow shows average 8.5-day onboarding time. |
| **Solution**         | Deploy AI-driven orchestration agent to preempt and automate access approvals.    |
| **Expected Benefit** | 3.5-day average reduction in onboarding time, ~$420K cost savings/year.           |
| **Feasibility**      | APIs and compliance support available; minimal technical debt.                    |
| **Owner**            | VP HR Operations                                                                  |
| **Next Step**        | Pilot within 1 department, evaluate in 60 days.                                   |

---

## 6. Design Comparison: Open vs Guided Discovery

| Attribute                  | Open-Ended Discovery                | Guided Discovery                        |
| -------------------------- | ----------------------------------- | --------------------------------------- |
| **Starting Point**         | Data access across multiple systems | Specific business domain and hypothesis |
| **Data Governance**        | Broad, loosely controlled           | Scoped per domain with approval         |
| **Outputs**                | Interesting patterns, correlations  | Business cases with quantified ROI      |
| **Stakeholder Engagement** | Low; unclear ownership              | High; tied to business KPIs             |
| **Adoption Likelihood**    | Low (abstract insights)             | High (actionable evidence)              |
| **Trust and Governance**   | Weak; unclear boundaries            | Strong; governed and auditable          |

---

## 7. Key Takeaways

1. **Open-ended discovery** looks powerful but fails without domain context, metrics, and constraints.
2. **Guided discovery** is more mature—it starts with a purpose, integrates metrics, and produces actionable business outcomes.
3. The transition requires defining:

   * Problem hypothesis
   * KPIs and success thresholds
   * Data sources and access boundaries
   * Ownership and accountability
4. A **guided agentic discovery system** transforms AI from a pattern finder into a **strategic business accelerator**.

---

## 8. Recommended Next Steps

1. Identify **two pilot domains** (e.g., HR Onboarding, IT Incident Management).
2. Define **baseline metrics and hypotheses** per domain.
3. Deploy **domain-specific agent pipelines** with limited data access.
4. Review outputs for **business case quality, feasibility, and ROI**.
5. Scale across additional domains using the same guided framework.

---

## 9. Summary Statement

> **Open-ended agentic discovery** is like giving AI a flashlight in a dark warehouse—it finds a lot, but not necessarily what you need.
> **Guided agentic discovery** installs lights only where the business works, measures illumination, and ensures every new insight drives measurable value.

---

```
```
