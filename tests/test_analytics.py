"""
Test suite for analytics module
Tests all business calculations and metrics
"""
import pytest
from datetime import datetime, date, timedelta
from app.analytics import Analytics


class TestQuarterCalculations:
    """Test quarter-related calculations"""
    
    def test_get_quarter_date_range_q1(self):
        """Test Q1 date range"""
        start, end = Analytics.get_quarter_date_range(2026, 1)
        assert start == date(2026, 1, 1)
    
    def test_get_quarter_date_range_q4(self):
        """Test Q4 date range"""
        start, end = Analytics.get_quarter_date_range(2026, 4)
        assert start == date(2026, 10, 1)


class TestPipelineCalculations:
    """Test pipeline value calculations"""
    
    def test_calculate_total_pipeline_empty(self):
        """Test with no deals"""
        total, count = Analytics.calculate_total_pipeline([])
        assert total == 0.0
        assert count == 0
    
    def test_calculate_total_pipeline_basic(self):
        """Test basic pipeline calculation"""
        deals = [
            {"deal_value": 1000},
            {"deal_value": 2000},
            {"deal_value": None},
        ]
        total, count = Analytics.calculate_total_pipeline(deals)
        assert total == 3000.0
        assert count == 2
    
    def test_calculate_active_pipeline(self):
        """Test active pipeline calculation"""
        deals = [
            {"deal_status": "Open", "deal_value": 1000},
            {"deal_status": "On Hold", "deal_value": 2000},
            {"deal_status": "Closed", "deal_value": 3000},
            {"deal_value": 500},  # Unknown status, should include
        ]
        total, count = Analytics.calculate_active_pipeline(deals)
        assert total == 3500.0  # Open + On Hold + Unknown
        assert count == 3
    
    def test_calculate_average_deal_size(self):
        """Test average deal size"""
        deals = [
            {"deal_value": 1000},
            {"deal_value": 2000},
            {"deal_value": 3000},
        ]
        avg = Analytics.calculate_average_deal_size(deals)
        assert avg == 2000.0
    
    def test_calculate_average_deal_size_no_deals(self):
        """Test average with no deals"""
        avg = Analytics.calculate_average_deal_size([])
        assert avg is None


class TestPipelineByDimension:
    """Test pipeline breakdown by dimensions"""
    
    def test_pipeline_by_sector(self):
        """Test pipeline grouped by sector"""
        deals = [
            {"sector": "Mining", "deal_value": 1000},
            {"sector": "Mining", "deal_value": 2000},
            {"sector": "Energy", "deal_value": 1500},
            {"sector": None, "deal_value": 500},
        ]
        by_sector = Analytics.pipeline_by_sector(deals)
        
        assert by_sector["Mining"] == (3000.0, 2)
        assert by_sector["Energy"] == (1500.0, 1)
        assert by_sector["Unknown"] == (500.0, 1)
    
    def test_pipeline_by_stage(self):
        """Test pipeline grouped by stage"""
        deals = [
            {"deal_stage": "Proposal", "deal_value": 1000},
            {"deal_stage": "Proposal", "deal_value": 2000},
            {"deal_stage": "Negotiation", "deal_value": 1500},
        ]
        by_stage = Analytics.pipeline_by_stage(deals)
        
        assert by_stage["Proposal"] == (3000.0, 2)
        assert by_stage["Negotiation"] == (1500.0, 1)
    
    def test_weighted_pipeline(self):
        """Test weighted pipeline calculation"""
        deals = [
            {"deal_value": 1000, "probability": 1.0},  # 1000
            {"deal_value": 1000, "probability": 0.5},  # 500
            {"deal_value": 1000, "probability": None},  # Skip
            {"deal_value": None, "probability": 0.8},  # Skip
        ]
        weighted, count = Analytics.calculate_weighted_pipeline(deals)
        assert weighted == 1500.0
        assert count == 2


class TestDealCounting:
    """Test deal counting by status"""
    
    def test_count_deals_by_status(self):
        """Test deal status distribution"""
        deals = [
            {"deal_status": "Open"},
            {"deal_status": "Open"},
            {"deal_status": "On Hold"},
            {"deal_status": None},
        ]
        counts = Analytics.count_deals_by_status(deals)
        assert counts["Open"] == 2
        assert counts["On Hold"] == 1
        assert counts["Unknown"] == 1


class TestWorkOrderMetrics:
    """Test work order related calculations"""
    
    def test_count_work_orders_by_status(self):
        """Test work order status distribution"""
        wos = [
            {"execution_status": "Completed"},
            {"execution_status": "Completed"},
            {"execution_status": "In Progress"},
            {"execution_status": None},
        ]
        counts = Analytics.count_work_orders_by_status(wos)
        assert counts["Completed"] == 2
        assert counts["In Progress"] == 1
        assert counts["Unknown"] == 1
    
    def test_count_active_work_orders(self):
        """Test active work order counting"""
        wos = [
            {"execution_status": "In Progress"},
            {"execution_status": "Not Started"},
            {"execution_status": "On Hold"},
            {"execution_status": "Completed"},
        ]
        active = Analytics.count_active_work_orders(wos)
        assert active == 3
    
    def test_count_completed_work_orders(self):
        """Test completed work order counting"""
        wos = [
            {"execution_status": "Completed"},
            {"execution_status": "Completed"},
            {"execution_status": "In Progress"},
        ]
        completed = Analytics.count_completed_work_orders(wos)
        assert completed == 2
    
    def test_detect_delayed_work_orders(self):
        """Test delayed work order detection"""
        reference_date = datetime(2026, 1, 15)
        
        wos = [
            {
                "execution_status": "In Progress",
                "probable_end_date": datetime(2026, 1, 10),  # Past - delayed
            },
            {
                "execution_status": "In Progress",
                "probable_end_date": datetime(2026, 1, 20),  # Future - not delayed
            },
            {
                "execution_status": "Completed",
                "probable_end_date": datetime(2026, 1, 10),  # Completed - skip
            },
            {
                "execution_status": "In Progress",
                "probable_end_date": None,  # No end date - skip
            },
        ]
        
        delayed = Analytics.detect_delayed_work_orders(wos, reference_date)
        assert len(delayed) == 1
        assert delayed[0]["execution_status"] == "In Progress"
    
    def test_calculate_billed_value(self):
        """Test billed value calculation"""
        wos = [
            {"billed_value": 1000},
            {"billed_value": 2000},
            {"billed_value": None},
        ]
        total, count = Analytics.calculate_billed_value(wos)
        assert total == 3000.0
        assert count == 2
    
    def test_work_orders_by_sector(self):
        """Test work orders grouped by sector"""
        wos = [
            {"sector": "Mining"},
            {"sector": "Mining"},
            {"sector": "Energy"},
            {"sector": None},
        ]
        by_sector = Analytics.work_orders_by_sector(wos)
        assert by_sector["Mining"] == 2
        assert by_sector["Energy"] == 1
        assert by_sector["Unknown"] == 1


class TestLeadershipSummary:
    """Test leadership summary generation"""
    
    def test_generate_leadership_summary_empty(self):
        """Test summary with no data"""
        summary = Analytics.generate_leadership_summary([], [])
        
        assert summary["pipeline"]["total_value"] == 0.0
        assert summary["pipeline"]["total_count"] == 0
        assert summary["work_orders"]["active_count"] == 0
    
    def test_generate_leadership_summary_basic(self):
        """Test basic summary generation"""
        deals = [
            {
                "deal_value": 10000,
                "deal_status": "Open",
                "sector": "Mining",
                "probability": 0.8,
            },
            {
                "deal_value": 5000,
                "deal_status": "Closed",
                "sector": "Energy",
                "probability": None,
            },
        ]
        
        wos = [
            {"execution_status": "In Progress", "sector": "Mining", "billed_value": 1000},
            {"execution_status": "Completed", "sector": "Energy", "billed_value": 2000},
        ]
        
        summary = Analytics.generate_leadership_summary(deals, wos)
        
        assert summary["pipeline"]["total_value"] == 15000.0
        assert summary["pipeline"]["total_count"] == 2
        assert summary["pipeline"]["active_count"] == 10000.0  # Only Open
        assert summary["work_orders"]["active_count"] == 1
        assert summary["work_orders"]["completed_count"] == 1
        assert summary["work_orders"]["total_billed"] == 3000.0
    
    def test_generate_leadership_summary_with_issues(self):
        """Test summary includes data quality issues"""
        deals = [{"deal_value": None}]
        wos = [{"billed_value": None}]
        caveats = ["Some data missing"]
        
        summary = Analytics.generate_leadership_summary(deals, wos, caveats)
        assert "Some data missing" in summary["data_quality_caveats"]


class TestFilterByQuarter:
    """Test quarter-based filtering"""
    
    def test_filter_by_quarter_basic(self):
        """Test basic quarter filtering"""
        deals = [
            {"close_date": datetime(2026, 1, 15)},  # Q1
            {"close_date": datetime(2026, 4, 15)},  # Q2
            {"close_date": datetime(2026, 7, 15)},  # Q3
        ]
        
        q1_deals = Analytics.filter_by_quarter(deals, 2026, 1)
        assert len(q1_deals) == 1
    
    def test_filter_by_quarter_fallback_date(self):
        """Test fallback to tentative close date"""
        deals = [
            {"close_date": None, "tentative_close_date": datetime(2026, 1, 15)},
            {"close_date": None, "tentative_close_date": datetime(2026, 4, 15)},
        ]
        
        q1_deals = Analytics.filter_by_quarter(deals, 2026, 1)
        assert len(q1_deals) == 1
