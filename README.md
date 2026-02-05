# Claude Skill: Slack API

> Read Slack messages, threads, channels, and download attachments without MCP dependencies.

A Python-based Claude Code skill for interacting with Slack workspaces using browser session tokens. No MCP server required - uses pure Python with urllib.

## Quick Install

```bash
npx skills add hienlh/claude-skill-slack-api
```

Or install globally without prompts:

```bash
npx skills add hienlh/claude-skill-slack-api -y -g
```

After install, configure your tokens (see [Authentication](#2-configure-authentication-tokens)).

## Features

- **Read Messages** - Fetch channel history, thread replies, or specific messages from URLs
- **Search** - Search messages across your workspace
- **List Channels** - Browse public and private channels
- **Download Files** - Download attachments from messages/threads
- **Post Messages** - Send messages to channels or threads
- **User/Channel Info** - Get detailed user and channel information

## Installation

### 1. Clone to your Claude skills directory

```bash
git clone https://github.com/hienlh/claude-skill-slack-api.git ~/.claude/skills/slack-api
```

### 2. Configure authentication tokens

Get your Slack browser session tokens:

1. Open Slack in your browser (not the desktop app)
2. Open DevTools → Application → Cookies
3. Find and copy:
   - `xoxc-*` token → `SLACK_XOXC_TOKEN`
   - `d` cookie (starts with `xoxd-*`) → `SLACK_XOXD_TOKEN`

Create `.env` file:

```bash
cp ~/.claude/skills/slack-api/.env.example ~/.claude/skills/slack-api/.env
# Edit .env with your tokens
```

### 3. (Optional) Install URL detection hook

Copy the hook to automatically detect Slack URLs in your prompts:

```bash
cp ~/.claude/skills/slack-api/hooks/slack-url-detector.cjs ~/.claude/hooks/
```

Add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node $HOME/.claude/hooks/slack-url-detector.cjs"
          }
        ]
      }
    ]
  }
}
```

## Quick Start

```bash
# Read a message from URL
python3 ~/.claude/skills/slack-api/scripts/slack.py --url "https://workspace.slack.com/archives/C05AZF69J9Z/p1769774454630549"

# Read a thread
python3 ~/.claude/skills/slack-api/scripts/slack.py --url "https://workspace.slack.com/archives/C05AZF69J9Z/p1769774454630549?thread_ts=1769174779.798959"

# Get channel history
python3 ~/.claude/skills/slack-api/scripts/slack.py --history -c C05AZF69J9Z -l 10

# Search messages
python3 ~/.claude/skills/slack-api/scripts/slack.py --search "keyword in:channel-name"

# List files in a thread
python3 ~/.claude/skills/slack-api/scripts/slack.py --url "..." --list-files -v

# Download all files
python3 ~/.claude/skills/slack-api/scripts/slack.py --url "..." --download-files -o ./downloads
```

## Commands Reference

| Command | Description | Required |
|---------|-------------|----------|
| `--url URL` | Read from Slack message URL | URL |
| `--history` | Get channel message history | `-c CHANNEL` |
| `--replies` | Get thread replies | `-c`, `--thread-ts` |
| `--search QUERY` | Search messages | query |
| `--list-channels` | List workspace channels | - |
| `--post` | Post message | `-c`, `-t TEXT` |
| `--user-info ID` | Get user details | user_id |
| `--channel-info ID` | Get channel details | channel_id |
| `--list-files` | List files with details | `--url` or messages |
| `--download-files` | Download all files | `--url` or messages |

## Options

| Option | Description |
|--------|-------------|
| `-c`, `--channel` | Channel ID |
| `--thread-ts` | Thread timestamp |
| `-t`, `--text` | Message text (for posting) |
| `-l`, `--limit` | Number of results (default: 20) |
| `-o`, `--output-dir` | Download directory (default: ./slack-downloads) |
| `-v`, `--verbose` | Verbose file info |
| `--json` | Output raw JSON |

## URL Timestamp Conversion

Slack URLs use a special timestamp format:
- URL: `p1767879572095059`
- API: `1767879572.095059` (insert dot 6 chars from end)

The script handles this conversion automatically.

## Requirements

- Python 3.6+
- No external dependencies (uses stdlib only)

## License

MIT License - See [LICENSE](LICENSE)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)
