#!/usr/bin/env python3
"""Convert markdown to Slack mrkdwn and post as a channel message."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SLACK_API_BASE = "https://slack.com/api"
CHANNEL_ID_RE = re.compile(r"^[CGD][A-Z0-9]{8,}$")


@dataclass
class SlackResult:
    channel: str
    ts: str


def convert_inline(text: str) -> str:
    """Convert a subset of markdown inline syntax to Slack mrkdwn."""
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"<\2|\1>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"*\1*", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"_\1_", text)
    text = re.sub(r"__([^_]+)__", r"*\1*", text)
    text = re.sub(r"~~([^~]+)~~", r"~\1~", text)
    return text


def markdown_to_slack(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False

    for line in lines:
        fence_match = re.match(r"^\s*```", line)
        if fence_match:
            in_code = not in_code
            out.append("```")
            continue

        if in_code:
            out.append(line.rstrip("\n"))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            text = convert_inline(heading.group(2).strip())
            out.append(f"*{text}*")
            continue

        task = re.match(r"^\s*[-*]\s+\[( |x|X)\]\s+(.+)$", line)
        if task:
            marker = "x" if task.group(1).lower() == "x" else " "
            item = convert_inline(task.group(2).strip())
            out.append(f"• [{marker}] {item}")
            continue

        bullet = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if bullet:
            item = convert_inline(bullet.group(1).strip())
            out.append(f"• {item}")
            continue

        ordered = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ordered:
            item = convert_inline(ordered.group(1).strip())
            out.append(f"• {item}")
            continue

        quote = re.match(r"^\s*>\s?(.+)$", line)
        if quote:
            out.append(f"> {convert_inline(quote.group(1).strip())}")
            continue

        out.append(convert_inline(line))

    rendered = "\n".join(out)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered).strip()
    return rendered


def _api_post(token: str, endpoint: str, payload: dict) -> dict:
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SLACK_API_BASE}/{endpoint}",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Slack HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Slack connection error: {exc.reason}") from exc
    parsed = json.loads(body)
    if not parsed.get("ok"):
        raise RuntimeError(f"Slack API error from {endpoint}: {parsed.get('error')}")
    return parsed


def _iter_channels(token: str) -> Iterable[dict]:
    cursor = ""
    while True:
        payload = {
            "exclude_archived": "true",
            "limit": "1000",
            "types": "public_channel,private_channel",
        }
        if cursor:
            payload["cursor"] = cursor
        data = _api_post(token, "conversations.list", payload)
        for channel in data.get("channels", []):
            yield channel
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break


def resolve_channel_id(token: str, channel: str) -> str:
    normalized = channel.strip()
    if normalized.startswith("#"):
        normalized = normalized[1:]
    if CHANNEL_ID_RE.match(normalized):
        return normalized

    for c in _iter_channels(token):
        if c.get("name") == normalized:
            return c["id"]
    raise RuntimeError(
        f"Could not resolve channel name '{channel}'. Use a channel ID or ensure "
        "the bot has channels:read/groups:read and channel access."
    )


def post_message(token: str, channel_id: str, text: str) -> SlackResult:
    data = _api_post(
        token,
        "chat.postMessage",
        {"channel": channel_id, "text": text, "mrkdwn": "true"},
    )
    return SlackResult(channel=data["channel"], ts=data["ts"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish markdown file contents to Slack as a formatted message."
    )
    parser.add_argument("markdown_file", help="Path to markdown file")
    parser.add_argument("channel", help="Slack channel name or channel ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print converted Slack text instead of posting",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.markdown_file)
    if not path.is_file():
        print(f"Markdown file not found: {path}", file=sys.stderr)
        return 1

    markdown = path.read_text(encoding="utf-8")
    rendered = markdown_to_slack(markdown)
    if not rendered:
        print("Rendered message is empty; nothing to post.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(rendered)
        return 0

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("Missing SLACK_BOT_TOKEN environment variable.", file=sys.stderr)
        return 1

    try:
        channel_id = resolve_channel_id(token, args.channel)
        result = post_message(token, channel_id, rendered)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Posted to channel {result.channel} at ts={result.ts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
