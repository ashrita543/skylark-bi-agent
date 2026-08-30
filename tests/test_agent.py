"""
Test suite for BI Agent
Tests query planning and execution
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agent import Agent
from app.monday_client import MondayClient, MondayAPIError


class TestAgentInit:
    """Test agent initialization"""
    
    def test_init_default(self):
        """Test default initialization"""
        with patch("app.agent.MondayClient"):
            agent = Agent()
            assert agent.deals_cache is None
            assert agent.work_orders_cache is None
    
    def test_init_with_client(self):
        """Test initialization with existing client"""
        mock_client = Mock(spec=MondayClient)
        agent = Agent(mock_client)
        assert agent.monday_client == mock_client


class TestQueryPlanning:
    """Test query planning"""
    
    def test_plan_query_pipeline_question(self):
        """Test planning for pipeline question"""
        agent = Agent(Mock(spec=MondayClient))
        plan = agent.plan_query("How's our pipeline looking?")
        
        assert "Deals" in plan.get("boards_needed", [])
        assert not plan.get("needs_clarification", False)
    
    def test_plan_query_work_order_question(self):
        """Test planning for work order question"""
        agent = Agent(Mock(spec=MondayClient))
        plan = agent.plan_query("Which work orders are delayed?")
        
        assert "WorkOrders" in plan.get("boards_needed", [])
    
    def test_plan_query_sector_comparison(self):
        """Test planning for sector comparison"""
        agent = Agent(Mock(spec=MondayClient))
        plan = agent.plan_query("Compare energy and mining sectors")
        
        assert "by_sector" in plan.get("metrics", [])
    
    def test_plan_query_count_metrics(self):
        """Test planning for count-based questions"""
        agent = Agent(Mock(spec=MondayClient))
        plan = agent.plan_query("How many active projects do we have?")
        
        assert "counts" in plan.get("metrics", []) or "active" in plan.get("metrics", [])


class TestDataFetching:
    """Test data fetching and normalization"""
    
    @patch.object(MondayClient, "get_board_items")
    @patch.object(MondayClient, "get_board_columns")
    @patch("app.agent.Config.DEALS_BOARD_ID", "board123")
    def test_fetch_deals_success(self, mock_columns, mock_items):
        """Test successful deals fetch"""
        mock_items.return_value = [
            {
                "id": "item1",
                "name": "Test Deal",
                "created_at": "2026-01-01",
                "column_values": [
                    {"id": "col1", "text": "Mining"},
                    {"id": "col2", "text": "1000"},
                ],
            }
        ]
        
        mock_columns.return_value = [
            {"id": "col1", "title": "Sector/service"},
            {"id": "col2", "title": "Masked Deal value"},
        ]
        
        mock_client = Mock(spec=MondayClient)
        mock_client.get_board_items = mock_items
        mock_client.get_board_columns = mock_columns
        
        agent = Agent(mock_client)
        deals, issues = agent.fetch_and_normalize_deals()
        
        assert len(deals) == 1
        assert deals[0]["sector"] == "Mining"
    
    @patch.object(MondayClient, "get_board_items")
    @patch("app.agent.Config.DEALS_BOARD_ID", "")
    def test_fetch_deals_no_board_id(self, mock_items):
        """Test with missing board ID"""
        mock_client = Mock(spec=MondayClient)
        mock_client.get_board_items = mock_items
        
        agent = Agent(mock_client)
        deals, issues = agent.fetch_and_normalize_deals()
        
        assert deals == []
        assert any("not configured" in issue.lower() for issue in issues)
    
    @patch.object(MondayClient, "get_board_items")
    @patch("app.agent.Config.DEALS_BOARD_ID", "board123")
    def test_fetch_deals_cache(self, mock_items):
        """Test caching of deals"""
        mock_items.return_value = [
            {
                "id": "item1",
                "name": "Deal",
                "created_at": "2026-01-01",
                "column_values": [],
            }
        ]
        
        mock_client = Mock(spec=MondayClient)
        mock_client.get_board_items = mock_items
        mock_client.get_board_columns = Mock(return_value=[])
        
        agent = Agent(mock_client)
        
        # First call
        deals1, issues1 = agent.fetch_and_normalize_deals()
        call_count_1 = mock_items.call_count
        
        # Second call (should use cache)
        deals2, issues2 = agent.fetch_and_normalize_deals()
        call_count_2 = mock_items.call_count
        
        assert deals1 == deals2
        assert call_count_1 == call_count_2  # No additional calls
    
    @patch.object(MondayClient, "get_board_items")
    @patch("app.agent.Config.DEALS_BOARD_ID", "board123")
    def test_fetch_deals_force_refresh(self, mock_items):
        """Test force refresh bypasses cache"""
        mock_items.return_value = [
            {
                "id": "item1",
                "name": "Deal",
                "created_at": "2026-01-01",
                "column_values": [],
            }
        ]
        
        mock_client = Mock(spec=MondayClient)
        mock_client.get_board_items = mock_items
        mock_client.get_board_columns = Mock(return_value=[])
        
        agent = Agent(mock_client)
        
        # First call
        agent.fetch_and_normalize_deals()
        call_count_1 = mock_items.call_count
        
        # Second call with force_refresh
        agent.fetch_and_normalize_deals(force_refresh=True)
        call_count_2 = mock_items.call_count
        
        assert call_count_2 > call_count_1


class TestMetricInference:
    """Test metric inference from questions"""
    
    def test_infer_total_metrics(self):
        """Test inference of total metrics"""
        agent = Agent(Mock(spec=MondayClient))
        metrics = agent._infer_metrics("What is our total pipeline?")
        
        assert "total_value" in metrics
    
    def test_infer_sector_metrics(self):
        """Test inference of sector metrics"""
        agent = Agent(Mock(spec=MondayClient))
        metrics = agent._infer_metrics("Pipeline by sector?")
        
        assert "by_sector" in metrics
    
    def test_infer_active_metrics(self):
        """Test inference of active metrics"""
        agent = Agent(Mock(spec=MondayClient))
        metrics = agent._infer_metrics("How many active deals?")
        
        assert "active" in metrics or "counts" in metrics
    
    def test_infer_average_metrics(self):
        """Test inference of average metrics"""
        agent = Agent(Mock(spec=MondayClient))
        metrics = agent._infer_metrics("What's the average deal size?")
        
        assert "averages" in metrics


class TestAnalysis:
    """Test analysis execution"""
    
    def test_analyze_pipeline(self):
        """Test pipeline analysis"""
        agent = Agent(Mock(spec=MondayClient))
        
        results = {
            "deals": [
                {"deal_value": 10000, "deal_status": "Open", "sector": "Mining"},
                {"deal_value": 5000, "deal_status": "Closed", "sector": "Energy"},
            ],
            "work_orders": [],
        }
        
        analysis = agent._analyze("pipeline", results, ["total_value"])
        
        assert "pipeline_total" in analysis
        assert analysis["pipeline_total"]["value"] == 15000.0
        assert analysis["pipeline_total"]["count"] == 2


class TestResponseFormatting:
    """Test response formatting"""
    
    def test_format_pipeline_response(self):
        """Test pipeline response formatting"""
        agent = Agent(Mock(spec=MondayClient))
        
        analysis = {
            "pipeline_total": {"value": 15000.0, "count": 2},
            "active_pipeline": {"value": 10000.0, "count": 1},
        }
        
        response = agent._format_response("What's our pipeline?", analysis)
        
        assert "15000" in response or "15,000" in response
        assert "2 deals" in response or "2" in response
    
    def test_format_sector_response(self):
        """Test sector response formatting"""
        agent = Agent(Mock(spec=MondayClient))
        
        analysis = {
            "pipeline_by_sector": {
                "Mining": (10000.0, 1),
                "Energy": (5000.0, 1),
            }
        }
        
        response = agent._format_response("Pipeline by sector?", analysis)
        
        assert "Mining" in response
        assert "Energy" in response


class TestLeadershipSummary:
    """Test leadership summary generation"""
    
    @patch.object(MondayClient, "get_board_items")
    @patch.object(MondayClient, "get_board_columns")
    @patch("app.agent.Config.DEALS_BOARD_ID", "board123")
    @patch("app.agent.Config.WORK_ORDERS_BOARD_ID", "board456")
    def test_generate_leadership_summary(self, mock_wo_cols, mock_wo_items):
        """Test leadership summary generation"""
        mock_wo_items.return_value = []
        mock_wo_cols.return_value = []

        mock_client = Mock(spec=MondayClient)
        mock_client.get_board_items = Mock(return_value=[])
        mock_client.get_board_columns = Mock(return_value=[])

        agent = Agent(mock_client)
        result = agent.generate_leadership_summary()

        assert result["success"] is True
        assert "summary" in result
        assert "timestamp" in result
