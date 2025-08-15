from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app.models.errors import InvalidDocumentFormatError, DataMetadataMismatchError
import pytest


@pytest.fixture()
def test_country_score_data():
    yield [
        {
            "IndicatorCode": "BIODIV",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.15,
            "Value": 15.0,
        },
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.90,
            "Value": 90
        },
        {
            "IndicatorCode": "CHMPOL",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.72,
            "Value": 72
        },
        {
            "IndicatorCode": "UNEMPL",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.50,
            "Value": 50.0
        }
    ]


@pytest.fixture()
def test_item_details():
    yield [
        {
            "Children": [],
            "DatasetCodes": [
                "UNSDG_MARINE",
                "UNSDG_TERRST",
                "UNSDG_FRSHWT"
            ],
            "Description": "Percentage of important sites for terrestrial, freshwater, and marine biodiversity that are covered by protected areas, by ecosystem type.",
            "DocumentType": "IndicatorDetail",
            "Indicator": "Biodiversity Protection",
            "IndicatorCode": "BIODIV",
            "ItemCode": "BIODIV",
            "ItemName": "Biodiversity Protection",
            "ItemOrder": 0,
            "ItemType": "Indicator",
            "LowerGoalpost": None,
            "Policy": "Protection of Biodiversity",
            "SourceOrganization": "UNSDG",
            "SourceOrganizationIndicatorCode": SSPI,
            "SourceOrganizationURL": "https://unstats.un.org/sdgapi/swagger/",
            "TreePath": "sspi/sus/eco/biodiv",
            "UpperGoalpost": None
        },
        {
            "Children": [],
            "DatasetCodes": [
                "UNSDG_REDLST"
            ],
            "Description": "Measures the level of extinction risk across species within a country. Index values of 1 represent all species qualifying as having an extinction risk of “least concern,” while values of 0 represent all species having gone extinct.",
            "DocumentType": "IndicatorDetail",
            "Footnote": None,
            "Indicator": "IUCN Red List Index",
            "IndicatorCode": "REDLST",
            "Inverted": False,
            "ItemCode": "REDLST",
            "ItemName": "IUCN Red List Index",
            "ItemOrder": 1,
            "ItemType": "Indicator",
            "LowerGoalpost": 0.0,
            "Policy": "Endangered Species Protection",
            "TreePath": "sspi/sus/eco/redlst",
            "UpperGoalpost": 1.0
        },
        {
            "Children": [],
            "DatasetCodes": [
                "UNSDG_STKHLM",
                "UNSDG_BASELA",
                "UNSDG_MONTRL",
                "UNSDG_MINMAT",
                "UNSDG_ROTDAM"
            ],
            "Description": "Compliance with three treaties",
            "DocumentType": "IndicatorDetail",
            "Footnote": None,
            "Indicator": "Chemical Pollution Convention Compliance",
            "IndicatorCode": "CHMPOL",
            "ItemCode": "CHMPOL",
            "ItemName": "Chemical Pollution Convention Compliance",
            "ItemOrder": 4,
            "ItemType": "Indicator",
            "LowerGoalpost": 0.0,
            "Policy": "Chemical Waste Management",
            "TreePath": "sspi/sus/lnd/chmpol",
            "UpperGoalpost": 100.0
        },
        {
            "Children": [],
            "DatasetCodes": [
                "ILO_UNEMPL"
            ],
            "Description": "Percentage of unemployed receiving unemployment benefits.",
            "DocumentType": "IndicatorDetail",
            "Footnote": None,
            "Indicator": "Unemployment Benefits Coverage",
            "IndicatorCode": "UNEMPL",
            "Inverted": False,
            "ItemCode": "UNEMPL",
            "ItemName": "Unemployment Benefits Coverage",
            "ItemOrder": 17,
            "ItemType": "Indicator",
            "LowerGoalpost": 0.0,
            "Policy": "Unemployment \nBenefits",
            "SourceOrganization": "ILO",
            "SourceOrganizationIndicatorCode": "DF_SDG_0131_SEX_SOC_RT",
            "SourceOrganizationURL": "https://ilostat.ilo.org/",
            "TreePath": "sspi/ms/wwb/unempl",
            "UpperGoalpost": 100.0
        },
        {
            "Category": "Ecosystem",
            "CategoryCode": "ECO",
            "Children": [
                "BIODIV",
                "REDLST"
            ],
            "Description": "Placeholder",
            "DocumentType": "CategoryDetail",
            "IndicatorCodes": [
                "BIODIV",
                "REDLST"
            ],
            "ItemCode": "ECO",
            "ItemName": "Ecosystem",
            "ItemOrder": 0,
            "ItemType": "Category",
            "Pillar": "Sustainability",
            "PillarCode": "SUS",
            "ShortDescription": "Policies protecting natural ecosystems",
            "TreePath": "sspi/sus/eco"
        },
        {
            "Category": "Land",
            "CategoryCode": "LND",
            "Children": [
                "CHMPOL",
            ],
            "Description": "Placeholder",
            "DocumentType": "CategoryDetail",
            "IndicatorCodes": [
                "CHMPOL",
            ],
            "ItemCode": "LND",
            "ItemName": "Land",
            "ItemOrder": 1,
            "ItemType": "Category",
            "Pillar": "Sustainability",
            "PillarCode": "SUS",
            "ShortDescription": "Policies promoting sustainable land use",
            "TreePath": "sspi/sus/lnd"
        },
        {
            "Category": "Worker Wellbeing",
            "CategoryCode": "WWB",
            "Children": [
                "UNEMPL"
            ],
            "Description": "Placeholder",
            "DocumentType": "CategoryDetail",
            "IndicatorCodes": [
                "UNEMPL",
            ],
            "ItemCode": "WWB",
            "ItemName": "Worker Wellbeing",
            "ItemOrder": 6,
            "ItemType": "Category",
            "Pillar": "Market Structure",
            "PillarCode": "MS",
            "ShortDescription": "Policies promoting the safety of workers on and off the job",
            "TreePath": "sspi/ms/wwb"
        },
        {
            "CategoryCodes": [
                "ECO",
                "LND",
            ],
            "Children": [
                "ECO",
                "LND",
            ],
            "Description": "Placeholder",
            "DocumentType": "PillarDetail",
            "ItemCode": "SUS",
            "ItemName": "Sustainability",
            "ItemOrder": 0,
            "ItemType": "Pillar",
            "Pillar": "Sustainability",
            "PillarCode": "SUS",
            "ShortDescription": "Measures policies protecting ecosystems and the environment.",
            "TreePath": "sspi/sus"
        },
        {
            "CategoryCodes": [
                "WWB",
            ],
            "Children": [
                "WWB"
            ],
            "Description": "Placeholder",
            "DocumentType": "PillarDetail",
            "ItemCode": "MS",
            "ItemName": "Market Structure",
            "ItemOrder": 1,
            "ItemType": "Pillar",
            "Pillar": "Market Structure",
            "PillarCode": "MS",
            "ShortDescription": "Measures policies which by which countries structure markets to provide goods and services.",
            "TreePath": "sspi/ms"
        },
        {
            "Children": [
                "MS",
                "SUS"
            ],
            "Code": "SSPI",
            "Description": "The Sustainable and Shared Proseperity Index scores national policies across three pillars: Sustainability, Market Structure, and Public Goods\n",
            "DocumentType": "SSPIDetail",
            "ItemCode": "SSPI",
            "ItemName": "Sustainable and Shared Prosperity Policy Index",
            "ItemOrder": 0,
            "ItemType": "SSPI",
            "Name": "Sustainable and Shared Prosperity Policy Index",
            "PillarCodes": [
                "SUS",
                "MS"
            ],
            "ShortDescription": "The Sustainable and Shared Proseperity Index scores national policies across three pillars: Sustainability, Market Structure, and Public Goods\n",
            "TreePath": "sspi"
        }
    ]

def test_sspi_construction(test_item_details, test_country_score_data):
    sspi = SSPI(test_item_details, test_country_score_data)



# def test_category_indicator_getter(dummy_category_list):
#     assert dummy_category_list[0].code == "ECO"
#     assert len(dummy_category_list[0].indicators) == 2
#     print(dummy_category_list[0].indicators)
#     biodiv = dummy_category_list[0].get_indicator("BIODIV")
#     redlst = dummy_category_list[0].get_indicator("REDLST")
#     assert biodiv is not None
#     assert redlst is not None


# def test_category_handles_repeats(dummy_category_list, test_item_details):
#     tol = 10**-10
#     assert abs(dummy_category_list[0].score() - 0.525) < tol
#     new_data = {
#         "IndicatorCode": "BIODIV",
#         "CountryCode": "AUS",
#         "Year": 2018,
#         "Value": 0,
#         "Score": 0
#     }
#     dummy_category_list[0].load(test_item_details[0], new_data)
#     assert len(dummy_category_list[0].indicators) == 2
#     assert abs(dummy_category_list[0].score() - 0.45) < tol


# def test_indicator_catches_invalid_score(dummy_category_list, test_item_details):
#     eco = dummy_category_list[0]
#     new_data = {
#         "IndicatorCode": "BIODIV",
#         "CountryCode": "AUS",
#         "Year": 2018,
#         "Value": 105,
#         "Score": 1.05
#     }
#     with pytest.raises(InvalidDocumentFormatError) as exception_info:
#         eco.load(test_item_details[0], new_data)
#     new_data = {
#         "IndicatorCode": "BIODIV",
#         "CountryCode": "AUS",
#         "Year": 2018,
#         "Value": -0.005,
#         "Score": -0.00005
#     }
#     with pytest.raises(InvalidDocumentFormatError) as exception_info:
#         eco.load(test_item_details[0], new_data)


# def test_indicator_fails_to_load_missing(dummy_category_list, test_item_details):
#     eco = dummy_category_list[0]
#     new_data = {
#         "IndicatorCode": "BIODIV",
#         "CountryCode": "AUS",
#         "Year": 2018,
#     }
#     with pytest.raises(InvalidDocumentFormatError) as exception_info:
#         eco.load(test_item_details[0], new_data)


# def test_category_score_fails_on_missing_data(dummy_category_list, test_item_details):
#     eco = dummy_category_list[0]
#     new_data = {
#         "IndicatorCode": "BIODIV",
#         "CountryCode": "AUS",
#         "Year": 2018,
#         "Value": None,
#         "Score": None
#     }
#     eco.load(test_item_details[0], new_data)
#     with pytest.raises(TypeError) as exception_info:
#         eco.score()


# @pytest.fixture()
# def dummy_pillar_list(test_item_details, test_country_score_data):

#     def get_pillar(pillar, pillar_code):
#         for p in pillars:
#             if p.code == pillar_code:
#                 return p
#         return None

#     pillars = []
#     for i, detail in enumerate(test_item_details):
#         matched_pillar = get_pillar(pillars, detail["PillarCode"])
#         if not matched_pillar:
#             matched_pillar = Pillar(detail, test_country_score_data[i])
#             pillars.append(matched_pillar)
#         else:
#             matched_pillar.load(detail, test_country_score_data[i])
#     yield pillars


# def test_pillar_construction(dummy_pillar_list):
#     assert len(dummy_pillar_list) == 2
#     assert len(dummy_pillar_list[0].categories) == 2


# def test_pillar_score(dummy_pillar_list):
#     scores = [0, 0]
#     for i, pil in enumerate(dummy_pillar_list):
#         scores[i] = pil.score()
#     tol = 10**-10
#     assert abs(scores[0] - (0.525 + 0.72)/2) < tol
#     assert abs(scores[1] - 0.50) < tol


@pytest.fixture()
def sspi_overall(test_item_details, test_country_score_data):
    yield SSPI(test_item_details, test_country_score_data)


def test_sspi_fails_on_mismatch(test_item_details, test_country_score_data):
    new_data = {
        "IndicatorCode": "FATINJ",
        "CountryCode": "AUS",
        "Year": 2018,
        "Score": 0.7
    }
    country_scores = list(test_country_score_data) + [new_data]
    with pytest.raises(DataMetadataMismatchError):
        sspi = SSPI(test_item_details, country_scores)


def test_sspi_score(sspi_overall):
    tol = 10**-10
    assert abs(sspi_overall.get_item("SSPI").score - ((0.525 + 0.72)/2 + 0.5)/2) < tol


def test_sspi_pillar_scores(sspi_overall):
    tol = 10**-10
    assert abs(sspi_overall.get_item("SUS").score - (0.525 + 0.72)/2) < tol
    assert abs(sspi_overall.get_item("MS").score - 0.50) < tol


def test_sspi_category_scores(sspi_overall):
    tol = 10**-10
    assert abs(sspi_overall.get_item("ECO").score - 0.525) < tol
    assert abs(sspi_overall.get_item("LND").score - 0.72) < tol
    assert abs(sspi_overall.get_item("WWB").score - 0.50) < tol


def test_sspi_indicator_scores(sspi_overall):
    tol = 10**-10
    assert abs(sspi_overall.get_item("BIODIV").score - 0.15) < tol
    assert abs(sspi_overall.get_item("REDLST").score - 0.90) < tol
    assert abs(sspi_overall.get_item("CHMPOL").score - 0.72) < tol
    assert abs(sspi_overall.get_item("UNEMPL").score - 0.50) < tol


def test_score_percolation_single_indicator_category():
    """Test that when a category has only one indicator, the category score equals the indicator score"""
    tol = 10**-10
    
    # Test data with single indicator per category for clear percolation testing
    single_indicator_data = [
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "USA",
            "Year": 2020,
            "Score": 0.835,
            "Value": 83.5
        },
        {
            "IndicatorCode": "CHMPOL", 
            "CountryCode": "USA",
            "Year": 2020,
            "Score": 0.672,
            "Value": 67.2
        }
    ]
    
    # Metadata with single-indicator categories
    single_indicator_metadata = [
        {
            "Children": [],
            "IndicatorCode": "REDLST",
            "ItemCode": "REDLST",
            "ItemName": "IUCN Red List Index",
            "ItemType": "Indicator",
            "TreePath": "sspi/sus/eco/redlst"
        },
        {
            "Children": [],
            "IndicatorCode": "CHMPOL",
            "ItemCode": "CHMPOL", 
            "ItemName": "Chemical Pollution Convention Compliance",
            "ItemType": "Indicator",
            "TreePath": "sspi/sus/lnd/chmpol"
        },
        {
            "CategoryCode": "ECO",
            "IndicatorCodes": ["REDLST"],
            "ItemCode": "ECO",
            "ItemName": "Ecosystem",
            "ItemType": "Category",
            "PillarCode": "SUS",
            "TreePath": "sspi/sus/eco"
        },
        {
            "CategoryCode": "LND", 
            "IndicatorCodes": ["CHMPOL"],
            "ItemCode": "LND",
            "ItemName": "Land",
            "ItemType": "Category", 
            "PillarCode": "SUS",
            "TreePath": "sspi/sus/lnd"
        },
        {
            "CategoryCodes": ["ECO", "LND"],
            "ItemCode": "SUS",
            "ItemName": "Sustainability",
            "ItemType": "Pillar",
            "TreePath": "sspi/sus"
        },
        {
            "PillarCodes": ["SUS"],
            "ItemCode": "SSPI",
            "ItemName": "Sustainable and Shared Prosperity Policy Index",
            "ItemType": "SSPI",
            "TreePath": "sspi"
        }
    ]
    
    sspi = SSPI(single_indicator_metadata, single_indicator_data)
    
    # Test that single-indicator categories have scores equal to their indicator
    assert abs(sspi.get_item("ECO").score - sspi.get_item("REDLST").score) < tol, \
        f"ECO category score {sspi.get_item('ECO').score} should equal REDLST indicator score {sspi.get_item('REDLST').score}"
    
    assert abs(sspi.get_item("LND").score - sspi.get_item("CHMPOL").score) < tol, \
        f"LND category score {sspi.get_item('LND').score} should equal CHMPOL indicator score {sspi.get_item('CHMPOL').score}"


def test_score_percolation_single_category_pillar():
    """Test that when a pillar has only one category, the pillar score equals the category score"""
    tol = 10**-10
    
    # Test data with single category pillar
    single_category_data = [
        {
            "IndicatorCode": "UNEMPL",
            "CountryCode": "USA", 
            "Year": 2020,
            "Score": 0.451,
            "Value": 45.1
        }
    ]
    
    # Metadata with single-category pillar
    single_category_metadata = [
        {
            "Children": [],
            "IndicatorCode": "UNEMPL",
            "ItemCode": "UNEMPL",
            "ItemName": "Unemployment Benefits Coverage",
            "ItemType": "Indicator",
            "TreePath": "sspi/ms/wwb/unempl"
        },
        {
            "CategoryCode": "WWB",
            "IndicatorCodes": ["UNEMPL"],
            "ItemCode": "WWB",
            "ItemName": "Worker Wellbeing",
            "ItemType": "Category",
            "PillarCode": "MS", 
            "TreePath": "sspi/ms/wwb"
        },
        {
            "CategoryCodes": ["WWB"],
            "ItemCode": "MS",
            "ItemName": "Market Structure",
            "ItemType": "Pillar",
            "TreePath": "sspi/ms"
        },
        {
            "PillarCodes": ["MS"],
            "ItemCode": "SSPI",
            "ItemName": "Sustainable and Shared Prosperity Policy Index", 
            "ItemType": "SSPI",
            "TreePath": "sspi"
        }
    ]
    
    sspi = SSPI(single_category_metadata, single_category_data)
    
    # Test that single-category pillar has score equal to its category
    assert abs(sspi.get_item("MS").score - sspi.get_item("WWB").score) < tol, \
        f"MS pillar score {sspi.get_item('MS').score} should equal WWB category score {sspi.get_item('WWB').score}"
    
    # Test full percolation: indicator -> category -> pillar -> SSPI 
    assert abs(sspi.get_item("WWB").score - sspi.get_item("UNEMPL").score) < tol, \
        f"WWB category score {sspi.get_item('WWB').score} should equal UNEMPL indicator score {sspi.get_item('UNEMPL').score}"
        
    assert abs(sspi.get_item("SSPI").score - sspi.get_item("UNEMPL").score) < tol, \
        f"SSPI score {sspi.get_item('SSPI').score} should equal UNEMPL indicator score {sspi.get_item('UNEMPL').score} in single-indicator hierarchy"


def test_score_percolation_time_series():
    """Test that score percolation works correctly across multiple years"""
    tol = 10**-10
    
    # Multi-year test data with single indicator category
    time_series_data = [
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "USA",
            "Year": 2018,
            "Score": 0.836,
        },
        {
            "IndicatorCode": "REDLST", 
            "CountryCode": "USA",
            "Year": 2019,
            "Score": 0.835,
        },
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "USA", 
            "Year": 2020,
            "Score": 0.834,
        }
    ]
    
    # Simple hierarchy metadata
    time_series_metadata = [
        {
            "Children": [],
            "IndicatorCode": "REDLST",
            "ItemCode": "REDLST",
            "ItemName": "IUCN Red List Index",
            "ItemType": "Indicator",
            "TreePath": "sspi/sus/eco/redlst"
        },
        {
            "CategoryCode": "ECO",
            "IndicatorCodes": ["REDLST"],
            "ItemCode": "ECO", 
            "ItemName": "Ecosystem",
            "ItemType": "Category",
            "PillarCode": "SUS",
            "TreePath": "sspi/sus/eco"
        },
        {
            "CategoryCodes": ["ECO"],
            "ItemCode": "SUS",
            "ItemName": "Sustainability", 
            "ItemType": "Pillar",
            "TreePath": "sspi/sus"
        },
        {
            "PillarCodes": ["SUS"],
            "ItemCode": "SSPI",
            "ItemName": "Sustainable and Shared Prosperity Policy Index",
            "ItemType": "SSPI", 
            "TreePath": "sspi"
        }
    ]
    
    # Test each year separately to verify consistent percolation
    for year_data in time_series_data:
        sspi = SSPI(time_series_metadata, [year_data])
        
        year = year_data["Year"]
        expected_score = year_data["Score"]
        
        # Verify all levels have the same score as the single indicator
        assert abs(sspi.get_item("REDLST").score - expected_score) < tol, \
            f"Year {year}: REDLST indicator should have score {expected_score}"
            
        assert abs(sspi.get_item("ECO").score - expected_score) < tol, \
            f"Year {year}: ECO category should equal REDLST score {expected_score}, got {sspi.get_item('ECO').score}"
            
        assert abs(sspi.get_item("SUS").score - expected_score) < tol, \
            f"Year {year}: SUS pillar should equal REDLST score {expected_score}, got {sspi.get_item('SUS').score}"
            
        assert abs(sspi.get_item("SSPI").score - expected_score) < tol, \
            f"Year {year}: SSPI should equal REDLST score {expected_score}, got {sspi.get_item('SSPI').score}"


def test_fragile_year_consistency():
    """Test that the fragile SSPI implementation correctly enforces year consistency"""
    
    # Test data with inconsistent years - should crash
    inconsistent_year_data = [
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "USA",
            "Year": 2018,
            "Score": 0.836,
        },
        {
            "IndicatorCode": "CHMPOL",
            "CountryCode": "USA", 
            "Year": 2019,  # Different year - should cause failure
            "Score": 0.672,
        }
    ]
    
    simple_metadata = [
        {
            "IndicatorCode": "REDLST",
            "ItemCode": "REDLST",
            "ItemType": "Indicator",
        },
        {
            "IndicatorCode": "CHMPOL", 
            "ItemCode": "CHMPOL",
            "ItemType": "Indicator",
        },
        {
            "ItemCode": "SSPI",
            "ItemType": "SSPI",
            "PillarCodes": []
        }
    ]
    
    # Should crash due to inconsistent years
    with pytest.raises(AssertionError, match="All indicators must have same year"):
        SSPI(simple_metadata, inconsistent_year_data)


def test_fragile_missing_year():
    """Test that the fragile SSPI implementation crashes on missing year data"""
    
    missing_year_data = [
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "USA",
            "Score": 0.836,
            # Missing Year field - should crash
        }
    ]
    
    simple_metadata = [
        {
            "IndicatorCode": "REDLST",
            "ItemCode": "REDLST", 
            "ItemType": "Indicator",
        },
        {
            "ItemCode": "SSPI",
            "ItemType": "SSPI",
            "PillarCodes": []
        }
    ]
    
    # Should crash due to missing year - KeyError occurs first
    with pytest.raises(KeyError, match="Year"):
        SSPI(simple_metadata, missing_year_data)


def test_eco_redlst_bug_regression():
    """
    Regression test for the specific ECO category bug described in issue #733.
    When ECO category has only REDLST indicator (due to complete indicator filtering),
    ECO scores should exactly equal REDLST scores across all years.
    """
    tol = 10**-10
    
    # Test multiple years with realistic REDLST scores (matching real USA data)
    redlst_scores_by_year = {
        2018: 0.83596,
        2019: 0.83538,
        2020: 0.83458,
        2021: 0.83379,
        2022: 0.83338,
        2023: 0.83231
    }
    
    # Metadata matching real ECO category structure but with only REDLST (complete indicator)
    eco_redlst_metadata = [
        {
            "Children": [],
            "IndicatorCode": "REDLST",
            "ItemCode": "REDLST",
            "ItemName": "IUCN Red List Index",
            "ItemType": "Indicator",
            "TreePath": "sspi/sus/eco/redlst"
        },
        {
            "CategoryCode": "ECO",
            "IndicatorCodes": ["REDLST"],  # Only REDLST after filtering incomplete indicators
            "ItemCode": "ECO",
            "ItemName": "Ecosystem",
            "ItemType": "Category", 
            "PillarCode": "SUS",
            "TreePath": "sspi/sus/eco"
        },
        {
            "CategoryCodes": ["ECO"],
            "ItemCode": "SUS",
            "ItemName": "Sustainability",
            "ItemType": "Pillar",
            "TreePath": "sspi/sus"
        },
        {
            "PillarCodes": ["SUS"],
            "ItemCode": "SSPI",
            "ItemName": "Sustainable and Shared Prosperity Policy Index",
            "ItemType": "SSPI",
            "TreePath": "sspi"
        }
    ]
    
    # Test each year separately (as finalize process does)
    for year, expected_score in redlst_scores_by_year.items():
        year_data = [
            {
                "IndicatorCode": "REDLST",
                "CountryCode": "USA",
                "Year": year,
                "Score": expected_score
            }
        ]
        
        sspi = SSPI(eco_redlst_metadata, year_data)
        
        # The bug manifested as ECO having different scores than REDLST
        # This test ensures they are identical
        redlst_score = sspi.get_item("REDLST").score
        eco_score = sspi.get_item("ECO").score
        
        assert abs(redlst_score - expected_score) < tol, \
            f"Year {year}: REDLST should have score {expected_score}, got {redlst_score}"
            
        assert abs(eco_score - expected_score) < tol, \
            f"Year {year}: ECO should equal REDLST score {expected_score}, got {eco_score}"
            
        assert abs(eco_score - redlst_score) < tol, \
            f"Year {year}: ECO score {eco_score} should exactly equal REDLST score {redlst_score}"
        
        # Verify percolation up the hierarchy 
        sus_score = sspi.get_item("SUS").score
        sspi_score = sspi.get_item("SSPI").score
        
        assert abs(sus_score - expected_score) < tol, \
            f"Year {year}: SUS pillar should equal REDLST score {expected_score}, got {sus_score}"
            
        assert abs(sspi_score - expected_score) < tol, \
            f"Year {year}: SSPI should equal REDLST score {expected_score}, got {sspi_score}"


# def test_sspi_score_tree(sspi_overall):
#     score_tree = sspi_overall.score_tree()
#     assert len(score_tree["SSPI"].keys()) == 2
#     assert len(score_tree["SSPI"]["Pillars"]) == 2
#     assert len(score_tree["SSPI"]["Pillars"][0].keys()) == 4
#     assert len(score_tree["SSPI"]["Pillars"][1].keys()) == 4
#     assert len(score_tree["SSPI"]["Pillars"][0]["Categories"]) == 2
#     assert len(score_tree["SSPI"]["Pillars"][1]["Categories"]) == 1
#     assert len(score_tree["SSPI"]["Pillars"][0]["Categories"][0].keys()) == 4
#     assert len(score_tree["SSPI"]["Pillars"][0]["Categories"][1].keys()) == 4
#     assert len(score_tree["SSPI"]["Pillars"][0]
#                ["Categories"][0]["Indicators"]) == 2
#     assert len(score_tree["SSPI"]["Pillars"][0]
#                ["Categories"][1]["Indicators"]) == 1
