#!/usr/bin/env python3
"""
Slack API Client - Python alternative to slack-mcp-server

Supports:
- conversations_history: Get channel/DM messages
- conversations_replies: Get thread replies
- conversations_search: Search messages
- channels_list: List channels
- reactions_add: Add emoji reaction
- add_message: Post message to channel/thread
- file download: Download attachments from messages

Authentication: Uses XOXC + XOXD tokens (browser session tokens)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class SlackClient:
    """Slack API client using browser session tokens"""

    BASE_URL = "https://slack.com/api"

    def __init__(self, xoxc_token: str, xoxd_token: str):
        self.xoxc_token = xoxc_token
        self.xoxd_token = xoxd_token

    def _request(self, method: str, params: Optional[Dict[str, Any]] = None, post_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make API request to Slack"""
        url = f"{self.BASE_URL}/{method}"

        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"

        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.xoxc_token}")
        req.add_header("Cookie", f"d={self.xoxd_token}")

        if post_data:
            req.add_header("Content-Type", "application/json; charset=utf-8")
            data = json.dumps(post_data).encode("utf-8")
            req.data = data

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            return {"ok": False, "error": f"HTTP {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"URL Error: {e.reason}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_channel_history(
        self,
        channel_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        latest: Optional[str] = None,
        oldest: Optional[str] = None,
        include_all_metadata: bool = False
    ) -> Dict[str, Any]:
        """Get messages from a channel or DM"""
        params = {
            "channel": channel_id,
            "limit": limit,
            "cursor": cursor,
            "latest": latest,
            "oldest": oldest,
            "include_all_metadata": "true" if include_all_metadata else None
        }
        return self._request("conversations.history", params)

    def get_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
        limit: int = 100,
        cursor: Optional[str] = None,
        inclusive: bool = True
    ) -> Dict[str, Any]:
        """Get replies to a thread"""
        params = {
            "channel": channel_id,
            "ts": thread_ts,
            "limit": limit,
            "cursor": cursor,
            "inclusive": "true" if inclusive else "false"
        }
        return self._request("conversations.replies", params)

    def search_messages(
        self,
        query: str,
        count: int = 20,
        page: int = 1,
        sort: str = "timestamp",
        sort_dir: str = "desc"
    ) -> Dict[str, Any]:
        """Search messages (requires user token, not bot token)"""
        params = {
            "query": query,
            "count": count,
            "page": page,
            "sort": sort,
            "sort_dir": sort_dir
        }
        return self._request("search.messages", params)

    def list_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100,
        cursor: Optional[str] = None,
        exclude_archived: bool = True
    ) -> Dict[str, Any]:
        """List channels"""
        params = {
            "types": types,
            "limit": limit,
            "cursor": cursor,
            "exclude_archived": "true" if exclude_archived else "false"
        }
        return self._request("conversations.list", params)

    def add_reaction(
        self,
        channel_id: str,
        timestamp: str,
        emoji: str
    ) -> Dict[str, Any]:
        """Add emoji reaction to a message"""
        post_data = {
            "channel": channel_id,
            "timestamp": timestamp,
            "name": emoji.strip(":")
        }
        return self._request("reactions.add", post_data=post_data)

    def post_message(
        self,
        channel_id: str,
        text: str,
        thread_ts: Optional[str] = None,
        reply_broadcast: bool = False
    ) -> Dict[str, Any]:
        """Post a message to a channel or thread"""
        post_data = {
            "channel": channel_id,
            "text": text
        }
        if thread_ts:
            post_data["thread_ts"] = thread_ts
            post_data["reply_broadcast"] = reply_broadcast
        return self._request("chat.postMessage", post_data=post_data)

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information"""
        return self._request("users.info", {"user": user_id})

    def get_users_list(self, limit: int = 100, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Get list of users"""
        return self._request("users.list", {"limit": limit, "cursor": cursor})

    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information"""
        return self._request("conversations.info", {"channel": channel_id})

    def download_file(self, url: str, output_path: str) -> bool:
        """Download a file from Slack using authenticated request"""
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {self.xoxc_token}")
        req.add_header("Cookie", f"d={self.xoxd_token}")

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                # Create parent directories if needed
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            return True
        except Exception as e:
            print(f"Error downloading file: {e}", file=sys.stderr)
            return False


def parse_slack_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse Slack message URL to extract channel_id and timestamps

    URL formats:
    - https://workspace.slack.com/archives/C05AZF69J9Z/p1769774454630549
    - https://workspace.slack.com/archives/C05AZF69J9Z/p1769774454630549?thread_ts=1769174779.798959&cid=C05AZF69J9Z
    """
    pattern = r"https://[^/]+\.slack\.com/archives/([A-Z0-9]+)/p(\d+)"
    match = re.match(pattern, url)

    if not match:
        return None

    channel_id = match.group(1)
    raw_ts = match.group(2)

    # Convert URL timestamp (p1769774454630549) to API format (1769774454.630549)
    message_ts = f"{raw_ts[:-6]}.{raw_ts[-6:]}"

    result = {
        "channel_id": channel_id,
        "message_ts": message_ts
    }

    # Check for thread_ts in query params
    if "thread_ts=" in url:
        thread_match = re.search(r"thread_ts=([0-9.]+)", url)
        if thread_match:
            result["thread_ts"] = thread_match.group(1)

    return result


def format_message(msg: Dict[str, Any], users_cache: Dict[str, str] = None) -> str:
    """Format a Slack message for display"""
    user_id = msg.get("user", msg.get("bot_id", "unknown"))
    user_name = users_cache.get(user_id, user_id) if users_cache else user_id

    ts = msg.get("ts", "")
    if ts:
        try:
            dt = datetime.fromtimestamp(float(ts))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = ts
    else:
        time_str = "unknown"

    text = msg.get("text", "")

    # Handle reactions
    reactions = msg.get("reactions", [])
    reaction_str = ""
    if reactions:
        reaction_parts = [f":{r['name']}: ({r['count']})" for r in reactions]
        reaction_str = f"\n  Reactions: {' '.join(reaction_parts)}"

    # Handle files
    files = msg.get("files", [])
    files_str = ""
    if files:
        file_parts = [f"📎 {f.get('name', 'unnamed')}" for f in files]
        files_str = f"\n  Files: {', '.join(file_parts)}"

    return f"[{time_str}] {user_name}:\n  {text}{reaction_str}{files_str}"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def format_file_info(f: Dict[str, Any], verbose: bool = False) -> str:
    """Format file info for display"""
    name = f.get('name', 'unnamed')
    size = format_file_size(f.get('size', 0))
    filetype = f.get('filetype', 'unknown')
    url = f.get('url_private_download') or f.get('url_private', '')
    permalink = f.get('permalink', '')

    if verbose:
        return (
            f"  📎 {name}\n"
            f"     Type: {filetype} | Size: {size}\n"
            f"     Download: {url}\n"
            f"     Permalink: {permalink}"
        )
    return f"  📎 {name} ({filetype}, {size})"


def extract_files_from_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract all files from a list of messages"""
    files = []
    for msg in messages:
        msg_files = msg.get('files', [])
        for f in msg_files:
            f['_message_ts'] = msg.get('ts', '')
            f['_message_user'] = msg.get('user', '')
            files.append(f)
    return files


def load_env_file(env_path: str, xoxc: str, xoxd: str) -> tuple:
    """Load tokens from a .env file"""
    if os.path.exists(env_path):
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key == "SLACK_XOXC_TOKEN" and not xoxc:
                            xoxc = value
                        elif key == "SLACK_XOXD_TOKEN" and not xoxd:
                            xoxd = value
        except:
            pass
    return xoxc, xoxd


def load_tokens() -> tuple:
    """Load tokens from environment or .env file"""
    xoxc = os.environ.get("SLACK_XOXC_TOKEN")
    xoxd = os.environ.get("SLACK_XOXD_TOKEN")

    # Load from skill's .env file
    if not (xoxc and xoxd):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_env_path = os.path.join(script_dir, ".env")
        xoxc, xoxd = load_env_file(skill_env_path, xoxc, xoxd)

    return xoxc, xoxd


def main():
    parser = argparse.ArgumentParser(
        description="Slack API Client - Read and interact with Slack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Read a message/thread from URL
  %(prog)s --url "https://workspace.slack.com/archives/C05AZF69J9Z/p1769774454630549?thread_ts=1769174779.798959"

  # Get channel history
  %(prog)s --history --channel C05AZF69J9Z --limit 10

  # Get thread replies
  %(prog)s --replies --channel C05AZF69J9Z --thread-ts 1769174779.798959

  # Search messages
  %(prog)s --search "keyword in:channel-name"

  # List channels
  %(prog)s --list-channels

  # Post message (use with caution)
  %(prog)s --post --channel C05AZF69J9Z --text "Hello!"

  # List files from a thread with details
  %(prog)s --url "..." --list-files

  # Download all files from a thread
  %(prog)s --url "..." --download-files --output-dir ./downloads

  # Output as JSON
  %(prog)s --url "..." --json
"""
    )

    # Actions
    parser.add_argument("--url", help="Slack message URL to read")
    parser.add_argument("--history", action="store_true", help="Get channel history")
    parser.add_argument("--replies", action="store_true", help="Get thread replies")
    parser.add_argument("--search", help="Search query")
    parser.add_argument("--list-channels", action="store_true", help="List channels")
    parser.add_argument("--post", action="store_true", help="Post a message")
    parser.add_argument("--user-info", help="Get user info by ID")
    parser.add_argument("--channel-info", help="Get channel info by ID")

    # File operations
    parser.add_argument("--list-files", action="store_true", help="List files from messages with details")
    parser.add_argument("--download-files", action="store_true", help="Download all files from messages")
    parser.add_argument("--output-dir", "-o", default="./slack-downloads", help="Output directory for downloads (default: ./slack-downloads)")

    # Parameters
    parser.add_argument("--channel", "-c", help="Channel ID")
    parser.add_argument("--thread-ts", help="Thread timestamp")
    parser.add_argument("--text", "-t", help="Message text (for posting)")
    parser.add_argument("--limit", "-l", type=int, default=20, help="Number of results (default: 20)")
    parser.add_argument("--cursor", help="Pagination cursor")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--pretty", action="store_true", help="Pretty format output (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output for files")

    args = parser.parse_args()

    # Load tokens
    xoxc, xoxd = load_tokens()
    if not (xoxc and xoxd):
        print("Error: Slack tokens not found.", file=sys.stderr)
        print("Set SLACK_XOXC_TOKEN and SLACK_XOXD_TOKEN environment variables", file=sys.stderr)
        print("or configure them in ~/.claude/.mcp.json", file=sys.stderr)
        sys.exit(1)

    client = SlackClient(xoxc, xoxd)
    result = None

    try:
        if args.url:
            parsed = parse_slack_url(args.url)
            if not parsed:
                print(f"Error: Could not parse Slack URL: {args.url}", file=sys.stderr)
                sys.exit(1)

            channel_id = parsed["channel_id"]

            if "thread_ts" in parsed:
                # Get thread replies
                result = client.get_thread_replies(channel_id, parsed["thread_ts"], limit=args.limit)
            else:
                # Get single message context
                result = client.get_channel_history(channel_id, limit=1, latest=parsed["message_ts"], inclusive=True)

        elif args.history:
            if not args.channel:
                print("Error: --channel required for --history", file=sys.stderr)
                sys.exit(1)
            result = client.get_channel_history(args.channel, limit=args.limit, cursor=args.cursor)

        elif args.replies:
            if not args.channel or not args.thread_ts:
                print("Error: --channel and --thread-ts required for --replies", file=sys.stderr)
                sys.exit(1)
            result = client.get_thread_replies(args.channel, args.thread_ts, limit=args.limit, cursor=args.cursor)

        elif args.search:
            result = client.search_messages(args.search, count=args.limit)

        elif args.list_channels:
            result = client.list_channels(limit=args.limit, cursor=args.cursor)

        elif args.post:
            if not args.channel or not args.text:
                print("Error: --channel and --text required for --post", file=sys.stderr)
                sys.exit(1)
            result = client.post_message(args.channel, args.text, thread_ts=args.thread_ts)

        elif args.user_info:
            result = client.get_user_info(args.user_info)

        elif args.channel_info:
            result = client.get_channel_info(args.channel_info)

        else:
            parser.print_help()
            sys.exit(0)

        # Output
        if result:
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                # Pretty format
                if not result.get("ok"):
                    print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
                    sys.exit(1)

                messages = result.get("messages", [])

                # Handle file operations
                if args.list_files or args.download_files:
                    files = extract_files_from_messages(messages)
                    if not files:
                        print("No files found in messages.")
                    else:
                        print(f"Found {len(files)} file(s):\n")
                        for i, f in enumerate(files, 1):
                            print(f"{i}. {format_file_info(f, verbose=args.verbose)}")

                        if args.download_files:
                            print(f"\nDownloading to: {args.output_dir}")
                            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
                            success = 0
                            for f in files:
                                url = f.get('url_private_download') or f.get('url_private')
                                name = f.get('name', 'unnamed')
                                if url:
                                    output_path = os.path.join(args.output_dir, name)
                                    print(f"  Downloading: {name}...", end=" ")
                                    if client.download_file(url, output_path):
                                        print("OK")
                                        success += 1
                                    else:
                                        print("FAILED")
                            print(f"\nDownloaded {success}/{len(files)} files.")
                elif messages:
                    print(f"Found {len(messages)} message(s):\n")
                    for msg in messages:
                        print(format_message(msg))
                        print("-" * 60)

                # Handle search results (search API returns different structure)
                if args.search:
                    search_data = result.get("messages", {})
                    if isinstance(search_data, dict):
                        search_messages = search_data.get("matches", [])
                        if search_messages:
                            print(f"Found {len(search_messages)} match(es):\n")
                            for msg in search_messages:
                                print(format_message(msg))
                                print("-" * 60)

                # Handle channel list
                channels = result.get("channels", [])
                if channels:
                    print(f"Found {len(channels)} channel(s):\n")
                    for ch in channels:
                        name = ch.get("name", "unnamed")
                        ch_id = ch.get("id", "")
                        is_private = "🔒" if ch.get("is_private") else "📢"
                        members = ch.get("num_members", 0)
                        print(f"{is_private} #{name} ({ch_id}) - {members} members")

                # Handle user info
                user = result.get("user", {})
                if user:
                    print(f"User: {user.get('real_name', user.get('name', 'unknown'))}")
                    print(f"  ID: {user.get('id')}")
                    print(f"  Email: {user.get('profile', {}).get('email', 'N/A')}")
                    print(f"  Title: {user.get('profile', {}).get('title', 'N/A')}")

                # Handle channel info
                channel = result.get("channel", {})
                if channel:
                    print(f"Channel: #{channel.get('name', 'unnamed')}")
                    print(f"  ID: {channel.get('id')}")
                    print(f"  Topic: {channel.get('topic', {}).get('value', 'N/A')}")
                    print(f"  Purpose: {channel.get('purpose', {}).get('value', 'N/A')}")

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
