"""Tests for request context token integration with AuthHandler."""

import os
import time
from unittest.mock import patch

import jwt
import pytest

from osdu_mcp_server.shared.auth_handler import AuthHandler
from osdu_mcp_server.shared.config_manager import ConfigManager
from osdu_mcp_server.shared.request_context import (
    clear_request_user_token,
    set_request_user_token,
)


def create_valid_jwt(
    exp_offset: int = 3600,
    iss: str = "test-issuer",
    aud: str = "test-audience",
) -> str:
    """Create a valid JWT token for testing.

    Args:
        exp_offset: Seconds from now until expiration
        iss: Issuer claim
        aud: Audience claim

    Returns:
        Encoded JWT token
    """
    payload = {
        "exp": int(time.time()) + exp_offset,
        "iat": int(time.time()),
        "iss": iss,
        "aud": aud,
        "sub": "test-user",
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


class TestRequestContextTokenIntegration:
    """Tests for request context token integration with AuthHandler."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Set up environment variables for testing."""
        original_env = os.environ.copy()

        # Set minimal config
        os.environ["OSDU_MCP_SERVER_URL"] = "https://test.osdu.com"
        os.environ["OSDU_MCP_DATA_PARTITION"] = "test-partition"
        # Set Azure credentials to avoid auto-detection issues
        os.environ["AZURE_TENANT_ID"] = "test-tenant"

        yield

        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    @pytest.fixture(autouse=True)
    def cleanup_context(self):
        """Clean up request context after each test."""
        yield
        clear_request_user_token()

    @pytest.mark.asyncio
    async def test_request_token_takes_priority(self):
        """Test that request context token is used when available."""
        # Create a valid JWT for request context
        request_token = create_valid_jwt()
        set_request_user_token(request_token)

        config = ConfigManager()

        # Mock Azure credential to avoid actual auth
        with patch(
            "osdu_mcp_server.shared.auth_handler.DefaultAzureCredential"
        ) as mock_cred:
            auth_handler = AuthHandler(config)

            # Get token should return request context token
            token = await auth_handler.get_access_token()

            assert token == request_token
            # Azure credential should not have been called for token
            mock_cred.return_value.get_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_to_configured_auth_when_no_request_token(self):
        """Test fallback to configured auth when no request token is present."""
        # Set env var for user token mode
        os.environ["OSDU_MCP_USER_TOKEN"] = create_valid_jwt()

        config = ConfigManager()
        auth_handler = AuthHandler(config)

        # No request context token set
        token = await auth_handler.get_access_token()

        # Should use the environment token
        assert token == os.environ["OSDU_MCP_USER_TOKEN"]

    @pytest.mark.asyncio
    async def test_request_token_cleared_after_request(self):
        """Test that clearing request token reverts to configured auth."""
        request_token = create_valid_jwt()
        env_token = create_valid_jwt()

        # Set env token
        os.environ["OSDU_MCP_USER_TOKEN"] = env_token

        config = ConfigManager()
        auth_handler = AuthHandler(config)

        # First, set request token
        set_request_user_token(request_token)
        token1 = await auth_handler.get_access_token()
        assert token1 == request_token

        # Clear request token
        clear_request_user_token()
        token2 = await auth_handler.get_access_token()
        assert token2 == env_token
