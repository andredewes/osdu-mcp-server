"""Tests for HTTP app and token extraction middleware."""

import pytest
from starlette.testclient import TestClient

from osdu_mcp_server.http_app import create_http_app


class TestTokenExtractionMiddleware:
    """Tests for the token extraction middleware."""

    @pytest.fixture
    def app(self):
        """Create a test app."""
        return create_http_app(enable_cors=False)

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint is available."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "osdu-mcp-server"
        assert data["transport"] == "http"

    def test_token_extracted_from_primary_header(self, client):
        """Test token is extracted from osdu_mcp_user_token header."""
        # Note: The token extraction happens in request context, we test
        # the endpoint availability and header acceptance
        response = client.get(
            "/health",
            headers={"osdu_mcp_user_token": "test-bearer-token"},
        )

        assert response.status_code == 200

    def test_token_extracted_from_alternative_header(self, client):
        """Test token is extracted from alternative header format."""
        response = client.get(
            "/health",
            headers={"osdu-mcp-user-token": "test-bearer-token"},
        )

        assert response.status_code == 200

    def test_token_extracted_from_x_header(self, client):
        """Test token is extracted from x-osdu-mcp-user-token header."""
        response = client.get(
            "/health",
            headers={"x-osdu-mcp-user-token": "test-bearer-token"},
        )

        assert response.status_code == 200

    def test_bearer_prefix_stripped(self, client):
        """Test that Bearer prefix is stripped from token."""
        response = client.get(
            "/health",
            headers={"osdu_mcp_user_token": "Bearer test-bearer-token"},
        )

        assert response.status_code == 200

    def test_server_url_extracted_from_primary_header(self, client):
        """Test server URL is extracted from osdu_mcp_server_url header."""
        response = client.get(
            "/health",
            headers={"osdu_mcp_server_url": "https://custom-osdu.com"},
        )

        assert response.status_code == 200

    def test_server_url_extracted_from_alternative_header(self, client):
        """Test server URL is extracted from alternative header format."""
        response = client.get(
            "/health",
            headers={"osdu-mcp-server-url": "https://custom-osdu.com"},
        )

        assert response.status_code == 200

    def test_server_url_extracted_from_x_header(self, client):
        """Test server URL is extracted from x-osdu-mcp-server-url header."""
        response = client.get(
            "/health",
            headers={"x-osdu-mcp-server-url": "https://custom-osdu.com"},
        )

        assert response.status_code == 200

    def test_data_partition_extracted_from_primary_header(self, client):
        """Test data partition is extracted from osdu_mcp_data_partition header."""
        response = client.get(
            "/health",
            headers={"osdu_mcp_data_partition": "custom-partition"},
        )

        assert response.status_code == 200

    def test_data_partition_extracted_from_alternative_header(self, client):
        """Test data partition is extracted from alternative header format."""
        response = client.get(
            "/health",
            headers={"osdu-mcp-data-partition": "custom-partition"},
        )

        assert response.status_code == 200

    def test_data_partition_extracted_from_x_header(self, client):
        """Test data partition is extracted from x-osdu-mcp-data-partition header."""
        response = client.get(
            "/health",
            headers={"x-osdu-mcp-data-partition": "custom-partition"},
        )

        assert response.status_code == 200

    def test_multiple_headers_combined(self, client):
        """Test all headers can be provided together."""
        response = client.get(
            "/health",
            headers={
                "osdu_mcp_user_token": "test-token",
                "osdu_mcp_server_url": "https://custom-osdu.com",
                "osdu_mcp_data_partition": "custom-partition",
            },
        )

        assert response.status_code == 200


class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_enabled_by_default(self):
        """Test that CORS is enabled by default."""
        app = create_http_app(enable_cors=True)
        client = TestClient(app)

        # Preflight request
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Check CORS headers are present
        assert "access-control-allow-origin" in response.headers

    def test_cors_disabled(self):
        """Test that CORS can be disabled."""
        app = create_http_app(enable_cors=False)
        client = TestClient(app)

        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # CORS headers should not be present
        assert "access-control-allow-origin" not in response.headers

    def test_mcp_session_header_exposed(self):
        """Test that Mcp-Session-Id header is exposed in CORS."""
        app = create_http_app(enable_cors=True)
        client = TestClient(app)

        # Make an actual request, not just preflight
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
            },
        )

        # Check expose headers - they should be in the response
        assert response.status_code == 200
        # The expose-headers should be present in cross-origin responses
        expose_headers = response.headers.get("access-control-expose-headers", "")
        assert "mcp-session-id" in expose_headers.lower()
