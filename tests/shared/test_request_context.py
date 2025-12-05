"""Tests for request context module."""

from osdu_mcp_server.shared.request_context import (
    clear_request_data_partition,
    clear_request_metadata,
    clear_request_server_url,
    clear_request_user_token,
    get_request_data_partition,
    get_request_metadata,
    get_request_server_url,
    get_request_user_token,
    set_request_data_partition,
    set_request_metadata,
    set_request_server_url,
    set_request_user_token,
)


class TestRequestContext:
    """Tests for request context functionality."""

    def teardown_method(self) -> None:
        """Clean up context after each test."""
        clear_request_user_token()
        clear_request_server_url()
        clear_request_data_partition()
        clear_request_metadata()

    def test_set_and_get_user_token(self) -> None:
        """Test setting and getting user token."""
        token = "test-token-12345"
        set_request_user_token(token)

        assert get_request_user_token() == token

    def test_get_user_token_when_not_set(self) -> None:
        """Test getting token when none is set."""
        assert get_request_user_token() is None

    def test_clear_user_token(self) -> None:
        """Test clearing user token."""
        set_request_user_token("test-token")
        clear_request_user_token()

        assert get_request_user_token() is None

    def test_set_and_get_metadata(self) -> None:
        """Test setting and getting metadata."""
        set_request_metadata("key1", "value1")
        set_request_metadata("key2", {"nested": "value"})

        assert get_request_metadata("key1") == "value1"
        assert get_request_metadata("key2") == {"nested": "value"}

    def test_get_metadata_with_default(self) -> None:
        """Test getting metadata with default value."""
        assert get_request_metadata("nonexistent", "default") == "default"
        assert get_request_metadata("nonexistent") is None

    def test_clear_metadata(self) -> None:
        """Test clearing all metadata."""
        set_request_metadata("key1", "value1")
        set_request_metadata("key2", "value2")
        clear_request_metadata()

        assert get_request_metadata("key1") is None
        assert get_request_metadata("key2") is None

    def test_multiple_tokens_isolation(self) -> None:
        """Test that setting a new token replaces the old one."""
        set_request_user_token("token1")
        assert get_request_user_token() == "token1"

        set_request_user_token("token2")
        assert get_request_user_token() == "token2"

    def test_null_token(self) -> None:
        """Test setting None as token."""
        set_request_user_token("initial")
        set_request_user_token(None)

        assert get_request_user_token() is None


class TestServerUrlContext:
    """Tests for server URL request context functionality."""

    def teardown_method(self) -> None:
        """Clean up context after each test."""
        clear_request_server_url()

    def test_set_and_get_server_url(self) -> None:
        """Test setting and getting server URL."""
        url = "https://osdu.example.com"
        set_request_server_url(url)

        assert get_request_server_url() == url

    def test_get_server_url_when_not_set(self) -> None:
        """Test getting server URL when none is set."""
        assert get_request_server_url() is None

    def test_clear_server_url(self) -> None:
        """Test clearing server URL."""
        set_request_server_url("https://osdu.example.com")
        clear_request_server_url()

        assert get_request_server_url() is None

    def test_server_url_replacement(self) -> None:
        """Test that setting a new URL replaces the old one."""
        set_request_server_url("https://first.com")
        assert get_request_server_url() == "https://first.com"

        set_request_server_url("https://second.com")
        assert get_request_server_url() == "https://second.com"

    def test_null_server_url(self) -> None:
        """Test setting None as server URL."""
        set_request_server_url("https://initial.com")
        set_request_server_url(None)

        assert get_request_server_url() is None


class TestDataPartitionContext:
    """Tests for data partition request context functionality."""

    def teardown_method(self) -> None:
        """Clean up context after each test."""
        clear_request_data_partition()

    def test_set_and_get_data_partition(self) -> None:
        """Test setting and getting data partition."""
        partition = "my-partition"
        set_request_data_partition(partition)

        assert get_request_data_partition() == partition

    def test_get_data_partition_when_not_set(self) -> None:
        """Test getting data partition when none is set."""
        assert get_request_data_partition() is None

    def test_clear_data_partition(self) -> None:
        """Test clearing data partition."""
        set_request_data_partition("my-partition")
        clear_request_data_partition()

        assert get_request_data_partition() is None

    def test_data_partition_replacement(self) -> None:
        """Test that setting a new partition replaces the old one."""
        set_request_data_partition("partition1")
        assert get_request_data_partition() == "partition1"

        set_request_data_partition("partition2")
        assert get_request_data_partition() == "partition2"

    def test_null_data_partition(self) -> None:
        """Test setting None as data partition."""
        set_request_data_partition("initial")
        set_request_data_partition(None)

        assert get_request_data_partition() is None
