"""HTTP transport wrapper for OSDU MCP Server.

This module provides HTTP transport support with custom header extraction
for the osdu_mcp_user_token authentication header.
"""

import contextlib
from collections.abc import AsyncIterator
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send

from .server import mcp
from .shared.logging_manager import get_logger
from .shared.request_context import (
    clear_request_data_partition,
    clear_request_metadata,
    clear_request_server_url,
    clear_request_user_token,
    set_request_data_partition,
    set_request_metadata,
    set_request_server_url,
    set_request_user_token,
)

logger = get_logger(__name__)


# Header name for passing user token (case-insensitive in HTTP)
USER_TOKEN_HEADER = "osdu_mcp_user_token"
# Alternative header names (some clients prefer different formats)
ALT_TOKEN_HEADERS = ["osdu-mcp-user-token", "x-osdu-mcp-user-token"]

# Header names for server URL (case-insensitive in HTTP)
SERVER_URL_HEADER = "osdu_mcp_server_url"
ALT_SERVER_URL_HEADERS = ["osdu-mcp-server-url", "x-osdu-mcp-server-url"]

# Header names for data partition (case-insensitive in HTTP)
DATA_PARTITION_HEADER = "osdu_mcp_data_partition"
ALT_DATA_PARTITION_HEADERS = ["osdu-mcp-data-partition", "x-osdu-mcp-data-partition"]


class TokenExtractionMiddleware:
    """Middleware to extract user token and config from HTTP headers.

    This middleware checks for the following headers (and alternatives)
    and stores values in the request context for use by downstream handlers:
    - osdu_mcp_user_token: Authentication token
    - osdu_mcp_server_url: OSDU server URL override
    - osdu_mcp_data_partition: Data partition override
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application to wrap
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process the request and extract token from headers.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract headers (they come as list of tuples with bytes)
        headers = dict(scope.get("headers", []))

        # Try to find the token header (case-insensitive)
        token = self._extract_header(
            headers, [USER_TOKEN_HEADER] + ALT_TOKEN_HEADERS
        )
        if token:
            # Remove "Bearer " prefix if present
            if token.lower().startswith("bearer "):
                token = token[7:]
            set_request_user_token(token)
            set_request_metadata("token_source", "http_header")
            logger.debug(
                f"Extracted user token from header (length: {len(token)})"
            )

        # Try to find the server URL header
        server_url = self._extract_header(
            headers, [SERVER_URL_HEADER] + ALT_SERVER_URL_HEADERS
        )
        if server_url:
            # Ensure URL doesn't have trailing slash for consistency
            server_url = server_url.rstrip("/")
            set_request_server_url(server_url)
            set_request_metadata("server_url_source", "http_header")
            logger.debug(f"Extracted server URL from header: {server_url}")

        # Try to find the data partition header
        data_partition = self._extract_header(
            headers, [DATA_PARTITION_HEADER] + ALT_DATA_PARTITION_HEADERS
        )
        if data_partition:
            set_request_data_partition(data_partition)
            set_request_metadata("data_partition_source", "http_header")
            logger.debug(f"Extracted data partition from header: {data_partition}")

        try:
            await self.app(scope, receive, send)
        finally:
            # Clean up context after request
            clear_request_user_token()
            clear_request_server_url()
            clear_request_data_partition()
            clear_request_metadata()

    def _extract_header(
        self, headers: dict[bytes, bytes], header_names: list[str]
    ) -> str | None:
        """Extract a header value from the headers dict.

        Args:
            headers: Dictionary of headers (bytes keys and values)
            header_names: List of header names to try (case-insensitive)

        Returns:
            Header value as string, or None if not found
        """
        for header_name in header_names:
            header_bytes = header_name.lower().encode("latin-1")
            if header_bytes in headers:
                value = headers[header_bytes]
                if isinstance(value, bytes):
                    return value.decode("latin-1")
                return str(value)
        return None


async def health_check_endpoint(request: Request) -> Response:
    """Health check endpoint for load balancers and monitoring.

    Args:
        request: Starlette request object

    Returns:
        JSON response with health status
    """
    return JSONResponse(
        {
            "status": "healthy",
            "service": "osdu-mcp-server",
            "transport": "http",
        }
    )


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[dict[str, Any]]:
    """Manage application lifespan for HTTP server.

    Args:
        app: Starlette application

    Yields:
        Empty context dict
    """
    logger.info("Starting OSDU MCP Server (HTTP transport)")
    async with mcp.session_manager.run():
        yield {}
    logger.info("Shutting down OSDU MCP Server (HTTP transport)")


def create_http_app(
    enable_cors: bool = True,
    cors_origins: list[str] | None = None,
) -> Starlette:
    """Create a Starlette app wrapping the MCP server with HTTP support.

    This creates an HTTP application that:
    1. Extracts auth tokens from the osdu_mcp_user_token header
    2. Provides a health check endpoint at /health
    3. Mounts the MCP streamable HTTP app at /mcp
    4. Optionally enables CORS for browser clients

    Args:
        enable_cors: Whether to enable CORS middleware
        cors_origins: List of allowed origins for CORS (default: ["*"])

    Returns:
        Configured Starlette application
    """
    if cors_origins is None:
        cors_origins = ["*"]

    # Configure MCP to use root path since we're mounting at /mcp
    mcp.settings.streamable_http_path = "/"

    # Build routes
    routes = [
        Route("/health", health_check_endpoint, methods=["GET"]),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ]

    # Build middleware stack
    middleware: list[Middleware] = [
        Middleware(TokenExtractionMiddleware),
    ]

    if enable_cors:
        middleware.append(
            Middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
                allow_headers=["*"],
                expose_headers=["Mcp-Session-Id"],
            )
        )

    # Create the Starlette app
    app = Starlette(
        routes=routes,
        middleware=middleware,
        lifespan=lifespan,
    )

    return app


# Pre-configured HTTP app for use with uvicorn
# Usage: uvicorn osdu_mcp_server.http_app:app --host 0.0.0.0 --port 8000
app = create_http_app()
