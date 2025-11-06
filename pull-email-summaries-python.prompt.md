---
mode: agent
tools: ['search/codebase']
description: 'Fetch and summarize direct emails via Python for a given day, then write goals/inbox/YYYYMMDD-emails.md'
---

# Pull Email Summaries (Python)

Your purpose: run the Python script that fetches direct-to-user emails for a day, read the raw TXT, summarize full content into clear bullets grouped by topic, and write a Markdown file in `goals/inbox/` for later inclusion in the daily goals check-in.

## Inputs

- **Day**: `${input:day}` in `YYYYMMDD`. If omitted, infer today.

## Steps

1. If Day is missing, infer today in `YYYYMMDD`.
2. In the repo terminal, run:
   - `npm run emails:day -- ${input:day}`
3. Read `goals/inbox/raw-${input:day}.txt`.
4. Produce `goals/inbox/${input:day}-emails.md` with:

   ```md
   # Email Summary for ${input:day}

   ## Highlights
   - <3 to 7 bullets with concrete asks or decisions. include sender and link when relevant>

   ## By Message
   ${for each message}
   ### ${Subject}
   - From: <sender> at <time>
   - Summary: <3 to 5 bullets with asks, deadlines, owners>
   - Link: <webLink if present>
   ```

5. Show a preview and ask for approval to save. On approval, write or update the file and report the path.

## Guidelines

- Summarize the full body. Avoid paraphrasing the preview only.
- Capture requests, deadlines, deliverables, links, and owners.
- No invented content. If a message is ambiguous, note the uncertainty.