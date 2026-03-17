# Slack Publish Agent Routing

When the user runs command-style prompts like:

- `codex publish <markdown-file> <channel>`
- `publish <markdown-file> <channel>`

use the `slack-markdown-publish` skill and execute:

`python3 slack-markdown-publish/scripts/publish_markdown_to_slack.py <markdown-file> <channel>`

Execution requirements:

- Prefer `SLACK_BOT_TOKEN` from environment.
- If environment inheritance is restricted, allow token fallback from `.env` or `.env.local` in the current working directory.
- Support explicit token file with:
  `python3 slack-markdown-publish/scripts/publish_markdown_to_slack.py <markdown-file> <channel> --env-file <path>`
