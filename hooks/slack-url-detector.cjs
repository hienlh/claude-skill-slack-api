#!/usr/bin/env node
/**
 * Slack URL Detector - UserPromptSubmit Hook
 *
 * Detects Slack message URLs in user prompts and injects instructions
 * to fetch the message content using Python slack-api skill.
 *
 * URL Format: https://{workspace}.slack.com/archives/{channel_id}/p{timestamp}
 *
 * Exit Codes:
 *   0 - Success (non-blocking)
 */

const fs = require('fs');

// Slack URL regex pattern
const SLACK_URL_PATTERN = /https:\/\/([a-zA-Z0-9-]+)\.slack\.com\/archives\/([A-Z0-9]+)\/p(\d+)/g;

/**
 * Parse Slack URL into components
 * @param {string} url - Full Slack URL
 * @returns {Object} - Parsed components
 */
function parseSlackUrl(url) {
  const match = url.match(/https:\/\/([a-zA-Z0-9-]+)\.slack\.com\/archives\/([A-Z0-9]+)\/p(\d+)/);
  if (!match) return null;

  const [fullUrl, workspace, channelId, rawTimestamp] = match;

  // Convert p1767879572095059 format to 1767879572.095059 API format
  const apiTimestamp = rawTimestamp.slice(0, -6) + '.' + rawTimestamp.slice(-6);

  return {
    url: fullUrl,
    workspace,
    channelId,
    rawTimestamp,
    apiTimestamp,
  };
}

/**
 * Build instruction output for detected Slack URLs
 */
function buildSlackInstructions(parsedUrls, fullUrls) {
  const lines = [
    '## Slack Message Detected',
    '',
    'Use Python slack-api skill to read message:',
    '',
    '```bash',
    `python3 ~/.claude/skills/slack-api/scripts/slack.py --url "${fullUrls[0]}"`,
    '```',
    '',
  ];

  if (parsedUrls.length > 1) {
    lines.push('**Additional URLs detected:**');
    fullUrls.slice(1).forEach((url, index) => {
      lines.push(`${index + 2}. \`${url}\``);
    });
    lines.push('');
  }

  lines.push('**Available options:** `--list-files`, `--download-files -o DIR`, `--json`, `-v`');

  return lines;
}

async function main() {
  try {
    const stdin = fs.readFileSync(0, 'utf-8').trim();
    if (!stdin) process.exit(0);

    const payload = JSON.parse(stdin);
    const userPrompt = payload.prompt || '';

    // Find all Slack URLs in the prompt
    const matches = [...userPrompt.matchAll(SLACK_URL_PATTERN)];
    if (matches.length === 0) {
      process.exit(0);
    }

    // Parse all found URLs
    const parsedUrls = matches
      .map(match => parseSlackUrl(match[0]))
      .filter(Boolean);

    // Get full URLs (including query params like thread_ts)
    const fullUrlPattern = /https:\/\/[a-zA-Z0-9-]+\.slack\.com\/archives\/[A-Z0-9]+\/p\d+[^\s]*/g;
    const fullUrls = userPrompt.match(fullUrlPattern) || matches.map(m => m[0]);

    if (parsedUrls.length === 0) {
      process.exit(0);
    }

    // Output instructions
    const output = buildSlackInstructions(parsedUrls, fullUrls);
    console.log(output.join('\n'));

    process.exit(0);
  } catch (error) {
    // Silent fail - don't block user interaction
    process.exit(0);
  }
}

main();
