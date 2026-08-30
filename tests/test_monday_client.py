"""
Test suite for Monday.com API client
Uses mocked API responses - no real Monday.com connection required
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.monday_client import MondayClient, MondayAPIError


class TestMondayClientInit:
    """Test Monday client initialization"""
    
    def test_init_with_token(self):
        """Test initialization with API token"""
        client = MondayClient(api_token="test_token_123")
        assert client.api_token == "test_token_123"
        assert client.api_url == "https://api.monday.com/v2"
    
    def test_init_without_token(self):
        """Test initialization without token (uses config)"""
        with patch("app.monday_client.Config.MONDAY_API_TOKEN", "config_token"):
            client = MondayClient()
            assert client.api_token == "config_token"


class TestMondayClientRequest:
    """Test API request handling"""
    
    @patch("app.monday_client.requests.post")
    def test_request_success(self, mock_post):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_post.return_value = mock_response
        
        client = MondayClient(api_token="test_token")
        result = client._request("query { test }")
        
        assert result == {"test": "value"}
        mock_post.assert_called_once()
    
    @patch("app.monday_client.requests.post")
    def test_request_auth_error(self, mock_post):
        """Test authentication error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        client = MondayClient(api_token="invalid_token")
        
        with pytest.raises(MondayAPIError, match="Authentication failed"):
            client._request("query { test }")
    
    @patch("app.monday_client.requests.post")
    def test_request_graphql_error(self, mock_post):
        """Test GraphQL error response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Invalid query"}]
        }
        mock_post.return_value = mock_response
        
        client = MondayClient(api_token="test_token")
        
        with pytest.raises(MondayAPIError, match="GraphQL error"):
            client._request("invalid query")
    
    @patch("app.monday_client.requests.post")
    def test_request_rate_limit(self, mock_post):
        """Test rate limit error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        client = MondayClient(api_token="test_token")
        
        with pytest.raises(MondayAPIError, match="Rate limit"):
            client._request("query { test }")
    
    @patch("app.monday_client.requests.post")
    def test_request_timeout(self, mock_post):
        """Test request timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        client = MondayClient(api_token="test_token", )
        client.max_retries = 1
        
        with pytest.raises(MondayAPIError, match="timeout"):
            client._request("query { test }")


class TestGetBoardItems:
    """Test fetching board items"""
    
    @patch.object(MondayClient, "_request")
    def test_get_board_items_success(self, mock_request):
        """Test successful item fetch"""
        mock_request.return_value = {
            "boards": [
                {
                    "items_page": {
                        "cursor": None,
                        "items": [
                            {
                                "id": "item1",
                                "name": "Deal 1",
                                "created_at": "2026-01-01",
                                "column_values": [],
                            }
                        ],
                    }
                }
            ]
        }
        
        client = MondayClient(api_token="test_token")
        items = client.get_board_items("board123")
        
        assert len(items) == 1
        assert items[0]["id"] == "item1"
        assert items[0]["name"] == "Deal 1"
    
    @patch.object(MondayClient, "_request")
    def test_get_board_items_pagination(self, mock_request):
        """Test pagination through multiple pages"""
        # Mock responses for two pages
        mock_request.side_effect = [
            {
                "boards": [
                    {
                        "items_page": {
                            "cursor": "cursor_page2",
                            "items": [{"id": "item1", "name": "Deal 1", "column_values": []}],
                        }
                    }
                ]
            },
            {
                "boards": [
                    {
                        "items_page": {
                            "cursor": None,
                            "items": [{"id": "item2", "name": "Deal 2", "column_values": []}],
                        }
                    }
                ]
            },
        ]
        
        client = MondayClient(api_token="test_token")
        items = client.get_board_items("board123")
        
        assert len(items) == 2
        assert mock_request.call_count == 2
    
    @patch.object(MondayClient, "_request")
    def test_get_board_items_not_found(self, mock_request):
        """Test board not found"""
        mock_request.return_value = {"boards": []}
        
        client = MondayClient(api_token="test_token")
        
        with pytest.raises(MondayAPIError, match="not found"):
            client.get_board_items("invalid_board")


class TestGetBoardColumns:
    """Test fetching board columns"""
    
    @patch.object(MondayClient, "_request")
    def test_get_board_columns_success(self, mock_request):
        """Test successful column fetch"""
        mock_request.return_value = {
            "boards": [
                {
                    "columns": [
                        {
                            "id": "col1",
                            "title": "Deal Name",
                            "type": "text",
                            "settings_str": None,
                        },
                        {
                            "id": "col2",
                            "title": "Deal Value",
                            "type": "numbers",
                            "settings_str": None,
                        },
                    ]
                }
            ]
        }
        
        client = MondayClient(api_token="test_token")
        columns = client.get_board_columns("board123")
        
        assert len(columns) == 2
        assert columns[0]["id"] == "col1"
        assert columns[0]["title"] == "Deal Name"
    
    @patch.object(MondayClient, "_request")
    def test_get_board_columns_not_found(self, mock_request):
        """Test board not found"""
        mock_request.return_value = {"boards": []}
        
        client = MondayClient(api_token="test_token")
        
        with pytest.raises(MondayAPIError, match="not found"):
            client.get_board_columns("invalid_board")


class TestTestConnection:
    """Test connection testing"""
    
    @patch.object(MondayClient, "_request")
    def test_test_connection_success(self, mock_request):
        """Test successful connection"""
        mock_request.return_value = {"me": {"id": "user1", "name": "Test User"}}
        
        client = MondayClient(api_token="test_token")
        result = client.test_connection()
        
        assert result is True
    
    @patch.object(MondayClient, "_request")
    def test_test_connection_failure(self, mock_request):
        """Test failed connection"""
        mock_request.side_effect = MondayAPIError("Connection failed")
        
        client = MondayClient(api_token="test_token")
        result = client.test_connection()
        
        assert result is False
    
    def test_test_connection_no_token(self):
        """Test connection without token"""
        with patch("app.monday_client.Config.MONDAY_API_TOKEN", ""):
            client = MondayClient(api_token=None)
            result = client.test_connection()
            
            assert result is False


class TestRequestRetry:
    """Test request retry logic"""
    
    @patch("app.monday_client.requests.post")
    def test_retry_on_timeout(self, mock_post):
        """Test retries on timeout"""
        import requests
        
        # Fail twice, succeed on third attempt
        mock_post.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            Mock(status_code=200, json=lambda: {"data": {"result": "success"}}),
        ]
        
        client = MondayClient(api_token="test_token")
        client.max_retries = 3
        result = client._request("query { test }")
        
        assert result == {"result": "success"}
        assert mock_post.call_count == 3
    
    @patch("app.monday_client.requests.post")
    def test_exhaust_retries(self, mock_post):
        """Test exhausting retry attempts"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        client = MondayClient(api_token="test_token")
        client.max_retries = 2
        
        with pytest.raises(MondayAPIError, match="timeout"):
            client._request("query { test }")
        
        assert mock_post.call_count == 2
