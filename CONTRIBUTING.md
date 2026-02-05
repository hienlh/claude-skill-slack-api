# Contributing to Claude Skill: Slack API

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Include steps to reproduce the problem
- Include error messages and logs
- Specify your Python version and OS

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where applicable
- Keep functions focused and documented
- No external dependencies (stdlib only)

### Testing

Test your changes manually:

```bash
# Test URL parsing
python3 scripts/slack.py --url "https://workspace.slack.com/archives/C123456/p1234567890123456"

# Test channel history
python3 scripts/slack.py --history -c YOUR_CHANNEL -l 5

# Test file listing
python3 scripts/slack.py --url "..." --list-files -v
```

## Development Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and add your tokens
3. Make changes to `scripts/slack.py`
4. Test thoroughly

## Questions?

Open an issue or reach out!
