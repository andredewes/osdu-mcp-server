"""Request context for storing per-request data like user tokens and configuration.

This module provides a context variable-based mechanism to pass
authentication tokens and configuration from HTTP headers to the OSDU API clients.
When running as an HTTP server, these can be passed via HTTP headers:
- 'osdu_mcp_user_token' - Authentication token
- 'osdu_mcp_server_url' - OSDU server URL override
- 'osdu_mcp_data_partition' - Data partition override
"""

from contextvars import ContextVar
from typing import Any

# Context variable to store the user token for the current request
_request_user_token: ContextVar[str | None] = ContextVar(
    "osdu_mcp_user_token", default=None
)

# Context variable to store the server URL for the current request
_request_server_url: ContextVar[str | None] = ContextVar(
    "osdu_mcp_server_url", default=None
)

# Context variable to store the data partition for the current request
_request_data_partition: ContextVar[str | None] = ContextVar(
    "osdu_mcp_data_partition", default=None
)

# Context variable to store additional request metadata
_request_metadata: ContextVar[dict[str, Any]] = ContextVar(
    "request_metadata", default={}
)


def set_request_user_token(token: str | None) -> None:
    """Set the user token for the current request context.

    Args:
        token: The OAuth Bearer token (without "Bearer " prefix)
    """
    _request_user_token.set(token)


def get_request_user_token() -> str | None:
    """Get the user token from the current request context.

    Returns:
        The OAuth Bearer token if set, None otherwise
    """
    return _request_user_token.get()


def clear_request_user_token() -> None:
    """Clear the user token from the current request context."""
    _request_user_token.set(None)


def set_request_server_url(url: str | None) -> None:
    """Set the OSDU server URL for the current request context.

    Args:
        url: The OSDU server URL (e.g., 'https://osdu.example.com')
    """
    _request_server_url.set(url)


def get_request_server_url() -> str | None:
    """Get the OSDU server URL from the current request context.

    Returns:
        The OSDU server URL if set, None otherwise
    """
    return _request_server_url.get()


def clear_request_server_url() -> None:
    """Clear the server URL from the current request context."""
    _request_server_url.set(None)


def set_request_data_partition(partition: str | None) -> None:
    """Set the data partition for the current request context.

    Args:
        partition: The OSDU data partition ID
    """
    _request_data_partition.set(partition)


def get_request_data_partition() -> str | None:
    """Get the data partition from the current request context.

    Returns:
        The data partition ID if set, None otherwise
    """
    return _request_data_partition.get()


def clear_request_data_partition() -> None:
    """Clear the data partition from the current request context."""
    _request_data_partition.set(None)


def set_request_metadata(key: str, value: Any) -> None:
    """Set metadata for the current request context.

    Args:
        key: Metadata key
        value: Metadata value
    """
    current = _request_metadata.get()
    if current is None:
        current = {}
    current[key] = value
    _request_metadata.set(current)


def get_request_metadata(key: str, default: Any = None) -> Any:
    """Get metadata from the current request context.

    Args:
        key: Metadata key
        default: Default value if key not found

    Returns:
        The metadata value or default
    """
    current = _request_metadata.get()
    if current is None:
        return default
    return current.get(key, default)


def clear_request_metadata() -> None:
    """Clear all metadata from the current request context."""
    _request_metadata.set({})
