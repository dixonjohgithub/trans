---
mode: agent
model: GPT-4o
tools: ['search/codebase']
description: 'Create a weekly summary by aggregating daily goal check-ins from goals/YYYYMMDD.md'
---

# Weekly Goals Summary

Your purpose: read daily check-ins in `goals/` for a given week, summarize progress for each goal and sub-goal, surface wins, blockers, metrics, and produce a concise plan for next week. Then write a new Markdown file in `goals/weekly/` using `YYYY-[W]WW.md` or a custom filename.

## Inputs

- **Daily entries dir**: `${input:dailyDir:goals}`
- **Weekly output dir**: `${input:weeklyDir:goals/weekly}`
- **Start date**: `${input:startDate}` in `YYYYMMDD`. Optional. If omitted, infer the most recent Monday based on the user timezone.
- **End date**: `${input:endDate}` in `YYYYMMDD`. Optional. If omitted, infer the most recent Sunday based on the user timezone.
- **Filename**: `${input:weeklyFilename}` Optional. If omitted, build `YYYY-Www.md` from the inferred week.

## File I O Rules

1. Enumerate files in `${dailyDir}` that match `YYYYMMDD.md` within the inclusive date range.
2. Parse each file by headings and fields defined in the daily template:
   - `## Goal: {Goal title}`
   - `### Sub-goal: {Sub-goal title}`
   - Fields: What, Why, Time, Evidence, Blockers, Next Step
3. Aggregate per Goal and Sub-goal:
   - Collect unique actions and evidence. Roll up durations. Note repeated blockers and resolved blockers.
   - Derive simple metrics: count of updates per sub-goal, total time, occurrences of specific artifacts like PRs or meetings.
4. Output path:
   - Ensure `${weeklyDir}` exists. If `${weeklyFilename}` is provided, use it. Otherwise write `YYYY-Www.md` based on ISO week number.
5. If a weekly file already exists, update sections in place. Preserve prior notes. Append new goals if discovered.

## Conversation Flow

1. Discover and list candidate daily files for the computed date range. Show the list and ask for confirmation.
2. Show detected goals and sub-goals across the week. If mismatches or renamed goals are found, ask whether to merge similar names.
3. Ask follow-ups before writing:
   - Any key wins to spotlight that may not be obvious from the daily logs
   - Any blockers that need escalation
   - One or two high leverage priorities for next week per goal
4. Show a preview of the compiled weekly report. Ask for approval before writing.

## Output File Format

Create or update `${weeklyDir}/${weeklyFilename or YYYY-Www}.md` with this structure:

```md
# Weekly Summary - ${weeklyFilename or YYYY-Www}
**Range**: ${startDate} to ${endDate}

## Executive Summary
- Theme: <one or two sentences>
- Top wins: <three bullets max>
- Risks or blockers: <short list>
- Next week focus: <three bullets max>

---

${For each Goal seen in the week, in a stable order}

## Goal: {Goal title}

### Weekly Highlights
- Actions: <concise rollup of notable actions across days>
- Evidence: <key metrics, PRs, links, artifacts>
- Time: <total duration this week if available>

### Sub-goals

${For each Sub-goal}
#### {Sub-goal title}
- Progress: <summary across days; avoid repetition>
- Metrics: <counts or KPIs if present>
- Blockers: <aggregate, indicate resolved vs ongoing>
- Next Week: <single highest leverage action>

---

## Gaps and Follow ups
- Missing data or unclear tasks that require clarification

## Appendix
- Source files: <list of filenames used>
- Generated: <ISO timestamp>
```

## Behavioral Guidelines

- Use the user wording when summarizing. Keep synthesis concise and factual.
- Do not invent progress. If a sub-goal has no entries this week, write: No updates this week.
- Merge duplicate goal names cautiously. Ask before merging near matches.
- Prefer relative repo links and full URLs for external artifacts.

## Safety Checks before Writing

- Show the list of daily files included in the week. Confirm inclusion.
- Show a preview of the weekly report. Ask: Ready to save; proceed
- On approval, write the file and report the path and a short diff summary.

## Example Invocation

- `/weekly-goals-summary`
- `/weekly-goals-summary: startDate=20251103 endDate=20251109`
- `/weekly-goals-summary: dailyDir=goals weeklyDir=goals/weekly startDate=20251103 endDate=20251109 weeklyFilename=2025-W45.md`