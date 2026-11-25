"""Call the globally registered news-briefing MCP, including from older chats."""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import tomllib

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

TOOLS = {'get_news_briefing_status', 'get_latest_news_briefing', 'kakao_send_text', 'kakao_send_file'}


async def invoke(tool=None, arguments=None):
    codex_dir = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    config = tomllib.loads((codex_dir / 'config.toml').read_text(encoding='utf-8-sig'))
    entry = config.get('mcp_servers', {}).get('news-briefing')
    if not entry:
        raise ValueError('Configure your own compatible news-briefing stdio MCP server first; see the repository README.')
    if entry.get('enabled', True) is False:
        raise ValueError('The configured news-briefing MCP server is disabled.')
    if not entry.get('command'):
        raise ValueError('This fallback helper supports stdio MCP entries with command/args only.')
    params = StdioServerParameters(command=entry['command'], args=entry.get('args', []),
                                   env={**os.environ, **entry.get('env', {})})
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=240)) as client:
            await client.initialize()
            if tool is None:
                result = await client.list_tools()
                return {'tools': [t.model_dump(mode='json') for t in result.tools]}
            if tool not in TOOLS:
                raise ValueError('Unsupported news-briefing tool.')
            result = await client.call_tool(tool, arguments or {})
            if result.isError:
                raise RuntimeError('\n'.join(c.text for c in result.content if c.type == 'text'))
            if result.structuredContent is not None:
                return result.structuredContent
            return json.loads(next(c.text for c in result.content if c.type == 'text'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', nargs='?', choices=sorted(TOOLS))
    parser.add_argument('--list-tools', action='store_true')
    parser.add_argument('--arguments-file', type=Path)
    args = parser.parse_args()
    if not args.list_tools and not args.tool:
        parser.error('Choose a tool or --list-tools.')
    arguments = json.loads(args.arguments_file.read_text(encoding='utf-8-sig')) if args.arguments_file else {}
    result = asyncio.run(invoke(None if args.list_tools else args.tool, arguments))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
