#!/usr/bin/env python
"""
graph_fetch_emails.py

Description:
    Fetches Microsoft Graph email messages from the user's inbox for a given day,
    filters for messages sent directly to the user (not group or CC'd messages),
    extracts message content, and saves normalized results as JSON and TXT files
    for summarization and analysis.

Usage:
    python scripts/graph_fetch_emails.py [YYYYMMDD]

    - If no date argument is provided, the current UTC day is used.
    - Requires a valid Microsoft Graph access token and user email in .env:
        GRAPH_ACCESS_TOKEN=<your_token>
        USER_EMAIL=<your_email>

Dependencies:
    - requests: for HTTP requests to the Microsoft Graph API
    - python-dotenv: for reading environment variables from .env
    - beautifulsoup4: for converting HTML email bodies to text
    - pathlib: for filesystem operations
    - re, datetime, json: built-in libraries used for parsing and formatting

Output:
    Writes results to:
        goals/inbox/raw-YYYYMMDD.json   # structured message data
        goals/inbox/raw-YYYYMMDD.txt    # plaintext bodies for summarization

Author:
    JD (AI Engineer)
"""

import os
import sys
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pathlib import Path

GRAPH = "https://graph.microsoft.com/v1.0"


def yyyymmdd(dt: datetime) -> str:
    """Return a date formatted as YYYYMMDD."""
    return dt.strftime("%Y%m%d")


def parse_day_arg(arg: str | None) -> str:
    """Parse the day argument (YYYYMMDD). If not provided, return today's UTC date."""
    if arg:
        if not re.fullmatch(r"\d{8}", arg):
            raise ValueError("entry day must be YYYYMMDD")
        return arg
    return yyyymmdd(datetime.now(timezone.utc))


def iso_range_for_day(day: str) -> tuple[str, str]:
    """Given a YYYYMMDD string, return ISO 8601 start and end timestamps for that day (UTC)."""
    y, m, d = int(day[:4]), int(day[4:6]), int(day[6:8])
    start = datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def html_to_text(html: str) -> str:
    """Convert HTML email body to plaintext, removing scripts, styles, and extra whitespace."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join([ln for ln in lines if ln])


def eq(a: str | None, b: str | None) -> bool:
    """Case-insensitive string comparison that tolerates None."""
    return (a or "").lower() == (b or "").lower()


def is_direct_to_user(msg: dict, user_email: str) -> bool:
    """
    Determine if a message was sent directly to the user.
    Criteria:
        - User's email is the only address in 'toRecipients'
        - No addresses in 'ccRecipients'
    """
    to = msg.get("toRecipients") or []
    cc = msg.get("ccRecipients") or []
    addressed_to_user = any(eq(r.get("emailAddress", {}).get("address"), user_email) for r in to)
    single_to = len(to) == 1
    no_cc = len(cc) == 0
    return addressed_to_user and single_to and no_cc


def fetch_page(url: str, token: str) -> dict:
    """Perform a GET request to a Microsoft Graph API URL with the given bearer token."""
    res = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if not res.ok:
        raise RuntimeError(f"Graph error {res.status_code}: {res.text[:500]}")
    return res.json()


def fetch_messages_for_day(day: str, token: str) -> list[dict]:
    """
    Retrieve all messages for a specific UTC day using the Microsoft Graph API.

    Filters by:
        - receivedDateTime within the day range
        - isDraft = false
    Returns a list of message dictionaries.
    """
    start_iso, end_iso = iso_range_for_day(day)
    select = ",".join([
        "id","subject","from","sender","toRecipients","ccRecipients",
        "receivedDateTime","body","bodyPreview","webLink","isDraft"
    ])
    flt = quote(f"receivedDateTime ge {start_iso} and receivedDateTime lt {end_iso} and isDraft eq false")
    url = f"{GRAPH}/me/messages?$top=50&$select={select}&$filter={flt}&$orderby=receivedDateTime desc"
    all_msgs: list[dict] = []
    while url:
        page = fetch_page(url, token)
        all_msgs.extend(page.get("value") or [])
        url = page.get("@odata.nextLink") or ""
    return all_msgs


def normalize_message(m: dict) -> dict:
    """Extract relevant fields from a raw message and normalize the body to plaintext."""
    body_ct = (m.get("body") or {}).get("contentType", "text")
    body_raw = (m.get("body") or {}).get("content") or ""
    body_txt = html_to_text(body_raw) if body_ct.lower() == "html" else body_raw

    from_addr = (
        (m.get("from") or {}).get("emailAddress", {}).get("address")
        or (m.get("sender") or {}).get("emailAddress", {}).get("address")
        or ""
    )
    to_addrs = [
        r.get("emailAddress", {}).get("address")
        for r in (m.get("toRecipients") or [])
        if r.get("emailAddress")
    ]

    return {
        "id": m.get("id"),
        "subject": m.get("subject") or "(no subject)",
        "from": from_addr,
        "to": [a for a in to_addrs if a],
        "receivedDateTime": m.get("receivedDateTime"),
        "webLink": m.get("webLink") or "",
        "body": body_txt.strip(),
    }


def main():
    """
    Main execution flow:
        1. Load environment variables for Graph token and user email.
        2. Determine target date (today or passed via CLI).
        3. Fetch all messages for that day.
        4. Filter to direct-to-user messages only.
        5. Normalize and save results as JSON and TXT files.
    """
    load_dotenv()
    token = os.getenv("GRAPH_ACCESS_TOKEN")
    user_email = os.getenv("USER_EMAIL")
    if not token:
        raise RuntimeError("GRAPH_ACCESS_TOKEN missing in .env")
    if not user_email:
        raise RuntimeError("USER_EMAIL missing in .env")

    day = parse_day_arg(sys.argv[1] if len(sys.argv) > 1 else None)
    msgs = fetch_messages_for_day(day, token)
    direct = [m for m in msgs if is_direct_to_user(m, user_email)]
    normalized = [normalize_message(m) for m in direct]

    out_dir = Path("goals") / "inbox"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"raw-{day}.json"
    txt_path = out_dir / f"raw-{day}.txt"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"day": day, "count": len(normalized), "messages": normalized},
                  f, indent=2, ensure_ascii=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        for m in normalized:
            f.write(f"Subject: {m['subject']}\n")
            f.write(f"From: {m['from']}\n")
            f.write(f"Received: {m['receivedDateTime']}\n")
            f.write(f"Link: {m['webLink']}\n")
            f.write("Body:\n")
            f.write(m["body"])
            f.write("\n\n---\n\n")

    print(f"Wrote {len(normalized)} direct messages")
    print(f"  {json_path}")
    print(f"  {txt_path}")


if __name__ == "__main__":
    main()