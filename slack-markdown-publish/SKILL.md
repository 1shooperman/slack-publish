---
name: slack-markdown-publish
description: Publish local Markdown files to Slack as formatted messages (not file uploads) by converting Markdown to Slack mrkdwn and posting with chat.postMessage. Use when the user asks to send a .md file to a Slack channel, especially command-style requests like "codex publish foo.md my-slack-channel-foo" or "publish this markdown to Slack".
---

# Slack Markdown Publish

Use this skill to convert Markdown into Slack-compatible message text and publish it directly to a channel.

## Workflow

1. Parse the user request and extract `<markdown-file>` and `<channel>` from command-style text like `codex publish foo.md my-slack-channel-foo`.
2. Ensure `SLACK_BOT_TOKEN` is available from environment, or from `.env`/`.env.local` fallback.
3. Run:
   `python3 scripts/publish_markdown_to_slack.py <markdown-file> <channel>`
4. Report posting success including the resolved channel ID and message timestamp.
5. If posting fails, report the exact Slack API error and suggest missing scopes or channel membership as the likely fix.

## Expected command behavior

- Treat `#channel-name` and `channel-name` as channel names.
- Accept direct channel IDs like `C123...` and `G123...`.
- Post as a Slack message via `chat.postMessage`.
- Never upload the markdown file itself.

## Environment requirements

- `SLACK_BOT_TOKEN` must be set, or present in `.env` / `.env.local`.
- Bot token scopes should include:
  - `chat:write`
  - `channels:read` for public channel lookup by name
  - `groups:read` for private channel lookup by name
- The bot must be in the destination channel.

## Script

- `scripts/publish_markdown_to_slack.py`
  - Converts common markdown constructs to Slack mrkdwn:
    - headings to bold lines
    - bullet/numbered/task lists to bullet text
    - fenced code blocks to triple-backtick blocks
    - links to `<url|label>`
    - inline `**bold**`, `*italic*`, `` `code` ``, and `~~strike~~`
  - Resolves channel name to ID when needed.
  - Falls back to `.env` and `.env.local` when environment variables are not inherited.
  - Supports `--env-file <path>` for an explicit token file.
  - Supports `--dry-run` to print rendered Slack text without posting.
