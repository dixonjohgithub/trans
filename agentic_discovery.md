
# Why Open-Ended Agentic Discovery Fails and How Guided Agentic Discovery Outperforms Commercial “Automation Discovery” Tools

---

## 1. Introduction

A growing class of commercial platforms—such as **Skan.ai**, **Celonis**, and **UiPath Process Mining**—claim to provide *automated discovery* of business processes and automation opportunities by mining enterprise data.  

These tools bring real strengths in **process transparency** and **bottleneck visualization**, but their analytical foundation remains **descriptive**, not **prescriptive** or **generative**. They show *what happens*, but not *why it matters* or *how to fix it*.  

Similarly, **open-ended agentic discovery**—where an AI system explores multiple enterprise systems without clear direction—often produces an overwhelming amount of low-context information. The result: impressive dashboards but little actionable intelligence.

This document explains:
- Why unguided discovery (whether human-built or AI-based) fails  
- How commercial process mining tools fit into that same limitation  
- How **Guided Agentic Discovery** offers a measurable, KPI-anchored path forward  

---

## 2. The Promise and Pitfalls of Automation Discovery Tools

### 2.1. What Tools Like Skan.ai and Celonis Offer

| Tool | Core Strengths | Typical Use Cases |
|-------|----------------|-------------------|
| **Skan.ai** | Observes user workflows via desktop event capture and generates process maps | Detect repetitive digital tasks suitable for RPA |
| **Celonis** | Analyzes ERP and CRM event logs to detect inefficiencies and conformance gaps | Process optimization, order-to-cash acceleration |
| **UiPath Process Mining** | Combines event logs and task mining data to identify automation opportunities | Discovery of repetitive, rule-based tasks for bot deployment |

### 2.2. These Tools Excel At:
- **Mapping “as-is” workflows:** They reconstruct how a process *currently* operates using event logs or screen interactions.  
- **Identifying task-level inefficiencies:** They locate repetitive or slow steps that may be optimized or automated.  
- **Suggesting rule-based automation candidates:** They pinpoint activities that follow deterministic patterns (e.g., “always approve after step X”).  

**However**, their focus is primarily **descriptive**, not **prescriptive or generative**.

---

## 3. What “Descriptive, Not Prescriptive or Generative” Means

| Level | Purpose | Example Behavior | Analogy |
|--------|----------|------------------|----------|
| **Descriptive** | Answers *“What is happening?”* by analyzing existing data | Celonis identifies that 30% of invoices take longer than 5 days to approve | A speedometer—it shows current speed |
| **Diagnostic** | Answers *“Why is it happening?”* through correlation | Finds that delays occur when vendor ID is missing | A mechanic explaining why you slowed down |
| **Prescriptive** | Answers *“What should we do?”* by recommending actions | Suggests automation of vendor ID validation | A GPS suggesting a better route |
| **Generative** | Answers *“What new process could work better?”* by designing and simulating improvements | Proposes an AI agent that predicts missing IDs and routes approvals automatically | An autopilot that replans the entire route in real time |

Thus, **Skan.ai and Celonis** excel in **descriptive** visibility but **do not reason about solutions or redesign processes automatically**.

They’re “process mirrors,” not “process architects.”

---

## 4. The Limitations of Open-Ended and Commercial Discovery Approaches

| Limitation | Description | Business Impact |
|-------------|--------------|-----------------|
| **Domain-Agnostic** | Tools analyze all logs equally, regardless of business context | Irrelevant automation ideas across domains |
| **No KPI Alignment** | Findings are not tied to measurable performance metrics | Unclear ROI; results hard to prioritize |
| **Reactive** | Focused on existing data; cannot anticipate or simulate outcomes | Limited foresight and adaptability |
| **Static** | Models require periodic manual updates and data reloads | Missed continuous optimization opportunities |
| **Human-Dependent Synthesis** | Require analysts to interpret dashboards and write business cases | Slower adoption and inconsistent decision-making |

> In essence: they tell *you what happened*, but not *what to do next*.

---

## 5. Why Open-Ended Agentic Discovery Fails

Even when internal AI systems are designed to explore enterprise data autonomously, they face the same failure modes as these tools when operating without a domain hypothesis or business constraints:

1. **No Domain Context:** Without business boundaries (e.g., HR, IT, Finance), the AI cannot judge importance or ownership.  
2. **No KPIs or Success Criteria:** The AI cannot define what success looks like, producing findings that lack measurable impact.  
3. **Irrelevant Insights:** The AI finds anomalies but cannot determine if they are meaningful or actionable.  
4. **Governance Risk:** Broad, cross-system access increases privacy and compliance exposure.  
5. **No Value Translation:** Raw discoveries lack linkage to strategic objectives or ROI modeling.  

This results in an “AI in search of a problem” scenario—lots of noise, little transformation.

---

## 6. Guided Agentic Discovery: A Strategic Upgrade

### 6.1. Concept

**Guided Agentic Discovery** is a next-generation framework that merges AI’s pattern recognition power with strategic focus. It uses **domain anchors, KPI alignment, and hypothesis-driven reasoning** to produce actionable, measurable outputs.  

It goes beyond Celonis-style process mapping by **prescribing solutions**, **simulating impact**, and **automatically generating business cases**.

---

### 6.2. Core Principles

| Principle | Description |
|------------|--------------|
| **Domain Anchoring** | Start discovery within a defined business domain (HR, IT, Finance, Compliance). |
| **KPI-Driven Analysis** | Define measurable success metrics in advance. |
| **Hypothesis Framing** | Begin with a testable statement (e.g., “Access approval bottlenecks delay onboarding”). |
| **Governed Data Access** | Restrict to necessary data sources with privacy and ownership rules. |
| **Automated Business Case Generation** | Each finding outputs a structured “Problem → Evidence → Solution → Value → Effort” summary. |

---

## 7. Guided Agentic Discovery Architecture

### 7.1. Domain Configuration Example

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

### 7.2. Agent Roles

| Agent                 | Function                                                | Output                                  |
| --------------------- | ------------------------------------------------------- | --------------------------------------- |
| **Pattern Agent**     | Identifies recurring patterns within scoped domain data | Clustered issues and frequency analysis |
| **KPI Agent**         | Compares findings to baseline metrics                   | KPI deviation report                    |
| **Feasibility Agent** | Assesses data readiness and technical integration paths | Feasibility score                       |
| **Value Agent**       | Quantifies potential impact and ROI                     | Value projection                        |
| **Storycraft Agent**  | Produces a structured business case summary             | AI-generated business case document     |

---

## 8. Comprehensive Use Case Example: HR Domain

### **Title:** AI-Driven Onboarding Process Optimization

---

### **1. Problem Definition**

**Observation:** Onboarding is delayed due to manual access approvals.
**Hypothesis:** Automating system access requests via ServiceNow will reduce onboarding cycle time and improve productivity.

---

### **2. Domain Context**

| Aspect           | Description                                                                    |
| ---------------- | ------------------------------------------------------------------------------ |
| **Domain**       | Human Resources                                                                |
| **Process**      | Onboarding and Access Management                                               |
| **Data Sources** | Workday (tasks, completion times), ServiceNow (tickets), SharePoint (policies) |
| **Stakeholders** | HR Operations, IT Access, Compliance                                           |

---

### **3. Baseline Metrics**

| KPI                       | Current   | Target      | Success Criteria |
| ------------------------- | --------- | ----------- | ---------------- |
| Time to Productivity      | 8.5 days  | ≤ 5 days    | 40% improvement  |
| Access Request Cycle Time | 5.2 days  | ≤ 2 days    | 60% improvement  |
| Ticket Volume             | 420/month | ≤ 200/month | 50% reduction    |

---

### **4. Agent Findings**

**Pattern Agent:**

* 43% of hires delayed >5 days due to system access waits.

**KPI Agent:**

* Median onboarding duration: 8.5 days (+70% vs. target).
* Estimated productivity loss: $350/employee.

**Feasibility Agent:**

* APIs for auto-ticket generation confirmed.
* RAU compliance validated for automation.

**Value Agent:**

* Predicted 3.5-day reduction per hire.
* Annual value: ~$420K in recovered productivity.

**Storycraft Agent:**

* Drafts business case for “AI Onboarding Orchestration Agent” with success metrics, implementation roadmap, and ROI.

---

### **5. Success Metrics**

| Measure                        | Target | Review Cycle |
| ------------------------------ | ------ | ------------ |
| Time-to-Productivity Reduction | ≥ 30%  | Monthly      |
| Ticket Automation Rate         | ≥ 50%  | Monthly      |
| Productivity Gain              | ≥ 25%  | Quarterly    |
| HR Stakeholder Satisfaction    | ≥ 90%  | Biannual     |

---

## 9. Comparative Analysis: Process Mining vs. Guided Agentic Discovery

| Attribute                | Celonis / Skan.ai                  | Guided Agentic Discovery                 |
| ------------------------ | ---------------------------------- | ---------------------------------------- |
| **Discovery Mode**       | Reactive and descriptive           | Hypothesis-driven and prescriptive       |
| **Output**               | Process map or inefficiency report | AI-generated business case               |
| **KPI Integration**      | Optional or manual                 | Embedded and required                    |
| **Reasoning Capability** | Pattern recognition                | Causal reasoning and solution generation |
| **Governance**           | Broad data ingestion               | Scoped by domain                         |
| **Adoption Readiness**   | Requires human interpretation      | Ready for PM and exec review             |
| **Automation Scope**     | Rule-based RPA tasks               | AI + Automation orchestration            |

---

## 10. Strategic Positioning

**Process-mining tools** (Skan.ai, Celonis) deliver **retrospective insight**:

> “Here’s how your process runs and where it’s inefficient.”

**Guided Agentic Discovery** delivers **strategic foresight**:

> “Here’s why your process is underperforming, what can fix it, how much value it delivers, and who should own the fix.”

---

## 11. Key Takeaways

1. Commercial discovery tools reveal **what is happening**, not **what should happen**.
2. Open-ended agentic discovery repeats that mistake—broad, unguided, and hard to act on.
3. Guided Agentic Discovery introduces **intent, governance, and measurable outcomes**.
4. It merges **AI reasoning** with **enterprise KPIs** to turn discovery into decision-making.

---

## 12. Summary Statement

> Process-mining tools and open-ended agentic discovery both create visibility.
> Guided Agentic Discovery creates **direction**—anchored in business goals, governed by data access, and measured by real-world impact.

It is not just about seeing inefficiencies; it’s about **engineering transformation**.

```
```
