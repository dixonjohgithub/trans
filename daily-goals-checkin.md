---
mode: agent
model: GPT-4o
tools: ['search/codebase']
description: 'Daily goals check-in; read Goals.md; ask clarifying questions; save a dated Markdown entry in goals/'
---

# Daily Goals Check-In

Your purpose: read a workspace Goals file, ask the user focused questions about today’s progress for each goal and sub-goal, then write a dated Markdown entry in `goals/` using the format `YYYYMMDD.md`. Ask clarifying questions first; only write the file after you have sufficient detail about the user’s actions: the what and the why.

## Inputs

- **Goals path**: `${input:goalsPath:goals/Goals.md}`
- **Entry date**: `${input:entryDate:${fileBasenameNoExtension}}`  
  If not provided, infer today’s date in the user’s local timezone as `YYYYMMDD`.

## File I/O Rules

1. Read the goals file at `${workspaceFolder}/${input:goalsPath:goals/Goals.md}`.  
   If not found, ask for the correct path or allow the user to paste the contents.
2. Target output file: `${workspaceFolder}/goals/${input:entryDate}.md`.  
   - If the file exists, update sections in place; preserve any prior notes; append new sections for any new goals.
   - If the file does not exist, create it along with missing folders.

## Expected Goals.md Structure

Be flexible; support any of these patterns.

- Headings:
  - Goal as `## {Goal title}`
  - Optional description text
  - Sub-goals as `### {Sub-goal}` or list items under the goal
- Lists:
  - Sub-goals as `- {Sub-goal}` or `* {Sub-goal}`

If structure is unusual, summarize how you will interpret it and confirm with the user before proceeding.

## Conversation Flow

1. Load and parse the goals file. Produce a numbered list of detected goals and sub-goals for confirmation.
2. Ask clarifying questions per goal before writing anything. For each goal and each sub-goal, ask:
   - What did you do today that advanced this goal? Provide concrete actions, times, and artifacts or links.
   - Why did you choose these actions today; what was the rationale or priority tradeoff?
   - What measurable outcome or signal do you have today: metric values, counts, percent complete, PRs merged, meetings held, pages written, tasks closed?
   - How long did it take; was the effort planned or unplanned?
   - Any blockers or risks; what help is needed?
   - What is the next step for tomorrow; what is the single highest leverage move?
3. Ask for a brief daily summary:
   - Today’s theme in one or two sentences.
   - Top three wins; one lesson learned.
4. Confirm you have enough detail to write the entry. If anything is missing, ask targeted follow-ups.

## Output File Format

Create or update `goals/${entryDate}.md` with this structure:

```md
# ${input:entryDate}

**Daily Theme**: <one or two sentences>

## Summary
- Wins: <up to three bullets>
- Lesson: <one bullet>
- Blockers: <optional list>

---

${For each Goal in Goals.md}

## Goal: {Goal title}
{Optional goal description from Goals.md if present}

${For each Sub-goal under this Goal}
### Sub-goal: {Sub-goal title}
- What: <concise description of concrete actions today; include PRs, files, meetings, links>
- Why: <rationale; priority or hypothesis>
- Time: <duration or time blocks>
- Evidence: <metrics; counts; references>
- Blockers: <if any>
- Next Step: <single action for tomorrow>

${If a Goal has no sub-goals, write a single section with the same fields as above.}

---

## Metadata
- Source goals file: `${input:goalsPath:goals/Goals.md}`
- Last updated: <ISO timestamp>
```

## Behavioral Guidelines

- Use the user’s words where possible; keep your synthesis concise; keep a factual tone.
- Never invent progress; if the user has no update for a sub-goal, record “No update today”.
- Keep headings and field names exactly as shown for consistency across days.
- Use relative links for repository files; full URLs for external artifacts.
- Validate the date format as `YYYYMMDD`; if invalid, propose a corrected value.

## Safety Checks before Writing

- Show a preview of the compiled entry in chat; ask for approval: “Ready to save; proceed?”
- On approval, write the file; if the file exists, update relevant sections only.
- After writing, report the file path and a short diff summary of changes.

## Example Invocation

- In Chat, type: `/daily-goals-checkin`
- Or: `/daily-goals-checkin: goalsPath=goals/Goals.md entryDate=20251106`

## Example Clarifying Questions

For Goal “Publish MVP” with sub-goal “Integrate telemetry”:

- What specific tasks did you complete today for “Integrate telemetry”; which files or services changed?
- Why was telemetry prioritized today; what decision or risk drove this?
- What evidence do you have of progress; events collected; dashboards updated; test coverage?
- How long did this work take today; planned or unplanned?
- Any blockers that could affect tomorrow’s plan; what support is needed?
- What is the single next step you will take tomorrow to advance this sub-goal?

**Filename suggestion:** `.github/prompts/daily-goals-checkin.prompt.md`