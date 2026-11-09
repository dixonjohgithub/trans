# UAT Feedback Widget — Specification and Requirements

**Status:** Draft v1.1
**Owner:** JD (Principal AI Engineer)
**Target:** Agentic Intake Platform — React frontend + FastAPI backend
**Scope:** UAT environments only. Must be fully disabled (code-eliminated where possible) in production.

---

## 1. Purpose

Give UAT testers a way to submit feedback directly from inside the running web app — a comment, a category, and an automatic screenshot of what they were looking at — so the feedback arrives with enough context to be actionable without a separate write-up. Feedback is stored on our backend; nothing leaves the corporate network and no third-party SaaS is involved.

## 2. Goals and non-goals

### Goals
- One-click feedback from any screen in the app via a persistent floating button.
- Capture free-text comment, feedback type, and an automatic screenshot.
- Automatically attach context: page URL/route, browser/user-agent, viewport size, timestamp, app version/build, recent console errors, and the **currently selected intake card and its YAML definition**.
- Capture the tester's name explicitly, since the UAT-exposed app has no user authentication (platform auth exists, but the UAT app is not behind it).
- Persist feedback on the FastAPI backend in a queryable store.
- Provide a simple admin/export path so the engineering team can review submissions (JSON list endpoint + CSV export).
- Toggle the entire feature on/off per environment with a single flag on each tier.

### Non-goals
- Not a replacement for Jira. (Optional later: forward to Jira via existing Atlassian tooling.)
- No session replay, no screen recording, no analytics tracking.
- No element-level inspector/annotation tools in v1 (full-viewport screenshot only).
- No email notifications in v1.

## 3. User stories

| ID | As a… | I want… | So that… |
|---|---|---|---|
| US-1 | UAT tester | a visible "UAT feedback" button on every page | I can report something the moment I see it |
| US-2 | UAT tester | to pick a type (Bug / Suggestion / Question) and type a comment | the team can triage quickly |
| US-3 | UAT tester | the app to grab a screenshot automatically | I don't have to take and attach one myself |
| US-4 | UAT tester | confirmation that my feedback was sent | I know it was captured |
| US-5 | Engineer | all feedback stored with URL, tester name, time, browser, and the intake card YAML in use | I can reproduce the issue against the exact card configuration |
| US-5a | UAT tester | to enter my name once and have it remembered | I don't retype it on every submission |
| US-6 | Engineer | to list, filter, and export feedback | I can review it in a sheet or triage meeting |
| US-7 | Release manager | the feature to be absent in production builds | there is no UAT UI or endpoint exposed to real users |

## 4. Architecture overview

```
React app (UAT build)
  └─ <UatFeedbackProvider>            ← rendered only when VITE_UAT_FEEDBACK === "true"
       ├─ Floating trigger button
       ├─ Feedback modal (form + screenshot preview)
       └─ POST /api/uat/feedback  ──►  FastAPI
                                         └─ uat_feedback router   ← included only when UAT_FEEDBACK=true
                                              ├─ validates payload
                                              ├─ writes screenshot to disk/object store
                                              └─ inserts row into uat_feedback table
```

## 5. Frontend requirements (React)

### 5.1 Feature gating
- **FR-1** The widget renders only when `import.meta.env.VITE_UAT_FEEDBACK === "true"` (Vite) or `process.env.REACT_APP_UAT_FEEDBACK === "true"` (CRA). Use whichever the project uses.
- **FR-2** Import the widget via a dynamic import behind the flag so `html2canvas` and the widget code are tree-shaken / code-split out of production bundles.
  ```tsx
  // App.tsx
  const UatFeedback = import.meta.env.VITE_UAT_FEEDBACK === "true"
    ? lazy(() => import("./uat/UatFeedback"))
    : null;
  ...
  {UatFeedback && <Suspense fallback={null}><UatFeedback /></Suspense>}
  ```
- **FR-3** A production build with the flag unset must contain no "UAT feedback" strings and no `html2canvas` chunk. Verify with a bundle grep in CI.

### 5.2 Trigger button
- **FR-4** Fixed-position pill in the bottom-right corner, above the chat composer (`bottom: ~72px; right: 16px`), `z-index` above all app content.
- **FR-5** Label: `UAT feedback` with an icon. Accent color so it is clearly not part of the product UI.
- **FR-6** Keyboard accessible (`<button>`, focus ring, `aria-label="Send UAT feedback"`).
- **FR-7** Does not overlap the chat send button or any primary CTA.

### 5.3 Feedback modal
- **FR-8** Opens on trigger click. Closes on Cancel, the X button, `Esc`, or successful submit.
- **FR-9** Fields:
  - **Your name** — required text input, 2–80 chars. Pre-filled from `localStorage["uat_feedback_name"]` if present; saved back on successful submit. Validation error if empty: `Enter your name so we can follow up`.
  - **Type** — required, single-select chips: `Bug`, `Suggestion`, `Question`. Default: `Bug`.
  - **Comment** — required textarea, 10–2000 characters. Inline validation error if empty or too short: `Enter a few words describing what happened`.
  - **Severity** — optional select: `Blocker`, `High`, `Medium`, `Low`. Default `Medium`. Shown only when Type = Bug.
  - **Include screenshot** — checkbox, default checked.
- **FR-10** Screenshot is captured with `html2canvas` **at the moment the modal opens** (before the overlay is drawn), so the image shows the underlying page, not the modal.
  - Capture `document.body` at `scale: 1`, `useCORS: true`, `logging: false`.
  - Convert to PNG data URL; if the encoded size exceeds 2 MB, re-encode as JPEG at quality 0.7.
  - Show a thumbnail preview in the modal with a "Screenshot attached" label; if capture fails, show `Screenshot unavailable` and allow submit without it.
- **FR-11** The modal shows a small footer line stating what context is sent: `Also sends: page URL, current intake card, browser, timestamp`.
- **FR-11a** The modal displays the name of the currently selected intake card (read-only, e.g. `Intake card: Vendor Data Access v3`) so the tester can confirm the right one is attached. If no card is selected, display `Intake card: none selected`.
- **FR-12** Submit button: `Send feedback`. Disabled while a request is in flight; shows a spinner.
- **FR-13** On success: close modal and show a toast `Feedback sent — thanks` for 3 s.
- **FR-14** On failure: keep modal open, show inline error `Couldn't send feedback. Try again.` and keep the user's text.

### 5.4 Context captured automatically
- **FR-15** The widget assembles the following without user input:

| Field | Source |
|---|---|
| `page_url` | `window.location.href` |
| `route` | current router path (React Router `useLocation().pathname`), if available |
| `tester_name` | the **Your name** field (user-entered, remembered in `localStorage`) |
| `intake_card_id` | identifier of the currently selected intake card, from the app's intake-card state (store/context the card selector writes to) |
| `intake_card_name` | display name of the selected card |
| `intake_card_yaml` | the full YAML definition of the selected card **as currently loaded in the app** (the same text/object the app uses to drive the intake flow, serialized to YAML string). Max 256 KB; truncate with a `# [truncated]` marker if larger |
| `intake_card_version` | version/hash of the card if the app tracks one, optional |
| `user_agent` | `navigator.userAgent` |
| `viewport` | `{ width: window.innerWidth, height: window.innerHeight }` |
| `app_version` | build-time constant (`VITE_APP_VERSION` / git SHA) |
| `console_errors` | last 20 `console.error` / `window.onerror` / `unhandledrejection` messages, captured by a lightweight listener installed when the widget mounts |
| `session_id` | the app's existing chat/session identifier if one exists, optional |
| `client_timestamp` | `new Date().toISOString()` |

- **FR-16** No cookies, tokens, or request headers are captured. Console error capture stores message strings only, truncated to 500 chars each.
- **FR-16a** Intake YAML is read from the app's in-memory state at the moment the modal opens (not re-fetched), so it reflects exactly what the tester was running, including any unsaved/experimental card. If the card YAML is only available as a parsed object, serialize it with the project's existing YAML library (e.g. `js-yaml`) so the stored text is faithful to the structure.

### 5.5 Network
- **FR-17** `POST {API_BASE}/api/uat/feedback` with `Content-Type: application/json`, using the app's existing HTTP client. The UAT app is unauthenticated, so no auth header is expected; the backend protects the endpoint by network placement and rate limiting (see §7).
- **FR-18** Timeout 15 s. No automatic retry (user retries manually).

### 5.6 File layout (suggested)
```
src/uat/
  UatFeedback.tsx         # default export; mounts trigger + modal + error listener
  FeedbackModal.tsx
  useScreenshot.ts        # html2canvas wrapper, size fallback
  useConsoleErrorBuffer.ts
  uatApi.ts               # submitFeedback(payload)
  types.ts
```

## 6. Backend requirements (FastAPI)

### 6.1 Feature gating
- **BR-1** Settings value `UAT_FEEDBACK: bool = False` (pydantic-settings, env var `UAT_FEEDBACK`).
- **BR-2** The router is included only when the flag is true:
  ```python
  if settings.UAT_FEEDBACK:
      app.include_router(uat_feedback.router, prefix="/api/uat", tags=["uat"])
  ```
  With the flag false, `/api/uat/*` must return 404 and must not appear in OpenAPI docs.

### 6.2 Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/uat/feedback` | none (UAT network only) | Submit feedback |
| `GET` | `/api/uat/feedback` | admin token | List feedback (paginated, filterable) |
| `GET` | `/api/uat/feedback/{id}` | admin token | Single record incl. screenshot URL and intake YAML |
| `GET` | `/api/uat/feedback/{id}/screenshot` | admin token | Returns the image file |
| `GET` | `/api/uat/feedback/{id}/intake.yaml` | admin token | Returns the captured intake YAML as `text/yaml` |
| `GET` | `/api/uat/feedback/export.csv` | admin token | CSV of all records (no screenshots or YAML bodies) |
| `PATCH` | `/api/uat/feedback/{id}` | admin token | Update `status` / `triage_note` |

- **BR-3** The UAT-exposed app has no user authentication, so `POST` is open within the UAT network and relies on network placement, payload validation, and rate limiting. Read/export/patch endpoints require a shared secret: header `X-UAT-Admin-Token` compared (constant-time) against `settings.UAT_FEEDBACK_ADMIN_TOKEN`. If the platform's existing auth can be attached to the backend without exposing it to the UAT app, prefer that over the token.

### 6.3 Request schema — `POST /api/uat/feedback`
```json
{
  "type": "bug | suggestion | question",
  "severity": "blocker | high | medium | low | null",
  "comment": "string, 10–2000 chars",
  "tester_name": "string, 2–80 chars",
  "page_url": "string",
  "route": "string | null",
  "intake_card_id": "string | null",
  "intake_card_name": "string | null",
  "intake_card_version": "string | null",
  "intake_card_yaml": "string | null, max 256 KB",
  "user_agent": "string",
  "viewport": { "width": 1440, "height": 900 },
  "app_version": "string | null",
  "console_errors": ["string"],
  "session_id": "string | null",
  "client_timestamp": "ISO-8601 string",
  "screenshot_base64": "data:image/png;base64,... | null"
}
```
- **BR-4** Validate with Pydantic. Reject `screenshot_base64` larger than 5 MB decoded (413). Reject unknown `type`/`severity` values (422).
- **BR-5** Server sanitizes `tester_name` (trim, strip control chars) and rejects `intake_card_yaml` over 256 KB (413). The server does **not** parse or validate the YAML — it is stored verbatim for reproduction.

### 6.4 Response
- `201 Created` → `{ "id": "uuid", "received_at": "ISO-8601" }`

### 6.5 Storage
- **BR-6** Table `uat_feedback` (SQLAlchemy model; works on the project's existing DB, SQLite acceptable for UAT):

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `received_at` | timestamptz | server time |
| `client_timestamp` | timestamptz | |
| `type` | varchar(16) | |
| `severity` | varchar(16) nullable | |
| `comment` | text | |
| `page_url` | text | |
| `route` | text nullable | |
| `tester_name` | varchar(80) | |
| `intake_card_id` | varchar(128) nullable | indexed |
| `intake_card_name` | varchar(256) nullable | |
| `intake_card_version` | varchar(64) nullable | |
| `intake_card_yaml` | text nullable | stored verbatim |
| `user_agent` | text | |
| `viewport_w` / `viewport_h` | int | |
| `app_version` | varchar(64) nullable | |
| `console_errors` | JSON | |
| `session_id` | varchar(128) nullable | |
| `screenshot_path` | text nullable | relative path on disk / object key |
| `status` | varchar(16) | `new` (default), `triaged`, `fixed`, `wontfix` |
| `triage_note` | text nullable | |

- **BR-7** Screenshots are decoded and written to `settings.UAT_FEEDBACK_SCREENSHOT_DIR` (default `./data/uat_screenshots/`) as `{id}.png|jpg`. Never store base64 in the DB.
- **BR-8** Alembic migration included.

### 6.6 List endpoint behavior
- **BR-9** `GET /api/uat/feedback?type=bug&status=new&tester_name=...&intake_card_id=...&since=ISO&page=1&page_size=50`, newest first. Response includes `total`, `items[]` (without screenshot bytes or YAML body), plus `screenshot_url` and `intake_yaml_url` per item.
- **BR-10** CSV export columns: `id, received_at, tester_name, type, severity, status, intake_card_id, intake_card_name, intake_card_version, route, page_url, comment, app_version, screenshot_url, intake_yaml_url`.

### 6.7 File layout (suggested)
```
app/uat_feedback/
  __init__.py
  router.py
  schemas.py
  models.py
  service.py        # save screenshot, build CSV
alembic/versions/xxxx_add_uat_feedback.py
```

## 7. Security and compliance
- **SC-1** Feature is off by default on every tier; enabled only by explicit env var in UAT.
- **SC-2** The UAT app is unauthenticated, so `POST` is protected by UAT network placement plus validation and rate limiting; read/export/patch endpoints require the `X-UAT-Admin-Token` shared secret (stored in the environment, never in code or the frontend bundle).
- **SC-2a** `tester_name` is self-reported and should be treated as informational, not as an identity assertion.
- **SC-2b** Intake YAML may contain prompt text, routing rules, or field definitions considered internal. Store it with the same classification as the intake cards themselves; it is never returned by the list/export endpoints, only by the per-record YAML endpoint behind the admin token.
- **SC-3** Screenshots may contain sensitive data visible on screen. Store in the same protected location/classification as other app data; do not log screenshot contents; exclude the screenshot dir from backups to shared locations unless approved.
- **SC-4** No external network calls from the widget or backend. `html2canvas` is bundled from the internal Artifactory npm proxy.
- **SC-5** Comments and console errors are stored as plain text; strip control characters; enforce max lengths.
- **SC-6** Rate limit `POST /api/uat/feedback` to 10 requests/minute per client IP (no user identity available) to prevent accidental floods.
- **SC-7** Retention: delete `uat_feedback` rows and screenshots older than 90 days (scheduled job or manual script) unless exported.

## 8. Configuration summary

| Tier | Variable | Value |
|---|---|---|
| Frontend | `VITE_UAT_FEEDBACK` | `"true"` in UAT, unset elsewhere |
| Frontend | `VITE_APP_VERSION` | git SHA or semver injected at build |
| Backend | `UAT_FEEDBACK` | `true` in UAT, `false`/unset elsewhere |
| Backend | `UAT_FEEDBACK_SCREENSHOT_DIR` | path, default `./data/uat_screenshots` |
| Backend | `UAT_FEEDBACK_ADMIN_TOKEN` | random secret for read/export/patch endpoints |

## 9. Acceptance criteria

- [ ] AC-1 With both flags on, the trigger button appears on every route and opens the modal.
- [ ] AC-2 Submitting with an empty comment or empty name shows the inline validation error and does not call the API.
- [ ] AC-2a After one successful submit, reopening the modal pre-fills the name field; the value survives a page reload.
- [ ] AC-3 Submitting a valid bug with screenshot creates a DB row and a screenshot file; `GET /api/uat/feedback/{id}/screenshot` returns the image and it shows the page, not the modal.
- [ ] AC-3a With an intake card selected, the stored record's `intake_card_id` / `intake_card_name` match the selected card, and `GET /api/uat/feedback/{id}/intake.yaml` returns YAML that parses and is equivalent to the card definition loaded in the app at submit time.
- [ ] AC-3b With no intake card selected, submission succeeds and the intake fields are null; the modal shows `Intake card: none selected`.
- [ ] AC-3c An intake YAML over 256 KB is truncated client-side with a `# [truncated]` marker and accepted; a payload exceeding the server limit returns 413.
- [ ] AC-4 Screenshot capture failure still allows submission; `screenshot_path` is null.
- [ ] AC-5 `GET /api/uat/feedback` returns the record with all context fields; filters by `type`, `status`, `tester_name`, and `intake_card_id` work.
- [ ] AC-6 CSV export opens in Excel with one row per record, including intake card columns.
- [ ] AC-7 A request without a valid `X-UAT-Admin-Token` receives 401 on list/export/patch/screenshot/yaml endpoints; `POST` works without it.
- [ ] AC-8 With `VITE_UAT_FEEDBACK` unset, a production build contains no UAT feedback UI and no `html2canvas` chunk (verified by grep on `dist/`).
- [ ] AC-9 With `UAT_FEEDBACK=false`, `/api/uat/feedback` returns 404 and is absent from `/docs`.
- [ ] AC-10 11th submission within one minute from the same client IP returns 429.
- [ ] AC-11 Unit tests cover schema validation, size limits, role gating, and feature flag gating. Frontend tests cover modal validation and the success/failure flows (mocked API).

## 10. Deliverables
1. Frontend widget code under `src/uat/` with the gated lazy import in `App.tsx`.
2. Backend package `app/uat_feedback/` with router, schemas, models, service, and Alembic migration.
3. Tests (pytest + the project's frontend test runner).
4. `README-uat-feedback.md` covering: enabling the feature, where data lands, how to export, and how to confirm it is off in production.
5. CI check that fails a production build if `html2canvas` or `UatFeedback` appears in the output bundle.

## 11. Open questions for the implementer
1. Which store/context holds the currently selected intake card and its YAML (or parsed object) in the frontend? Confirm whether it is available as a YAML string or needs serializing.
2. Is the backend DB Postgres or SQLite in UAT? (Affects JSON column type in the migration.)
3. Can the platform's existing auth be attached to the backend admin endpoints without exposing it to the UAT app, or should the shared admin token be used as specified?
4. Should feedback optionally be forwarded to Jira in a later phase? If yes, which project key?
