# Slack Markdown Publish Skill

This project defines a Codex skill that publishes a local Markdown file to Slack as a **formatted message** (using Slack `mrkdwn`), not as a file upload and not as raw Markdown text.

Primary command style:

```bash
codex publish foo.md my-slack-channel-foo
```

## Create Slack App From Manifest

Use this file:

- `slack-app-manifest.yaml`

Slack UI steps:

1. Open `https://api.slack.com/apps`
2. Click **Create New App**
3. Select **From a manifest**
4. Pick your workspace
5. Paste the contents of `slack-app-manifest.yaml`
6. Create app, then click **Install to Workspace**
7. Copy the Bot User OAuth Token (`xoxb-...`)

The manifest already includes the required bot scopes:

- `chat:write`
- `channels:read`
- `groups:read`

## What Was Built

- Skill definition and workflow:
  - `slack-markdown-publish/SKILL.md`
- Skill UI metadata:
  - `slack-markdown-publish/agents/openai.yaml`
- Publisher script:
  - `slack-markdown-publish/scripts/publish_markdown_to_slack.py`

The skill is also installed to:

- `~/.codex/skills/slack-markdown-publish`

## Simple Configuration (No Additional Coding)

Set these up once:

1. `SLACK_BOT_TOKEN` environment variable must be present.
2. Slack app token scopes should include:
   - `chat:write`
   - `channels:read` (public channel lookup by name)
   - `groups:read` (private channel lookup by name)
3. Invite the bot to the destination channel.

Example:

```bash
export SLACK_BOT_TOKEN='xoxb-...'
```

## Custom Build (Implemented Here)

The script includes logic that simple configuration cannot provide on its own:

1. Convert Markdown to Slack `mrkdwn`:
   - `# Heading` / `## Heading` -> bold header line
   - bullet, numbered, and task lists -> Slack-friendly bullet lines
   - fenced code blocks -> triple-backtick blocks
   - links -> `<url|label>`
   - inline formatting conversions for bold/italic/strike
2. Resolve channel names (for example `my-slack-channel-foo` or `#my-slack-channel-foo`) to channel IDs.
3. Post via Slack `chat.postMessage` with clear error handling.
4. Support `--dry-run` to preview rendered Slack text before posting.

## Usage

### Through Codex (target behavior)

```bash
codex publish foo.md my-slack-channel-foo
```

### Direct script usage

From this repo:

```bash
python3 slack-markdown-publish/scripts/publish_markdown_to_slack.py foo.md my-slack-channel-foo
```

From installed skill:

```bash
python3 ~/.codex/skills/slack-markdown-publish/scripts/publish_markdown_to_slack.py foo.md my-slack-channel-foo
```

Dry run (preview converted text only):

```bash
python3 ~/.codex/skills/slack-markdown-publish/scripts/publish_markdown_to_slack.py foo.md my-slack-channel-foo --dry-run
```

## Example Conversion

Input Markdown:

```md
# MY HEADER
## My Topic
lorem ipsum dolor
```

Rendered for Slack:

```text
*MY HEADER*
*My Topic*
lorem ipsum dolor
```

## Notes

- This posts a normal Slack message, not a file attachment.
- Channel may be provided by name or by ID (`C...` / `G...`).
- If posting fails, check token scopes and bot channel membership first.

## Validation Status

- Script compiles successfully.
- Markdown conversion dry-run was verified locally.
- Full live post was not executed in this run (depends on your Slack token/workspace access).
