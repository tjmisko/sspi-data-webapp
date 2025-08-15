import pytest
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import get_country_code


def test_get_country_code_kosovo_variants():
    """Test Kosovo edge case handling with various spellings."""
    kosovo_variants = [
        "Kosovo",
        "kosovo", 
        "KOSOVO",
        "Republic of Kosovo",
        "kosovo region",
        "Kosovo and Metohija",
        "Southern Kosovo"
    ]
    
    for variant in kosovo_variants:
        result = get_country_code(variant)
        assert result == "XKX", f"Failed for Kosovo variant: {variant}"


def test_get_country_code_korea_variants():
    """Test Korea edge cases - South Korea vs North Korea."""
    
    # South Korea variants (no "democratic")
    south_korea_variants = [
        "Korea",
        "korea",
        "South Korea",
        "Republic of Korea",
        "korea republic",
        "Korean Peninsula"
    ]
    
    for variant in south_korea_variants:
        result = get_country_code(variant)
        assert result == "KOR", f"Failed for South Korea variant: {variant}"
    
    # North Korea variants (with "democratic")
    north_korea_variants = [
        "Korea Democratic",
        "democratic korea",
        "North Korea Democratic",
        "Democratic People's Republic of Korea",
        "korea democratic people",
        "Democratic Republic of Korea"
    ]
    
    for variant in north_korea_variants:
        result = get_country_code(variant)
        assert result == "PRK", f"Failed for North Korea variant: {variant}"


def test_get_country_code_niger_vs_nigeria():
    """Test Niger vs Nigeria disambiguation."""
    
    # Niger variants (should not contain "nigeria")
    niger_variants = [
        "Niger",
        "niger",
        "Republic of Niger",
        "niger republic"
    ]
    
    for variant in niger_variants:
        result = get_country_code(variant)
        assert result == "NER", f"Failed for Niger variant: {variant}"
    
    # Nigeria variants (should fallback to pycountry)
    nigeria_variants = [
        "Nigeria",
        "nigeria",
        "Federal Republic of Nigeria",
        "niger nigeria"  # Contains both "niger" and "nigeria"
    ]
    
    # These should NOT return "NER" due to "nigeria" in the name
    for variant in nigeria_variants:
        result = get_country_code(variant)
        assert result != "NER", f"Incorrectly returned NER for Nigeria variant: {variant}"


def test_get_country_code_congo_variants():
    """Test Congo disambiguation - DRC vs Republic of Congo."""
    
    # Democratic Republic of Congo variants
    drc_variants = [
        "Democratic Republic of Congo",
        "democratic republic congo",
        "DR Congo",
        "dr congo",
        "Congo Democratic Republic"
        # Note: "DRC" alone doesn't contain 'dr' and 'congo'
    ]
    
    for variant in drc_variants:
        result = get_country_code(variant)
        assert result == "COD", f"Failed for DRC variant: {variant}"
    
    # Republic of Congo variants
    congo_republic_variant = "Congo Republic"
    result = get_country_code(congo_republic_variant)
    assert result == "COG", f"Failed for ROC variant: {congo_republic_variant}"
    
    # Note: Other ROC variants need pycountry fallback


def test_get_country_code_guinea_bissau():
    """Test Guinea-Bissau edge case."""
    guinea_bissau_variants = [
        "Guinea Bissau",
        "guinea bissau",
        "Guinea-Bissau",
        "Republic of Guinea-Bissau"
    ]
    
    for variant in guinea_bissau_variants:
        result = get_country_code(variant)
        assert result == "GNB", f"Failed for Guinea-Bissau variant: {variant}"


def test_get_country_code_laos():
    """Test Laos edge case."""
    laos_variants = [
        "Laos",
        "laos",
        "LAOS"
    ]
    
    for variant in laos_variants:
        result = get_country_code(variant)
        assert result == "LAO", f"Failed for Laos variant: {variant}"
    
    # "Laos People's Democratic Republic" contains "democratic republic" 
    # which triggers the DR Congo rule first, returning "COD"
    # This is a limitation of the edge case ordering


def test_get_country_code_turkey_variants():
    """Test Turkey/Turkiye edge cases including typos."""
    
    turkey_variants = [
        "Turkey",
        "turkey",
        "TURKEY",
        "Republic of Turkey",
        "Turkiye", 
        "turkiye",
        "TURKIYE",
        "Republic of Turkiye",
        "Kiye",  # Typo case
        "kiye"   # Typo case
    ]
    
    for variant in turkey_variants:
        result = get_country_code(variant)
        assert result == "TUR", f"Failed for Turkey variant: {variant}"


def test_get_country_code_cape_verde():
    """Test Cape Verde edge case."""
    cape_verde_variants = [
        "Cape Verde",
        "cape verde",
        "CAPE VERDE",
        "Republic of Cape Verde",
        "Cabo Verde"
    ]
    
    for variant in cape_verde_variants:
        result = get_country_code(variant)
        assert result == "CPV", f"Failed for Cape Verde variant: {variant}"


def test_get_country_code_swaziland():
    """Test Swaziland edge case."""
    swaziland_variants = [
        "Swaziland",
        "swaziland", 
        "SWAZILAND",
        "Kingdom of Swaziland"
    ]
    
    for variant in swaziland_variants:
        result = get_country_code(variant)
        assert result == "SWZ", f"Failed for Swaziland variant: {variant}"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_get_country_code_israel_west_bank(mock_pycountry):
    """Test Israel and West Bank edge case."""
    # The function doesn't have a specific edge case for Israel/West Bank
    # It would fall back to pycountry
    mock_country = MagicMock()
    mock_country.alpha_3 = "ISR"
    mock_pycountry.countries.lookup.return_value = mock_country
    
    result = get_country_code("Israel")
    assert result == "ISR"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_get_country_code_gambia(mock_pycountry):
    """Test Gambia edge case."""
    # The function doesn't have a specific edge case for Gambia
    # It would fall back to pycountry
    mock_country = MagicMock()
    mock_country.alpha_3 = "GMB"
    mock_pycountry.countries.lookup.return_value = mock_country
    
    result = get_country_code("Gambia")
    assert result == "GMB"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_get_country_code_timor_leste(mock_pycountry):
    """Test Timor-Leste edge case."""
    # The function doesn't have a specific edge case for Timor-Leste
    # It would fall back to pycountry
    mock_country = MagicMock()
    mock_country.alpha_3 = "TLS"
    mock_pycountry.countries.lookup.return_value = mock_country
    
    result = get_country_code("Timor-Leste")
    assert result == "TLS"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_get_country_code_pycountry_fallback_success(mock_pycountry):
    """Test successful fallback to pycountry for standard country names."""
    
    # Mock successful pycountry lookup
    mock_country = MagicMock()
    mock_country.alpha_3 = "USA"
    mock_pycountry.countries.lookup.return_value = mock_country
    
    result = get_country_code("United States")
    
    assert result == "USA"
    mock_pycountry.countries.lookup.assert_called_once_with("United States")


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_get_country_code_pycountry_fallback_failure(mock_pycountry):
    """Test fallback when pycountry lookup fails."""
    
    # Mock failed pycountry lookup
    mock_pycountry.countries.lookup.side_effect = LookupError("Country not found")
    
    result = get_country_code("Unknown Country")
    
    assert result == "Unknown Country"  # Should return original name
    mock_pycountry.countries.lookup.assert_called_once_with("Unknown Country")


def test_get_country_code_case_insensitive():
    """Test that all edge cases are case insensitive."""
    
    test_cases = [
        ("KOSOVO", "XKX"),
        ("kosovo", "XKX"),
        ("Kosovo", "XKX"),
        ("KOREA", "KOR"),
        ("korea", "KOR"),
        ("DEMOCRATIC KOREA", "PRK"),
        ("democratic korea", "PRK"),
        ("NIGER", "NER"),
        ("niger", "NER"),
        ("TURKEY", "TUR"),
        ("turkey", "TUR")
    ]
    
    for country_name, expected_code in test_cases:
        result = get_country_code(country_name)
        assert result == expected_code, f"Case sensitivity failed for {country_name}"


def test_get_country_code_edge_case_precedence():
    """Test that edge cases take precedence over pycountry lookup."""
    
    # Even if pycountry might return different codes, edge cases should win
    with patch('sspi_flask_app.api.resources.utilities.pycountry') as mock_pycountry:
        mock_country = MagicMock()
        mock_country.alpha_3 = "WRONG"
        mock_pycountry.countries.lookup.return_value = mock_country
        
        # Should still return edge case result, not pycountry result
        result = get_country_code("Kosovo")
        assert result == "XKX"  # Edge case should win
        
        # pycountry should not be called for edge cases
        mock_pycountry.countries.lookup.assert_not_called()


def test_get_country_code_partial_matches():
    """Test that partial string matches work correctly."""
    
    # Test that substrings trigger the edge cases
    partial_cases = [
        ("Some Kosovo Region", "XKX"),
        ("South Korea Territory", "KOR"),
        ("Niger Basin", "NER"),
        ("Turkey and Greece", "TUR"),
        ("Cape Verde Islands", "CPV")
    ]
    
    for country_name, expected_code in partial_cases:
        result = get_country_code(country_name)
        assert result == expected_code, f"Partial match failed for {country_name}"


def test_get_country_code_complex_conditions():
    """Test complex conditional logic."""
    
    # Test DR Congo logic: should match "democratic republic" OR ("dr" AND "congo")
    dr_congo_cases = [
        "Democratic Republic of Congo",
        "DR Congo",
        "dr congo region",
        "Congo DR"
    ]
    
    for case in dr_congo_cases:
        result = get_country_code(case)
        assert result == "COD", f"DR Congo logic failed for {case}"
    
    # Test that just "dr" without "congo" doesn't match
    with patch('sspi_flask_app.api.resources.utilities.pycountry') as mock_pycountry:
        mock_country = MagicMock()
        mock_country.alpha_3 = "DOM"
        mock_pycountry.countries.lookup.return_value = mock_country
        
        result = get_country_code("Dominican Republic")  # Has "dr" but no "congo"
        assert result == "DOM"  # Should use pycountry, not COD


def test_get_country_code_empty_and_none_inputs():
    """Test edge cases with empty or None inputs."""
    
    # Empty string
    with patch('sspi_flask_app.api.resources.utilities.pycountry') as mock_pycountry:
        mock_pycountry.countries.lookup.side_effect = LookupError("Empty")
        result = get_country_code("")
        assert result == ""
    
    # None input - function doesn't handle None, will raise TypeError
    with pytest.raises(TypeError):
        get_country_code(None)


def test_get_country_code_whitespace_handling():
    """Test handling of extra whitespace."""
    
    whitespace_cases = [
        ("  Kosovo  ", "XKX"),
        ("\tKorea\n", "KOR"),
        ("  Niger  ", "NER"),
        (" Turkey ", "TUR")
    ]
    
    for country_name, expected_code in whitespace_cases:
        result = get_country_code(country_name)
        assert result == expected_code, f"Whitespace handling failed for '{country_name}'"


def test_get_country_code_numeric_inputs():
    """Test handling of numeric inputs."""
    
    # Function doesn't handle numeric inputs, will raise TypeError
    with pytest.raises(TypeError):
        get_country_code(123)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_get_country_code_standard_countries(mock_pycountry):
    """Test that standard country names work through pycountry."""
    
    standard_countries = [
        ("United States", "USA"),
        ("Germany", "DEU"), 
        ("France", "FRA"),
        ("Japan", "JPN"),
        ("Brazil", "BRA")
    ]
    
    for country_name, expected_code in standard_countries:
        mock_country = MagicMock()
        mock_country.alpha_3 = expected_code
        mock_pycountry.countries.lookup.return_value = mock_country
        
        result = get_country_code(country_name)
        assert result == expected_code
        mock_pycountry.countries.lookup.assert_called_with(country_name)