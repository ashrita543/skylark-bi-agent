"""
Test suite for data normalization
Tests all normalization functions with real-world messy data
"""
import pytest
from datetime import datetime, date
from app.normalizer import DataNormalizer


class TestStringNormalization:
    """Test string normalization"""
    
    def test_normalize_string_basic(self):
        """Test basic string normalization"""
        assert DataNormalizer.normalize_string("  hello  ") == "hello"
        assert DataNormalizer.normalize_string("WORLD") == "WORLD"
        assert DataNormalizer.normalize_string(None) is None
        assert DataNormalizer.normalize_string("") is None
        assert DataNormalizer.normalize_string("   ") is None
    
    def test_normalize_string_allows_empty(self):
        """Test allow_empty parameter"""
        assert DataNormalizer.normalize_string("", allow_empty=True) == ""
        assert DataNormalizer.normalize_string("   ", allow_empty=True) == ""
    
    def test_normalize_string_numeric_input(self):
        """Test with numeric input"""
        assert DataNormalizer.normalize_string(123) == "123"
        assert DataNormalizer.normalize_string(45.67) == "45.67"


class TestDateNormalization:
    """Test date normalization"""
    
    def test_normalize_date_datetime_object(self):
        """Test with datetime object"""
        dt = datetime(2026, 1, 15)
        result = DataNormalizer.normalize_date(dt)
        assert result == dt
    
    def test_normalize_date_iso_format(self):
        """Test ISO format dates"""
        result = DataNormalizer.normalize_date("2026-01-15")
        assert result == datetime(2026, 1, 15)
    
    def test_normalize_date_us_format(self):
        """Test US format dates"""
        result = DataNormalizer.normalize_date("01/15/2026")
        assert result == datetime(2026, 1, 15)
    
    def test_normalize_date_uk_format(self):
        """Test UK format dates"""
        result = DataNormalizer.normalize_date("15/01/2026")
        assert result == datetime(2026, 1, 15)
    
    def test_normalize_date_short_format(self):
        """Test short date format"""
        result = DataNormalizer.normalize_date("15-Jan-26")
        assert result == datetime(2026, 1, 15)
    
    def test_normalize_date_long_format(self):
        """Test long format"""
        result = DataNormalizer.normalize_date("January 15, 2026")
        assert result == datetime(2026, 1, 15)
    
    def test_normalize_date_invalid(self):
        """Test invalid date"""
        assert DataNormalizer.normalize_date("not-a-date") is None
        assert DataNormalizer.normalize_date("") is None
        assert DataNormalizer.normalize_date(None) is None
        assert DataNormalizer.normalize_date("N/A") is None


class TestNumericNormalization:
    """Test numeric value normalization"""
    
    def test_normalize_numeric_basic(self):
        """Test basic numeric normalization"""
        assert DataNormalizer.normalize_numeric(123) == 123.0
        assert DataNormalizer.normalize_numeric(45.67) == 45.67
        assert DataNormalizer.normalize_numeric("123") == 123.0
    
    def test_normalize_numeric_currency(self):
        """Test currency symbols"""
        assert DataNormalizer.normalize_numeric("$1,000") == 1000.0
        assert DataNormalizer.normalize_numeric("₹50,000") == 50000.0
        assert DataNormalizer.normalize_numeric("€100") == 100.0
    
    def test_normalize_numeric_commas(self):
        """Test comma separators"""
        assert DataNormalizer.normalize_numeric("1,000,000") == 1000000.0
        assert DataNormalizer.normalize_numeric("1000") == 1000.0
    
    def test_normalize_numeric_suffixes(self):
        """Test numeric suffixes (K, M, B)"""
        assert DataNormalizer.normalize_numeric("1K") == 1000.0
        assert DataNormalizer.normalize_numeric("1.5M") == 1500000.0
        assert DataNormalizer.normalize_numeric("2B") == 2000000000.0
    
    def test_normalize_numeric_invalid(self):
        """Test invalid numeric values"""
        assert DataNormalizer.normalize_numeric("not-a-number") is None
        assert DataNormalizer.normalize_numeric(None) is None
        assert DataNormalizer.normalize_numeric("") is None


class TestSectorNormalization:
    """Test sector normalization"""
    
    def test_normalize_sector_basic(self):
        """Test basic sector normalization"""
        assert DataNormalizer.normalize_sector("mining") == "Mining"
        assert DataNormalizer.normalize_sector("Mining") == "Mining"
        assert DataNormalizer.normalize_sector("MINING") == "Mining"
    
    def test_normalize_sector_variations(self):
        """Test sector name variations"""
        assert DataNormalizer.normalize_sector("powerline") == "Powerline"
        assert DataNormalizer.normalize_sector("Powerline") == "Powerline"
        assert DataNormalizer.normalize_sector("energy") == "Energy"
    
    def test_normalize_sector_unknown(self):
        """Test unknown sector"""
        assert DataNormalizer.normalize_sector("XYZ Sector") == "XYZ Sector"
    
    def test_normalize_sector_invalid(self):
        """Test invalid sectors"""
        assert DataNormalizer.normalize_sector(None) is None
        assert DataNormalizer.normalize_sector("") is None


class TestProbabilityNormalization:
    """Test probability normalization"""
    
    def test_normalize_probability_text(self):
        """Test text-based probability"""
        assert DataNormalizer.normalize_probability("High") == 0.8
        assert DataNormalizer.normalize_probability("Medium") == 0.5
        assert DataNormalizer.normalize_probability("Low") == 0.2
    
    def test_normalize_probability_numeric(self):
        """Test numeric probability"""
        assert DataNormalizer.normalize_probability("0.75") == 0.75
        assert DataNormalizer.normalize_probability("75%") == 0.75
        assert DataNormalizer.normalize_probability("75") == 0.75
    
    def test_normalize_probability_clamping(self):
        """Test probability clamping to 0-1"""
        assert DataNormalizer.normalize_probability("150") == 1.0
        assert DataNormalizer.normalize_probability("-0.5") == 0.0
    
    def test_normalize_probability_invalid(self):
        """Test invalid probability"""
        assert DataNormalizer.normalize_probability(None) is None
        assert DataNormalizer.normalize_probability("") is None


class TestStatusNormalization:
    """Test status normalization"""
    
    def test_normalize_deal_status(self):
        """Test deal status normalization"""
        assert DataNormalizer.normalize_deal_status("Open") == "Open"
        assert DataNormalizer.normalize_deal_status("open") == "Open"
        assert DataNormalizer.normalize_deal_status("On Hold") == "On Hold"
        assert DataNormalizer.normalize_deal_status("Won") == "Won"
    
    def test_normalize_execution_status(self):
        """Test execution status normalization"""
        assert DataNormalizer.normalize_execution_status("Completed") == "Completed"
        assert DataNormalizer.normalize_execution_status("completed") == "Completed"
        assert DataNormalizer.normalize_execution_status("In Progress") == "In Progress"
        assert DataNormalizer.normalize_execution_status("Not Started") == "Not Started"


class TestRecordCreation:
    """Test record creation from Monday.com items"""
    
    def test_create_record_from_items_empty(self):
        """Test with empty items"""
        records = DataNormalizer.create_record_from_items([], {})
        assert records == []
    
    def test_create_record_from_items_basic(self):
        """Test basic record creation"""
        items = [
            {
                "id": "123",
                "name": "Test Deal",
                "created_at": datetime(2026, 1, 1),
                "column_values": [],
            }
        ]
        records = DataNormalizer.create_record_from_items(items, {})
        assert len(records) == 1
        assert records[0]["id"] == "123"
        assert records[0]["name"] == "Test Deal"
    
    def test_create_record_from_items_with_mapping(self):
        """Test record creation with column mapping"""
        items = [
            {
                "id": "123",
                "name": "Test",
                "created_at": datetime(2026, 1, 1),
                "column_values": [
                    {"id": "col1", "text": "Value 1", "value": "val1", "type": "text"}
                ],
            }
        ]
        mapping = {"col1": "field1"}
        records = DataNormalizer.create_record_from_items(items, mapping)
        assert records[0]["field1"] == "Value 1"


class TestDataQualityReport:
    """Test data quality reporting"""
    
    def test_quality_report_empty(self):
        """Test with empty records"""
        report = DataNormalizer.get_data_quality_report([])
        assert report["total_records"] == 0
        assert "No records found" in report["issues"]
    
    def test_quality_report_complete(self):
        """Test with complete records"""
        records = [
            {"id": "1", "name": "Deal 1", "value": 1000},
            {"id": "2", "name": "Deal 2", "value": 2000},
        ]
        report = DataNormalizer.get_data_quality_report(records)
        assert report["total_records"] == 2
        assert len(report["missing_by_field"]) == 0
    
    def test_quality_report_missing_values(self):
        """Test with missing values"""
        records = [
            {"id": "1", "name": "Deal 1", "value": 1000},
            {"id": "2", "name": None, "value": None},
        ]
        report = DataNormalizer.get_data_quality_report(records)
        assert report["total_records"] == 2
        assert "name" in report["missing_by_field"]
        assert report["missing_by_field"]["name"]["count"] == 1
