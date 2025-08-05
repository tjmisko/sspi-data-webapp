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
