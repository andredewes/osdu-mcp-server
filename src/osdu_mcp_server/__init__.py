"""OSDU MCP Server - MCP server for OSDU platform integration.

Supports multiple transport modes:
- stdio: Standard input/output (default, for CLI/MCP clients)
- streamable-http: HTTP-based transport with streaming support
- sse: Server-Sent Events transport

For HTTP transports, auth tokens can be passed via the 'osdu_mcp_user_token' header.
"""

from .prompts import list_mcp_assets
from .server import mcp

__version__ = "0.8.0"
__all__ = ["list_mcp_assets", "mcp"]
