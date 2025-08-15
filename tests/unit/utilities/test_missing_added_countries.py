import pytest
from sspi_flask_app.api.resources.utilities import missing_countries, added_countries


class TestMissingCountries:
    """Test suite for missing_countries function."""
    
    def test_missing_countries_basic_functionality(self):
        """Test basic functionality of missing_countries."""
        
        sspi_list = ['USA', 'CAN', 'GBR', 'FRA']
        source_list = ['USA', 'GBR', 'DEU']
        
        result = missing_countries(sspi_list, source_list)
        
        expected = ['CAN', 'FRA']  # Countries in SSPI but not in source
        assert result == expected
    
    def test_missing_countries_no_missing(self):
        """Test when no countries are missing."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['USA', 'CAN', 'GBR', 'FRA', 'DEU']
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_missing_countries_all_missing(self):
        """Test when all SSPI countries are missing from source."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['FRA', 'DEU', 'ITA']
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == ['USA', 'CAN', 'GBR']
    
    def test_missing_countries_empty_sspi_list(self):
        """Test with empty SSPI list."""
        
        sspi_list = []
        source_list = ['USA', 'CAN', 'GBR']
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_missing_countries_empty_source_list(self):
        """Test with empty source list."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = []
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == ['USA', 'CAN', 'GBR']  # All SSPI countries are missing
    
    def test_missing_countries_both_empty(self):
        """Test with both lists empty."""
        
        sspi_list = []
        source_list = []
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_missing_countries_identical_lists(self):
        """Test with identical lists."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['USA', 'CAN', 'GBR']
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_missing_countries_order_independence(self):
        """Test that order doesn't matter."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['GBR', 'USA']  # Different order, missing CAN
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == ['CAN']
    
    def test_missing_countries_duplicate_handling(self):
        """Test behavior with duplicate entries."""
        
        sspi_list = ['USA', 'CAN', 'USA', 'GBR']  # USA appears twice
        source_list = ['USA', 'FRA']
        
        result = missing_countries(sspi_list, source_list)
        
        # Should include each missing country once per occurrence in SSPI list
        assert result == ['CAN', 'GBR']
    
    def test_missing_countries_case_sensitivity(self):
        """Test case sensitivity."""
        
        sspi_list = ['USA', 'can', 'GBR']
        source_list = ['USA', 'CAN', 'GBR']  # 'can' != 'CAN'
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == ['can']  # Lowercase 'can' not found in source
    
    def test_missing_countries_numeric_codes(self):
        """Test with numeric country codes."""
        
        sspi_list = [840, 124, 826]  # USA, CAN, GBR
        source_list = [840, 826, 276]  # USA, GBR, DEU
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == [124]  # CAN missing
    
    def test_missing_countries_mixed_types(self):
        """Test with mixed data types."""
        
        sspi_list = ['USA', 124, 'GBR']
        source_list = ['USA', 'GBR', 124]
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == []  # All found despite mixed types
    
    def test_missing_countries_preserves_order(self):
        """Test that order of missing countries matches SSPI list order."""
        
        sspi_list = ['ZZZ', 'AAA', 'MMM', 'BBB']
        source_list = ['AAA']
        
        result = missing_countries(sspi_list, source_list)
        
        # Should preserve order from SSPI list
        assert result == ['ZZZ', 'MMM', 'BBB']
    
    def test_missing_countries_with_none_values(self):
        """Test behavior with None values."""
        
        sspi_list = ['USA', None, 'GBR']
        source_list = ['USA', 'CAN', 'GBR']
        
        result = missing_countries(sspi_list, source_list)
        
        assert result == [None]  # None not found in source
    
    def test_missing_countries_realistic_scenario(self):
        """Test with realistic SSPI country scenario."""
        
        # Sample of SSPI67 countries
        sspi_list = ['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'JPN', 'AUS', 'NOR', 'SWE', 'DNK']
        
        # Source missing some countries
        source_list = ['USA', 'CAN', 'FRA', 'DEU', 'JPN', 'ITA', 'ESP', 'NLD']
        
        result = missing_countries(sspi_list, source_list)
        
        expected_missing = ['GBR', 'AUS', 'NOR', 'SWE', 'DNK']
        assert result == expected_missing


class TestAddedCountries:
    """Test suite for added_countries function."""
    
    def test_added_countries_basic_functionality(self):
        """Test basic functionality of added_countries."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['USA', 'CAN', 'GBR', 'FRA', 'DEU']
        
        result = added_countries(sspi_list, source_list)
        
        expected = ['FRA', 'DEU']  # Countries in source but not in SSPI
        assert result == expected
    
    def test_added_countries_no_additions(self):
        """Test when no countries are added."""
        
        sspi_list = ['USA', 'CAN', 'GBR', 'FRA']
        source_list = ['USA', 'CAN', 'GBR']
        
        result = added_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_added_countries_all_added(self):
        """Test when all source countries are additions."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['FRA', 'DEU', 'ITA']
        
        result = added_countries(sspi_list, source_list)
        
        assert result == ['FRA', 'DEU', 'ITA']
    
    def test_added_countries_empty_sspi_list(self):
        """Test with empty SSPI list."""
        
        sspi_list = []
        source_list = ['USA', 'CAN', 'GBR']
        
        result = added_countries(sspi_list, source_list)
        
        assert result == ['USA', 'CAN', 'GBR']  # All source countries are additions
    
    def test_added_countries_empty_source_list(self):
        """Test with empty source list."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = []
        
        result = added_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_added_countries_both_empty(self):
        """Test with both lists empty."""
        
        sspi_list = []
        source_list = []
        
        result = added_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_added_countries_identical_lists(self):
        """Test with identical lists."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['USA', 'CAN', 'GBR']
        
        result = added_countries(sspi_list, source_list)
        
        assert result == []
    
    def test_added_countries_order_independence(self):
        """Test that order doesn't matter for membership."""
        
        sspi_list = ['USA', 'GBR']
        source_list = ['GBR', 'CAN', 'USA']  # Different order, CAN is addition
        
        result = added_countries(sspi_list, source_list)
        
        assert result == ['CAN']
    
    def test_added_countries_preserves_source_order(self):
        """Test that order of added countries matches source list order."""
        
        sspi_list = ['AAA']
        source_list = ['ZZZ', 'AAA', 'MMM', 'BBB']
        
        result = added_countries(sspi_list, source_list)
        
        # Should preserve order from source list
        assert result == ['ZZZ', 'MMM', 'BBB']
    
    def test_added_countries_duplicate_handling(self):
        """Test behavior with duplicate entries."""
        
        sspi_list = ['USA', 'CAN']
        source_list = ['USA', 'FRA', 'FRA', 'DEU']  # FRA appears twice
        
        result = added_countries(sspi_list, source_list)
        
        # Should include each addition once per occurrence in source list
        assert result == ['FRA', 'FRA', 'DEU']
    
    def test_added_countries_case_sensitivity(self):
        """Test case sensitivity."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['USA', 'can', 'GBR']  # 'can' != 'CAN'
        
        result = added_countries(sspi_list, source_list)
        
        assert result == ['can']  # Lowercase 'can' is an addition
    
    def test_added_countries_numeric_codes(self):
        """Test with numeric country codes."""
        
        sspi_list = [840, 124]  # USA, CAN
        source_list = [840, 124, 276, 826]  # USA, CAN, DEU, GBR
        
        result = added_countries(sspi_list, source_list)
        
        assert result == [276, 826]  # DEU, GBR are additions
    
    def test_added_countries_mixed_types(self):
        """Test with mixed data types."""
        
        sspi_list = ['USA', 124]
        source_list = ['USA', 124, 'GBR', 276]
        
        result = added_countries(sspi_list, source_list)
        
        assert result == ['GBR', 276]  # New additions
    
    def test_added_countries_with_none_values(self):
        """Test behavior with None values."""
        
        sspi_list = ['USA', 'CAN']
        source_list = ['USA', None, 'GBR']
        
        result = added_countries(sspi_list, source_list)
        
        assert result == [None, 'GBR']  # None and GBR are additions
    
    def test_added_countries_realistic_scenario(self):
        """Test with realistic data source scenario."""
        
        # SSPI67 subset
        sspi_list = ['USA', 'CAN', 'GBR', 'FRA', 'DEU']
        
        # Data source with additional countries
        source_list = ['USA', 'CAN', 'GBR', 'FRA', 'DEU', 'ITA', 'ESP', 'PRT', 'GRC', 'BEL']
        
        result = added_countries(sspi_list, source_list)
        
        expected_additions = ['ITA', 'ESP', 'PRT', 'GRC', 'BEL']
        assert result == expected_additions


class TestCountryListComparison:
    """Test the two functions working together."""
    
    def test_complementary_behavior(self):
        """Test that missing_countries and added_countries are complementary."""
        
        sspi_list = ['USA', 'CAN', 'GBR', 'FRA']
        source_list = ['CAN', 'GBR', 'DEU', 'ITA']
        
        missing = missing_countries(sspi_list, source_list)
        added = added_countries(sspi_list, source_list)
        
        assert missing == ['USA', 'FRA']  # In SSPI but not source
        assert added == ['DEU', 'ITA']    # In source but not SSPI
        
        # Verify no overlap
        assert set(missing).isdisjoint(set(added))
    
    def test_union_covers_all_unique_countries(self):
        """Test that union of intersection, missing, and added covers all unique countries."""
        
        sspi_list = ['USA', 'CAN', 'GBR']
        source_list = ['GBR', 'FRA', 'DEU']
        
        missing = missing_countries(sspi_list, source_list)
        added = added_countries(sspi_list, source_list)
        intersection = [c for c in sspi_list if c in source_list]
        
        assert intersection == ['GBR']
        assert missing == ['USA', 'CAN']
        assert added == ['FRA', 'DEU']
        
        # Union should cover all unique countries
        all_countries = set(sspi_list + source_list)
        covered_countries = set(intersection + missing + added)
        assert all_countries == covered_countries
    
    def test_symmetric_difference(self):
        """Test symmetric difference behavior."""
        
        sspi_list = ['A', 'B', 'C']
        source_list = ['B', 'C', 'D']
        
        missing = missing_countries(sspi_list, source_list)
        added = added_countries(sspi_list, source_list)
        
        assert missing == ['A']
        assert added == ['D']
        
        # Symmetric difference should be union of missing and added
        symmetric_diff = set(missing + added)
        expected_symmetric_diff = set(sspi_list).symmetric_difference(set(source_list))
        assert symmetric_diff == expected_symmetric_diff
    
    def test_empty_lists_behavior(self):
        """Test behavior when one or both lists are empty."""
        
        # Empty SSPI, non-empty source
        missing1 = missing_countries([], ['A', 'B'])
        added1 = added_countries([], ['A', 'B'])
        assert missing1 == []
        assert added1 == ['A', 'B']
        
        # Non-empty SSPI, empty source
        missing2 = missing_countries(['A', 'B'], [])
        added2 = added_countries(['A', 'B'], [])
        assert missing2 == ['A', 'B']
        assert added2 == []
        
        # Both empty
        missing3 = missing_countries([], [])
        added3 = added_countries([], [])
        assert missing3 == []
        assert added3 == []
    
    def test_performance_with_large_lists(self):
        """Test performance with larger lists."""
        
        # Create larger lists
        sspi_list = [f'SSPI_{i}' for i in range(100)]
        source_list = [f'SRC_{i}' for i in range(150)]
        
        # Functions should complete without error
        missing = missing_countries(sspi_list, source_list)
        added = added_countries(sspi_list, source_list)
        
        # All SSPI countries should be missing (no overlap)
        assert len(missing) == 100
        assert missing == sspi_list
        
        # All source countries should be added
        assert len(added) == 150
        assert added == source_list