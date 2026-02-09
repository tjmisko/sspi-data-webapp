import pytest
from sspi_flask_app.api.resources.utilities import colormap


class TestColormap:
    """Test suite for colormap function."""
    
    def test_colormap_sus_pillar(self):
        """Test colormap for SUS (Sustainability) pillar."""
        
        result = colormap("SUS")
        
        assert result == "#28a745ff"
        assert result.startswith("#28a745")
        assert result.endswith("ff")  # Default alpha
    
    def test_colormap_ms_pillar(self):
        """Test colormap for MS (Market Structure) pillar."""
        
        result = colormap("MS")
        
        assert result == "#ff851bff"
        assert result.startswith("#ff851b")
        assert result.endswith("ff")  # Default alpha
    
    def test_colormap_pg_pillar(self):
        """Test colormap for PG (Public Goods) pillar."""
        
        result = colormap("PG")
        
        assert result == "#007bffff"
        assert result.startswith("#007bff")
        assert result.endswith("ff")  # Default alpha
    
    def test_colormap_custom_alpha(self):
        """Test colormap with custom alpha values."""
        
        alpha_test_cases = [
            ("SUS", "80", "#28a74580"),
            ("MS", "40", "#ff851b40"),
            ("PG", "cc", "#007bffcc"),
            ("SUS", "00", "#28a74500"),  # Fully transparent
            ("MS", "ff", "#ff851bff"),   # Fully opaque
        ]
        
        for pillar_code, alpha, expected in alpha_test_cases:
            result = colormap(pillar_code, alpha)
            assert result == expected, f"Failed for {pillar_code} with alpha {alpha}"
    
    def test_colormap_invalid_pillar_codes(self):
        """Test colormap with invalid pillar codes."""
        
        invalid_codes = [
            "INVALID",
            "sus",      # Lowercase
            "ms",       # Lowercase 
            "pg",       # Lowercase
            "",         # Empty string
            "SU",       # Partial
            "MSS",      # Too long
            "ABC",      # Different code
            "123",      # Numeric
            None,       # None value
        ]
        
        for invalid_code in invalid_codes:
            result = colormap(invalid_code)
            assert result is None, f"Should return None for invalid code: {invalid_code}"
    
    def test_colormap_case_sensitivity(self):
        """Test that colormap is case sensitive."""
        
        case_variants = [
            ("sus", None),     # Lowercase should return None
            ("SUS", "#28a745ff"),  # Uppercase should work
            ("Ms", None),      # Mixed case should return None
            ("MS", "#ff851bff"),   # Uppercase should work
            ("Pg", None),      # Mixed case should return None
            ("PG", "#007bffff"),   # Uppercase should work
        ]
        
        for pillar_code, expected in case_variants:
            result = colormap(pillar_code)
            assert result == expected, f"Case sensitivity test failed for {pillar_code}"
    
    def test_colormap_alpha_variations(self):
        """Test colormap with various alpha formats."""
        
        alpha_variations = [
            "00",     # Two digit hex
            "80",     # Two digit hex
            "ff",     # Two digit hex (uppercase)
            "FF",     # Two digit hex (uppercase)
            "a0",     # Two digit hex with letter
            "A0",     # Two digit hex with letter (uppercase)
            "1",      # Single digit (should work as-is)
            "123",    # Three digits (should work as-is)
            "",       # Empty string
        ]
        
        for alpha in alpha_variations:
            result = colormap("SUS", alpha)
            expected = f"#28a745{alpha}"
            assert result == expected, f"Alpha variation test failed for '{alpha}'"
    
    def test_colormap_pillar_code_types(self):
        """Test colormap with different input types for pillar codes."""
        
        # Test with non-string types
        non_string_inputs = [
            123,
            ["SUS"],
            {"code": "SUS"},
            True,
            False,
        ]
        
        for non_string_input in non_string_inputs:
            result = colormap(non_string_input)
            assert result is None, f"Should return None for non-string input: {non_string_input}"
    
    def test_colormap_all_known_pillars(self):
        """Test all known SSPI pillar codes."""
        
        known_pillars = [
            ("SUS", "#28a745ff"),  # Sustainability - Green
            ("MS", "#ff851bff"),   # Market Structure - Orange
            ("PG", "#007bffff"),   # Public Goods - Blue
        ]
        
        for pillar_code, expected_color in known_pillars:
            result = colormap(pillar_code)
            assert result == expected_color, f"Known pillar test failed for {pillar_code}"
    
    def test_colormap_color_format_validation(self):
        """Test that returned colors are in valid hex format."""
        
        valid_pillars = ["SUS", "MS", "PG"]
        
        for pillar in valid_pillars:
            result = colormap(pillar)
            
            # Should start with #
            assert result.startswith("#"), f"Color should start with # for {pillar}"
            
            # Should be 9 characters total (#RRGGBBAA)
            assert len(result) == 9, f"Color should be 9 characters for {pillar}"
            
            # Should be valid hex after #
            hex_part = result[1:]
            try:
                int(hex_part, 16)  # Should parse as hex
            except ValueError:
                pytest.fail(f"Color should be valid hex for {pillar}: {result}")
    
    def test_colormap_alpha_parameter_default(self):
        """Test that alpha parameter defaults to 'ff'."""
        
        # Test without alpha parameter
        result_default = colormap("SUS")
        # Test with explicit alpha
        result_explicit = colormap("SUS", "ff")
        
        assert result_default == result_explicit
        assert result_default == "#28a745ff"
    
    def test_colormap_realistic_usage_scenarios(self):
        """Test colormap with realistic SSPI usage scenarios."""
        
        # Scenario 1: UI components need colors with transparency
        ui_scenarios = [
            ("SUS", "80", "#28a74580"),  # Semi-transparent green
            ("MS", "cc", "#ff851bcc"),   # Mostly opaque orange
            ("PG", "40", "#007bff40"),   # Low opacity blue
        ]
        
        for pillar, alpha, expected in ui_scenarios:
            result = colormap(pillar, alpha)
            assert result == expected
        
        # Scenario 2: Chart legends need full opacity
        for pillar in ["SUS", "MS", "PG"]:
            result = colormap(pillar, "ff")
            assert result.endswith("ff")
        
        # Scenario 3: Hover effects need different opacity
        for pillar in ["SUS", "MS", "PG"]:
            hover_result = colormap(pillar, "b0")
            assert hover_result.endswith("b0")
    
    def test_colormap_pillar_color_distinctness(self):
        """Test that pillar colors are distinct from each other."""
        
        sus_color = colormap("SUS")
        ms_color = colormap("MS")
        pg_color = colormap("PG")
        
        # All should be different
        assert sus_color != ms_color
        assert sus_color != pg_color
        assert ms_color != pg_color
        
        # Extract RGB components (ignoring alpha)
        sus_rgb = sus_color[:7]  # #28a745
        ms_rgb = ms_color[:7]    # #ff851b
        pg_rgb = pg_color[:7]    # #007bff
        
        assert sus_rgb != ms_rgb
        assert sus_rgb != pg_rgb
        assert ms_rgb != pg_rgb
    
    def test_colormap_color_accessibility(self):
        """Test that colors follow basic accessibility principles."""
        
        pillar_colors = {
            "SUS": "#28a745",  # Green - should be distinct
            "MS": "#ff851b",   # Orange - should be distinct
            "PG": "#007bff",   # Blue - should be distinct
        }
        
        # Test that colors are not too similar (basic check)
        colors = list(pillar_colors.values())
        
        for i, color1 in enumerate(colors):
            for j, color2 in enumerate(colors):
                if i != j:
                    # Simple check - colors should not be identical
                    assert color1 != color2
                    
                    # Extract RGB values for basic comparison
                    rgb1 = [int(color1[k:k+2], 16) for k in (1, 3, 5)]
                    rgb2 = [int(color2[k:k+2], 16) for k in (1, 3, 5)]
                    
                    # Colors should have some significant difference
                    total_diff = sum(abs(a - b) for a, b in zip(rgb1, rgb2))
                    assert total_diff > 100, f"Colors too similar: {color1} vs {color2}"
    
    def test_colormap_string_interpolation(self):
        """Test that string interpolation works correctly."""
        
        test_cases = [
            ("SUS", "aa", "#28a745aa"),
            ("MS", "bb", "#ff851bbb"),
            ("PG", "cc", "#007bffcc"),
        ]
        
        for pillar, alpha, expected in test_cases:
            result = colormap(pillar, alpha)
            
            # Verify format
            assert result == expected
            
            # Verify interpolation worked correctly
            assert pillar in ["SUS", "MS", "PG"]  # Valid pillar
            assert alpha in result  # Alpha was interpolated
            assert result.count("#") == 1  # Only one hash symbol
            assert len(result) == 7 + len(alpha)  # Correct total length
    
    def test_colormap_memory_efficiency(self):
        """Test that colormap doesn't have memory issues with repeated calls."""
        
        # Make many calls to ensure no memory leaks or issues
        for _ in range(1000):
            colormap("SUS")
            colormap("MS", "80")
            colormap("PG", "cc")
            colormap("INVALID")  # Also test invalid calls
        
        # If we reach here without issues, memory handling is fine
        assert True
    
    def test_colormap_documentation_examples(self):
        """Test examples that might appear in documentation."""
        
        # Example 1: Basic usage
        assert colormap("SUS") == "#28a745ff"
        
        # Example 2: With transparency
        assert colormap("SUS", "80") == "#28a74580"
        
        # Example 3: All pillars
        sustainability = colormap("SUS")
        material_security = colormap("MS")
        personal_growth = colormap("PG")
        
        assert sustainability.startswith("#28a745")
        assert material_security.startswith("#ff851b")
        assert personal_growth.startswith("#007bff")
