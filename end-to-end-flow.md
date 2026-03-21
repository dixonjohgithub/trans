# Agentic Intake System — End-to-End Flow

This document describes the complete end-to-end flow of the Agentic Intake System, from the moment a user opens the catalog page to receiving a ticket confirmation after submission.

---

## Step 1: User Selects an Intake from the Catalog

### Frontend (`CatalogPage.tsx`)

1. Page mounts → `useIntakeCatalog` hook fires → calls `GET /api/configs`
2. **Backend** (`routes/config.py`): `FileConfigService.list_configs()` scans `backend/app/configs/`, loads all 12 YAML files via `yaml.safe_load()`, validates each against the `IntakeConfig` Pydantic model, and returns summaries (id, name, description, icon, enabled, question counts, steps)
3. Frontend renders a 12-card grid. 1 card is enabled ("Product Feature Intake"), 11 are disabled ("Coming Soon")
4. User clicks the enabled card → `handleCardSelect("product_feature_intake")` fires

### With MongoDB (future)

Step 2 above would change to `MongoConfigService.list_configs()` doing a `db.configs.find()` query instead of scanning the filesystem. The YAML files would have already been imported into MongoDB at startup.

---

## Step 2: Load the YAML Config and Create a Session

**Frontend** calls `POST /api/sessions` with `{ user_id: "user-default", product: "product_feature_intake" }`

### Backend (`routes/sessions.py`)

1. `config_service.get_config("product_feature_intake")` loads the **full** YAML config — all 8 questions, validation criteria, steps, platform config, field aggregation rules
2. Creates a session ID (UUID)
3. Initializes ADK session state with the **entire config embedded**:

```python
initial_state = {
    "product": "Product Feature Intake",
    "config": { ... entire YAML config dict ... },
    "current_question_index": 0,
    "total_questions": 8,
    "current_question_validated": False,
    "current_question_attempts": 0,
    "current_guidance": None,
    "answers": {},
    "status": "in_progress",
    "ticket_id": None,
    "ticket_url": None,
}
```

4. Stores session in `InMemorySessionService`
5. Returns `SessionInfo` to the frontend (session_id, product name, question counts, steps)

**Key insight: The config is loaded ONCE at session creation and embedded in session state. It is NOT re-read from YAML/MongoDB for every question.** Every subsequent chat request reads the config from `state["config"]`.

---

## Step 3: The Conversation Begins

### Frontend (`IntakePage.tsx`)

1. Navigates to `/intake/{session_id}`
2. Calls `GET /api/sessions/{session_id}/status` to get initial state (0 answered, all steps upcoming)
3. Renders: step indicator, progress bar (0%), sidebar ring (0%), chat window
4. Sends an initial greeting message via `POST /api/chat/{session_id}` to trigger the first agent response

### Backend (`routes/chat.py`)

1. Looks up session from `InMemorySessionService`
2. Generates a `trace_id` for log correlation
3. Creates an `AuditLogger` scoped to this request
4. Logs the user message
5. Routes to either mock agent (`USE_MOCK_AGENT=true`) or real ADK agent runner

---

## Step 3a: The Agent Processes Each Turn (Real ADK Mode)

The agent is a **single `LlmAgent`** with a dynamic instruction that adapts based on session state. It was built once at startup via `build_orchestrator()` and is reused for every request.

### For each `POST /api/chat/{session_id}`

1. `_agent_event_stream()` wraps the user message in ADK `Content` format
2. Calls `runner.run_async()` which sends the message to the agent
3. The agent receives a **dynamic instruction** built by `_build_intake_instruction()` that includes:
   - The current question text, type, and validation criteria (from `state["config"]`)
   - The attempt count and any retry guidance
   - All prior answers for context
   - Rules for what tools to call and when

The agent then decides what to do based on the user's message.

---

## The Question-Answer Cycle (Steps 3-4 in Detail)

### User Gives a Substantive Answer

1. **Agent evaluates** the answer against the YAML validation criteria:
   - `min_length`: Is it long enough?
   - `must_include_keywords`: Does it mention required terms?
   - `format`: Does it match the expected pattern?
   - `requires_justification`: Is there a "why"?
   - `guideline`: General quality guidance

2. **If the answer PASSES validation:**
   - Agent calls `store_answer_tool(question_id="q1", response="...", validated=True)`
     - `state_tools.store_answer()` writes to `state["answers"]["q1"] = { response, validated: True, skipped: False, attempts: N }`
   - Agent calls `advance_question_tool()`
     - `state_tools.advance_question()` increments `current_question_index`, resets `attempts` to 0, clears `guidance`
   - Agent responds with acknowledgment + asks the next question
   - **Backend** detects state change via `_emit_state_change_events()`:
     - Emits `progress` SSE event (questions_answered: 1, remaining: 7)
     - Emits `step_change` SSE event if the new question is in a different step
     - Emits `ui_control` SSE event if the next question is dropdown/multi-select

3. **If the answer FAILS validation (attempt < 3):**
   - Agent calls `increment_attempts_tool()`
     - `state_tools.increment_attempts()` bumps `current_question_attempts`
   - Agent calls `set_guidance_tool(guidance="Your answer needs to be at least 50 characters and include the business problem...")`
     - `state_tools.set_guidance()` stores the feedback in `current_guidance`
   - Agent responds with specific, helpful feedback explaining what's missing
   - **No progress events emitted** — the user stays on the same question
   - Next turn: the dynamic instruction includes the retry guidance, so the agent knows this is a retry

4. **If the answer FAILS validation (attempt = 3, max reached):**
   - Agent calls `store_answer_tool(validated=False)` — force-accepts the best available answer
   - Agent calls `advance_question_tool()` — moves on
   - Agent explains it's accepting the answer and moving forward

### User Says "I don't know" / "help me"

1. Agent recognizes this as a help request (from the dynamic instruction rules)
2. Agent synthesizes context from:
   - Prior answers in `state["answers"]`
   - Current question's `guideline` from the YAML criteria
   - Question text and type
3. Agent suggests or drafts an answer and asks the user to confirm or modify it
4. **No tools called yet** — the suggested answer still needs to go through validation

### User Says "skip"

1. Agent checks if the current question has `required: True`
   - **If required:** Agent responds "This question is required and cannot be skipped"
   - **If optional:** Agent calls `skip_question_tool()`
     - `skip_tool.skip_question()` stores the `skip_default` value from the YAML config
     - Advances the question index
     - Returns `{ status: "skipped" }`
2. Backend emits `progress` event

### User Selects a Dropdown/Multi-Select Option

1. Frontend rendered pill buttons or chips from the `ui_control` SSE event
2. User clicks an option → frontend sends the selection as a regular chat message
3. Agent validates the selection against `allowed_values` / `max_selections` from the criteria
4. Same validation cycle as text answers

---

## Step 5: Submission (After All 8 Questions)

When `current_question_index >= total_questions`:

1. **The dynamic instruction shifts to "Review & Submit" phase**

2. Agent calls `aggregate_fields_tool()`
   - `aggregation_tool.aggregate_fields()` maps all answers to platform fields:
     - Reads each answer's `platform_field` from the question config
     - If two questions map to the same field (e.g., both q1 and q2 map to "description"), applies the `field_aggregation` config (separator + template)
     - Skipped answers with `None` response are omitted
   - Stores the aggregated payload in `state["submission_payload"]`

3. Agent presents a formatted review summary to the user:
   > "Here's a summary of your intake: ..."
   > "Does this look correct? Say 'yes' to submit."

4. Backend also emits a `ui_control` event with `control: "review_actions"` containing all Q&A data so the frontend can offer a "Save as JSON" download

5. **User confirms** → Agent calls `submit_intake_tool()`
   - `submit_tool.submit_intake()`:
     - Reads `platform.type` from config (e.g., "test" or "jira")
     - Gets the appropriate adapter from `ADAPTER_REGISTRY`
     - Calls `adapter.submit(payload, platform_config)`
     - **Test Adapter:** Generates fake ticket ID "TEST-{timestamp}", logs summary
     - **Jira Adapter:** Calls `jira.issue_create()` via atlassian-python-api
   - On success: stores `ticket_id` and `ticket_url` in session state, sets `status: "submitted"`

6. Backend detects `ticket_id` changed → emits `submission_result` SSE event

---

## Step 6: User Gets Confirmation

**Frontend** receives the `submission_result` SSE event:

1. `chatStore.setSubmissionResult({ ticketId, ticketUrl })`
2. `SubmissionSuccess` component renders:
   - Green checkmark
   - "Your intake has been submitted!"
   - Ticket ID as a clickable link
   - Progress ring jumps to 100%
   - Chat input is hidden
   - "Back to Home" button

Stream ends with `[DONE]`.

---

## Agent Architecture

The system uses a **single unified `LlmAgent`** (not a multi-agent hierarchy) with a dynamic instruction that adapts based on the conversation phase:

```
Intake Agent (LlmAgent)
  |
  ├── Dynamic Instruction (adapts to 3 phases)
  │   ├── Phase 1: Questioning — present questions, validate, assist
  │   ├── Phase 2: Review & Submit — summarize answers, submit on confirm
  │   └── Phase 3: Complete — intake already submitted
  |
  └── Tools
      ├── store_answer_tool      → state_tools.store_answer()
      ├── advance_question_tool  → state_tools.advance_question()
      ├── increment_attempts_tool → state_tools.increment_attempts()
      ├── set_guidance_tool      → state_tools.set_guidance()
      ├── skip_question_tool     → skip_tool.skip_question()
      ├── aggregate_fields_tool  → aggregation_tool.aggregate_fields()
      └── submit_intake_tool     → submit_tool.submit_intake()
```

### Why a Single Agent?

The original design had separate agents (Ask, Router, Validation, Assist, Submission) in a LoopAgent/SequentialAgent hierarchy. However, within a single `run_async()` call, the multi-agent system would loop without pausing for user input. The single-agent design naturally pauses after each response to wait for the next user message.

---

## Session State Schema

All agent decisions are driven by session state. Here is the full state structure:

```python
{
    "product": "Product Feature Intake",
    "description": "Submit a product feature request...",
    "config_id": "product_feature_intake",
    "config": { ... entire YAML config ... },

    # Question tracking
    "current_question_index": 3,        # 0-based, which question we're on
    "total_questions": 8,
    "current_question_validated": False, # has current question been validated?
    "current_question_attempts": 1,      # validation attempts for current question
    "current_guidance": "Try including...", # retry feedback (None if first attempt)

    # Answers (populated as user progresses)
    "answers": {
        "q1": { "response": "...", "validated": True, "skipped": False, "attempts": 1 },
        "q2": { "response": "...", "validated": True, "skipped": False, "attempts": 2 },
        "q7": { "response": "None specified", "validated": True, "skipped": True, "attempts": 0 },
    },

    # Submission
    "submission_payload": { ... },  # populated by aggregate_fields_tool
    "status": "in_progress",        # in_progress | completed | submitted
    "ticket_id": None,              # populated after submission
    "ticket_url": None,
}
```

---

## How Many Times is the Config Read?

| Action | Config Source | Frequency |
|--------|-------------|-----------|
| Catalog page loads | YAML files on disk (or MongoDB) | Once per page load |
| Session created | YAML file by ID (or MongoDB) | Once per session |
| Every chat message | `state["config"]` (in memory) | Every message, but from session state — **not** from disk/DB |
| Status check | `state["config"]` via session | Every status poll |

**The config is read from disk/MongoDB exactly twice:** once for the catalog listing, once for session creation. After that, it lives in session state and is never re-read from the source.

---

## SSE Event Types Emitted During a Conversation

| Event Type | When Emitted | Key Fields |
|------------|-------------|------------|
| `message` | Every agent text response | `content` |
| `tool_call` | Agent invokes a function tool | `name` |
| `progress` | After question is answered/skipped | `current_question_index`, `total_questions`, `questions_answered`, `questions_remaining` |
| `step_change` | When transitioning between named steps | `step_index`, `step_id`, `step_name`, `step_description` |
| `ui_control` | Next question is dropdown/multi-select, or review phase | `control`, `options`, `required` |
| `submission_result` | After platform submission | `status`, `ticket_id`, `ticket_url` |
| `error` | On processing failure | `message`, `retryable` |
| `[DONE]` | End of every SSE stream | — |

---

## Logging

Every step above is logged across four structured JSON log streams:

| Log File | What It Captures |
|----------|-----------------|
| `app.log` | Startup, config loading, HTTP requests/responses |
| `agent_audit.log` | Every LLM call (prompt, response, tokens, latency), tool calls, validation decisions |
| `conversation_audit.log` | Every user message and assistant response in presentation order |
| `platform_audit.log` | External API calls to Jira/ServiceNow (sanitized) |

All entries include `session_id` and `trace_id` for end-to-end correlation.
