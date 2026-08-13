"""MCP server entrypoint for local stdio and Streamable HTTP."""

from __future__ import annotations

import argparse
from typing import Any

from mcp.server import MCPServer

from .adapter import DesignFlowAdapter
from .config import AdapterConfig
from .resources import register_resources
from .tools import register_tools


adapter = DesignFlowAdapter(AdapterConfig.from_env())
mcp = MCPServer(
    "Design Flow MCP",
    instructions=(
        "A thin adapter over Design Flow System v0.2. Draft imports and previews are "
        "non-authoritative. Only lock_round changes decision authority, through the engine."
    ),
)
register_tools(mcp, adapter)
register_resources(mcp, adapter)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Design Flow MCP adapter")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="Local subprocess transport or remotely deployable HTTP transport",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.transport == "stdio":
        mcp.run()
    else:
        options: dict[str, Any] = {"host": args.host, "port": args.port}
        mcp.run("streamable-http", **options)


if __name__ == "__main__":
    main()

