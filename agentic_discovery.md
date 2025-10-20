
# Why Open-Ended Agentic Discovery Fails and How Guided Agentic Discovery Outperforms Commercial “Automation Discovery” Tools

---

## 1. Introduction

A new wave of commercial platforms—like **Skan.ai**, **Celonis**, **UiPath Process Mining**, and similar **“automation discovery”** or **“process intelligence”** products—claim to deliver AI-driven automation discovery by mining enterprise data.  

While these tools provide valuable **process visualization**, **bottleneck detection**, and **automation opportunity insights**, they largely operate as **data-driven process mining engines**, not **agentic discovery systems**.  

More importantly, they inherit many of the same limitations of **open-ended agentic discovery**, particularly when used without clear business context, defined KPIs, or domain constraints.  

This paper explains **why unguided AI discovery fails**, **how emerging tools partially address the gap**, and **why a guided, domain-specific agentic discovery framework** offers a more strategic, value-aligned solution.

---

## 2. The Promise and Pitfalls of Automation Discovery Tools

### 2.1. What Tools Like Skan.ai and Celonis Offer

| Tool | Core Strengths | Typical Use Cases |
|-------|----------------|-------------------|
| **Skan.ai** | Computer vision and system telemetry-based process capture; generates process maps from employee workflows | Discovering repetitive digital tasks for RPA automation |
| **Celonis** | Enterprise process mining; correlates event logs across ERP/CRM systems (SAP, Salesforce, Workday) to identify inefficiencies | Process optimization, bottleneck identification, compliance drift detection |
| **UiPath Process Mining** | Event log–based process mapping tied to automation design tools | Discovering automation candidates for UiPath bots |

These tools excel at:
- Mapping **“as-is” workflows**  
- Identifying **task-level inefficiencies**  
- Suggesting **rule-based automation candidates**  

They provide clear operational visibility, but their focus is **descriptive**, not **prescriptive or generative**.  

---

### 2.2. The Limitations of These Tools

| Limitation | Description | Implication |
|-------------|--------------|-------------|
| **Domain-Agnostic** | Designed to scan all available data sources (ERP, CRM, HR, Finance) without business framing | Leads to irrelevant or low-value automation suggestions |
| **No KPI Alignment** | Findings are often not benchmarked against strategic or departmental KPIs | Hard to link discovered “inefficiencies” to measurable ROI |
| **Reactive Analysis** | Discover patterns in existing logs but cannot reason about *why* inefficiencies occur or how to solve them | Limited to “process snapshots” without predictive or adaptive recommendations |
| **Static Discovery** | Once process logs are mapped, systems require manual refresh and human interpretation | Discovery is not continuous or autonomous |
| **Limited Integration with AI Reasoning Agents** | Tools detect patterns but do not *synthesize business cases*, *assess feasibility*, or *simulate outcomes* | Organizations still rely on analysts to connect discovery → value → execution |

> In short, tools like **Celonis and Skan.ai** answer *“What is happening?”* but not *“Why does this matter, and what should we do about it?”*

---

## 3. Why Open-Ended Agentic Discovery Still Fails

Even if enterprise AI agents were deployed with unrestricted access to systems like Workday, ServiceNow, and SharePoint, they would face the same structural problems as commercial process-mining tools when used without **guidance**.

### 3.1. No Domain Context
Without business-domain constraints (HR, Finance, IT, Compliance), AI lacks a conceptual framework for **value assessment** or **ownership**.

### 3.2. Lack of KPI Anchors
AI cannot know whether a pattern represents a problem or normal variance without metrics like *mean time to resolve*, *cost per incident*, or *policy compliance thresholds*.

### 3.3. Misaligned Objectives
AI might find thousands of anomalies, but with no ranking or business linkage, the output becomes overwhelming.

### 3.4. Governance and Security Concerns
Open access to multiple enterprise systems introduces compliance risk, data redundancy, and integration complexity.

---

## 4. Guided Agentic Discovery: The Next Generation Approach

### 4.1. Conceptual Shift

**Guided Agentic Discovery** builds upon the strengths of process-mining tools (like Celonis) but adds:
- **Business-domain anchoring**
- **KPI- and hypothesis-driven reasoning**
- **Autonomous business case generation**
- **Cross-system context synthesis**

This approach transforms discovery from a **bottom-up pattern finder** into a **top-down strategy-aligned intelligence layer**.

---

### 4.2. Core Principles

| Principle | Description |
|------------|--------------|
| **Domain Anchoring** | Start with a single business area (HR, IT, Finance) and define measurable goals. |
| **KPI Integration** | Link findings to strategic and operational metrics. |
| **Hypothesis-Driven Exploration** | Use AI to validate business hypotheses rather than search blindly. |
| **Governed Data Access** | Limit data pulls to only relevant systems and datasets. |
| **Automated Business Case Generation** | Every insight is output as a structured, quantifiable proposal ready for Product Management review. |

---

## 5. Guided Agentic Discovery Architecture

### 5.1. Domain Configuration

Each domain defines:
- Approved systems and APIs  
- Baseline metrics (KPIs)  
- Success thresholds and cost models  
- Ownership and review cadence  

**Example: HR Domain Configuration**
```yaml
domain: Human Resources
primary_systems:
  - Workday
  - ServiceNow
kpis:
  - time_to_productivity_days
  - onboarding_completion_rate
  - access_request_cycle_time
success_thresholds:
  time_to_productivity_days: < 5
  onboarding_completion_rate: > 95%
  access_request_cycle_time: < 2
business_owner: VP_HR_Operations
```

### 5.2. Agent Layers and Roles

| Agent                 | Purpose                                            | Key Output                                      |
| --------------------- | -------------------------------------------------- | ----------------------------------------------- |
| **Pattern Agent**     | Finds recurring patterns within scoped domain data | Bottleneck clusters and frequency tables        |
| **KPI Agent**         | Measures deviation from baselines                  | KPI deltas, success-gap summaries               |
| **Feasibility Agent** | Tests if identified fixes are practical            | System readiness, policy alignment              |
| **Value Agent**       | Quantifies time or cost savings                    | ROI estimate, impact score                      |
| **Storycraft Agent**  | Converts discovery into business case documents    | Problem → Evidence → Solution → Impact template |

---

## 6. Comprehensive Example: HR Domain (Guided Version)

### **Title:** AI-Driven Onboarding Process Optimization

---

### **1. Problem Definition**

**Observation:** Employees face onboarding delays due to manual access approval workflows.
**Impact:** Extended “time-to-productivity” and reduced employee satisfaction.

**Hypothesis:**

> Automating access requests and approvals will reduce onboarding delays and improve operational efficiency.

---

### **2. Domain Context**

| Aspect           | Description                                                                           |
| ---------------- | ------------------------------------------------------------------------------------- |
| **Domain**       | Human Resources                                                                       |
| **Process**      | Employee Onboarding and Access Management                                             |
| **Data Sources** | Workday (Onboarding Steps), ServiceNow (Access Tickets), SharePoint (Access Policies) |
| **Stakeholders** | HR Operations, IT Access Team, Compliance                                             |

---

### **3. Baseline Metrics and KPIs**

| KPI                        | Current   | Target      | Success Criteria   |
| -------------------------- | --------- | ----------- | ------------------ |
| Time-to-Productivity       | 8.5 days  | ≤ 5 days    | 40% improvement    |
| Access Request Cycle Time  | 5.2 days  | ≤ 2 days    | 60% improvement    |
| Manual Ticket Volume       | 420/month | ≤ 200/month | 50% reduction      |
| Onboarding Completion Rate | 82%       | ≥ 95%       | Higher consistency |

---

### **4. Agent Findings**

**Pattern Agent:**

* 43% of onboarding cases delayed >5 days due to pending access approvals.
* 64% of delays originate from 3 core systems (VPN, Payroll, CRM).

**KPI Agent:**

* Median onboarding duration: 8.5 days.
* Deviation from KPI target: +70%.
* Correlated productivity loss per hire: $350.

**Feasibility Agent:**

* APIs exist for automated ServiceNow ticket generation.
* Access automation aligns with compliance RAUs.

**Value Agent:**

* Predicted reduction in onboarding time: 3.5 days.
* Annual value recovery: ~$420K (based on average onboarding cost × staff volume).

**Storycraft Agent:**

* Drafts formal business case with quantified ROI, risks, and implementation roadmap.

---

### **5. Success Criteria**

| Measure                   | Target | Source             | Review Cycle |
| ------------------------- | ------ | ------------------ | ------------ |
| Onboarding Time Reduction | ≥30%   | Workday Logs       | Monthly      |
| Access Request Automation | ≥50%   | ServiceNow Metrics | Monthly      |
| Productivity Gain         | ≥25%   | HR Survey + KPIs   | Quarterly    |
| Stakeholder Satisfaction  | ≥90%   | HR Feedback Portal | Biannual     |

---

## 7. Comparison: Commercial Process-Mining vs Guided Agentic Discovery

| Attribute                 | Celonis / Skan.ai                | Guided Agentic Discovery             |
| ------------------------- | -------------------------------- | ------------------------------------ |
| **Discovery Mode**        | Reactive, event-log-based        | Proactive, hypothesis-driven         |
| **Scope**                 | Enterprise-wide, domain-agnostic | Domain-specific (HR, IT, Finance)    |
| **Output Type**           | Process inefficiency report      | Business case with KPI & ROI         |
| **AI Role**               | Descriptive analytics            | Prescriptive reasoning and synthesis |
| **Governance**            | Limited contextual governance    | Strict data-scoped access            |
| **Adoption Readiness**    | Requires manual interpretation   | Ready-to-execute use cases           |
| **Integration with LLMs** | Minimal (rule-based)             | High (semantic and reasoning-driven) |

---

## 8. Strategic Positioning: Beyond Process Mining

Where **Skan.ai** and **Celonis** *describe* how work happens, **Guided Agentic Discovery** *decides what should happen next*.

* **Process Mining = Retrospective Insight**
  “Here’s how your process flows and where it’s inefficient.”
* **Guided Agentic Discovery = Strategic Foresight**
  “Here’s the root cause, its impact, and an executable AI-driven fix tied to KPIs.”

---

## 9. Key Takeaways

1. **Open-ended discovery** and many current commercial tools generate volume, not value.
2. **Guided discovery** introduces intent, metrics, and governance—producing actionable business cases, not dashboards.
3. **Agentic discovery frameworks** extend process mining into *continuous, context-aware improvement loops*.
4. AI must evolve from a **pattern detector** into a **domain reasoning engine** that ties every insight to measurable business outcomes.

---

## 10. Recommended Next Steps

1. Select 2–3 **pilot domains** (e.g., HR Onboarding, IT Incident Management).
2. Define **baseline KPIs and hypotheses** per domain.
3. Configure **domain-bound agents** with limited, governed access.
4. Generate and validate **AI-synthesized business cases**.
5. Compare results vs. commercial discovery tools to measure business case accuracy and ROI.

---

## 11. Final Summary

> Commercial tools like **Skan.ai** and **Celonis** provide excellent visibility into “how work happens,” but they stop short of *why it matters* and *what to do next*.
>
> **Guided Agentic Discovery** goes further—anchoring AI in business domains, success metrics, and organizational strategy to transform raw discovery into high-confidence, high-value decisions.

---

```
```
