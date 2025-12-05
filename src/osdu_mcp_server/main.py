"""Main entry point for OSDU MCP Server.

Supports multiple transport modes:
- stdio: Standard input/output (default, for CLI/MCP clients)
- streamable-http: HTTP-based transport with streaming support
- sse: Server-Sent Events transport (legacy)

When using HTTP transports, auth tokens can be passed via the
'osdu_mcp_user_token' HTTP header.
"""

import argparse
import os

from .server import mcp
from .shared.logging_manager import configure_logging, get_logger

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="OSDU MCP Server - Model Context Protocol server for OSDU platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with stdio transport (default)
  osdu-mcp-server

  # Run with streamable HTTP transport (with token header support)
  osdu-mcp-server --transport streamable-http --port 8000

  # Run with SSE transport on custom host/port
  osdu-mcp-server --transport sse --host 0.0.0.0 --port 9000

  # Run HTTP app directly with uvicorn (recommended for production)
  uvicorn osdu_mcp_server.http_app:app --host 0.0.0.0 --port 8000

Environment Variables:
  OSDU_MCP_TRANSPORT    Default transport (stdio, streamable-http, sse)
  OSDU_MCP_HOST         Default host for HTTP transports
  OSDU_MCP_PORT         Default port for HTTP transports

HTTP Header Authentication:
  When using HTTP transports, you can pass an OAuth token via the
  'osdu_mcp_user_token' header (or 'osdu-mcp-user-token', 'x-osdu-mcp-user-token').
  This token will be used for authenticating with OSDU APIs.
        """,
    )

    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "streamable-http", "sse"],
        default=os.environ.get("OSDU_MCP_TRANSPORT", "stdio"),
        help="Transport type (default: stdio or OSDU_MCP_TRANSPORT env var)",
    )

    parser.add_argument(
        "--host",
        default=os.environ.get("OSDU_MCP_HOST", "127.0.0.1"),
        help="Host to bind for HTTP transports (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=int(os.environ.get("OSDU_MCP_PORT", "8000")),
        help="Port for HTTP transports (default: 8000)",
    )

    return parser.parse_args()


def run_with_uvicorn(host: str, port: int) -> None:
    """Run the HTTP app with uvicorn for streamable HTTP transport.

    This provides proper token extraction from HTTP headers.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    import uvicorn

    from .http_app import create_http_app

    logger.info(
        "Starting OSDU MCP Server (streamable-http) on %s:%s", host, port
    )
    logger.info("Token header: osdu_mcp_user_token (or osdu-mcp-user-token)")

    app = create_http_app()
    uvicorn.run(app, host=host, port=port)


def main() -> None:
    """Run the MCP server with configured transport."""
    # Parse command line arguments
    args = parse_args()

    # Configure logging based on environment variables
    configure_logging()

    # Run the MCP server with specified transport
    if args.transport == "stdio":
        logger.info("Starting OSDU MCP Server (stdio transport)")
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        # Use uvicorn with our custom HTTP app for proper header extraction
        run_with_uvicorn(args.host, args.port)
    elif args.transport == "sse":
        # SSE transport can use the built-in FastMCP runner
        logger.info(
            "Starting OSDU MCP Server (sse) on %s:%s", args.host, args.port
        )
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()
