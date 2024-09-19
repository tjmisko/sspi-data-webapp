from sspi_flask_app.models.sspi import SSPI, Pillar, Category, Indicator
from sspi_flask_app.models.errors import InvalidDocumentFormatError, DataOrderError
import pytest

@pytest.fixture()
def test_country_score_data():
    yield [
        {
            "IndicatorCode": "BIODIV",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.15
        },
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.90
        },
        {
            "IndicatorCode": "STKHLM",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.72
        },
        {
            "IndicatorCode": "UNEMPL",
            "CountryCode": "AUS",
            "Year": 2018,
            "Score": 0.50
        }
    ]


@pytest.fixture()
def test_indicator_details():
    yield [
        {
            "DocumentType": "IndicatorDetail",
            "Metadata": {
                "Category": "Ecosystem",
                "CategoryCode": "ECO",
                "Description": "Percentage of important sites for terrestrial, freshwater, and marine biodiversity that are covered by protected areas, by ecosystem type.",
                "DocumentType": "IndicatorDetail",
                "Footnote": None,
                "GoalpostString": "(0, 100) \n(0, 100) \n(0, 100)",
                "Indicator": "Biodiversity Protection",
                "IndicatorCode": "BIODIV",
                "IntermediateWeights": "[0.33, 0.33, 0.33]",
                "Inverted": False,
                "LowerGoalpost": None,
                "NeedsFootnote": None,
                "NumberOfIntermediates": 3,
                "Pillar": "Sustainability",
                "PillarCode": "SUS",
                "Policy": "Protection of \nBiodiversity",
                "SourceOrganization": "UN SDG",
                "SourceOrganizationIndicatorCode": "[\"14.5.1\", \"15.1.2\"]",
                "SourceOrganizationURL": "https://unstats.un.org/sdgapi/swagger/",
                "SourceYear_sspi_main_data_v3": "2018",
                "StaticDataURL": "https://unstats.un.org/sdgs/dataportal/database ",
                "Summarized Footnote": None,
                "UpdatedDescription": None,
                "UpperGoalpost": None
            }
        },
        {
            "DocumentType": "IndicatorDetail",
            "Metadata": {
                "Category": "Ecosystem",
                "CategoryCode": "ECO",
                "Description": "Measures the level of extinction risk across species within a country. Index values of 1 represent all species qualifying as having an extinction risk of \u201cleast concern,\u201d while values of 0 represent all species having gone extinct.",
                "DocumentType": "IndicatorDetail",
                "Footnote": None,
                "GoalpostString": "(0, 1)",
                "Indicator": "IUCN Red List Index",
                "IndicatorCode": "REDLST",
                "IntermediateCodes": None,
                "IntermediateWeights": None,
                "Inverted": False,
                "LowerGoalpost": 0.0,
                "NeedsFootnote": None,
                "NumberOfIntermediates": 1,
                "Pillar": "Sustainability",
                "PillarCode": "SUS",
                "Policy": "Endangered Species Protection",
                "SourceOrganization": "UN SDG",
                "SourceOrganizationIndicatorCode": "[\"15.5.1\"]",
                "SourceOrganizationURL": "https://unstats.un.org/sdgapi/swagger/",
                "SourceYear_sspi_main_data_v3": "2019",
                "StaticDataURL": "https://unstats.un.org/sdgs/dataportal/database ",
                "Summarized Footnote": None,
                "UpdatedDescription": None,
                "UpperGoalpost": 1.0
            }
        },
        {
            "DocumentType": "IndicatorDetail",
            "Metadata": {
                "Category": "Land",
                "CategoryCode": "LND",
                "Description": "Percent of provisions concerning Persistent Organic Pollutants from Stockholm Convention ratified and followed.",
                "DocumentType": "IndicatorDetail",
                "Footnote": None,
                "GoalpostString": "(0, 100)",
                "Indicator": "Stockholm Convention Compliance",
                "IndicatorCode": "STKHLM",
                "IntermediateCodes": None,
                "IntermediateWeights": None,
                "Inverted": False,
                "LowerGoalpost": 0.0,
                "NeedsFootnote": None,
                "NumberOfIntermediates": 1,
                "Pillar": "Sustainability",
                "PillarCode": "SUS",
                "Policy": "Chemical Waste \nManagement",
                "SourceOrganization": "UN SDG",
                "SourceOrganizationIndicatorCode": "[\"12.4.1\"]",
                "SourceOrganizationURL": "https://unstats.un.org/sdgapi/swagger/",
                "SourceYear_sspi_main_data_v3": "2015",
                "StaticDataURL": "https://unstats.un.org/sdgs/dataportal/database ",
                "Summarized Footnote": None,
                "UpdatedDescription": None,
                "UpperGoalpost": 100.0
            }
        },
        {
            "DocumentType": "IndicatorDetail",
            "Metadata": {
                "Category": "Worker \nWellbeing",
                "CategoryCode": "WEB",
                "Description": "Percentage of unemployed receiving unemployment benefits.",
                "DocumentType": "IndicatorDetail",
                "Footnote": None,
                "GoalpostString": "(0, 100)",
                "Indicator": "Unemployment \nBenefits Coverage",
                "IndicatorCode": "UNEMPL",
                "IntermediateCodes": None,
                "IntermediateWeights": None,
                "Inverted": False,
                "LowerGoalpost": 0.0,
                "NeedsFootnote": None,
                "NumberOfIntermediates": 1,
                "Pillar": "Market Structure",
                "PillarCode": "MS",
                "Policy": "Unemployment \nBenefits",
                "SourceOrganization": "ILO",
                "SourceOrganizationIndicatorCode": None,
                "SourceOrganizationURL": "https://ilostat.ilo.org/",
                "SourceYear_sspi_main_data_v3": "2018",
                "StaticDataURL": None,
                "Summarized Footnote": None,
                "UpdatedDescription": None,
                "UpperGoalpost": 100.0
            }
        }
    ]


def test_indicator_construction(test_indicator_details, test_country_score_data):
    biodiv = Indicator(test_indicator_details[0], test_country_score_data[0])
    assert biodiv.score == 0.15
    assert biodiv.code == "BIODIV"
    redlst = Indicator(test_indicator_details[1], test_country_score_data[1])
    assert redlst.score == 0.90
    assert redlst.code == "REDLST"
    stkhlm = Indicator(test_indicator_details[2], test_country_score_data[2])
    assert stkhlm.score == 0.72
    assert stkhlm.code == "STKHLM"
    unempl = Indicator(test_indicator_details[3], test_country_score_data[3])
    assert unempl.score == 0.50
    assert unempl.code == "UNEMPL"

@pytest.fixture()
def dummy_category_list(test_indicator_details, test_country_score_data):

    def get_category(categories, category_code):
        for c in categories:
            if c.code == category_code:
                return c
        return None

    categories = []
    for i, detail in enumerate(test_indicator_details):
        matched_category = get_category(categories, detail["Metadata"]["CategoryCode"])
        if not matched_category:
            matched_category = Category(detail, test_country_score_data[i])
            categories.append(matched_category)
        else:
            matched_category.load(detail, test_country_score_data[i])
    yield categories

def test_category_construction(dummy_category_list):
    assert len(dummy_category_list) == 3
    assert len(dummy_category_list[0].indicators) == 2

def test_category_score(dummy_category_list):
    scores = [0, 0, 0]
    for i, cat in enumerate(dummy_category_list):
        scores[i] = cat.score()
    tol = 10**-10
    assert abs(scores[0] - 0.525) < tol
    assert abs(scores[1] - 0.72) < tol
    assert abs(scores[2] - 0.50) < tol

def test_category_indicator_getter(dummy_category_list):
    assert dummy_category_list[0].code == "ECO"
    assert len(dummy_category_list[0].indicators) == 2
    print(dummy_category_list[0].indicators)
    biodiv = dummy_category_list[0].get_indicator("BIODIV")
    redlst = dummy_category_list[0].get_indicator("REDLST")
    assert biodiv is not None
    assert redlst is not None

def test_category_handles_repeats(dummy_category_list, test_indicator_details):
    tol = 10**-10
    assert abs(dummy_category_list[0].score() - 0.525) < tol
    new_data =  {
        "IndicatorCode": "BIODIV",
        "CountryCode": "AUS",
        "Year": 2018,
        "Score": 0
    }
    dummy_category_list[0].load(test_indicator_details[0], new_data)
    assert len(dummy_category_list[0].indicators) == 2
    assert abs(dummy_category_list[0].score() - 0.45) < tol

def test_indicator_catches_invalid_score(dummy_category_list, test_indicator_details):
    eco = dummy_category_list[0]
    new_data =  {
        "IndicatorCode": "BIODIV",
        "CountryCode": "AUS",
        "Year": 2018,
        "Score": 1.05
    }
    with pytest.raises(InvalidDocumentFormatError) as exception_info:
        eco.load(test_indicator_details[0], new_data)
    new_data =  {
        "IndicatorCode": "BIODIV",
        "CountryCode": "AUS",
        "Year": 2018,
        "Score": -0.00005
    }
    with pytest.raises(InvalidDocumentFormatError) as exception_info:
        eco.load(test_indicator_details[0], new_data)

def test_indicator_fails_to_load_missing(dummy_category_list, test_indicator_details):
    eco = dummy_category_list[0]
    new_data =  {
        "IndicatorCode": "BIODIV",
        "CountryCode": "AUS",
        "Year": 2018,
    }
    with pytest.raises(InvalidDocumentFormatError) as exception_info:
        eco.load(test_indicator_details[0], new_data)

def test_category_score_fails_on_missing_data(dummy_category_list, test_indicator_details):
    eco = dummy_category_list[0]
    new_data =  {
        "IndicatorCode": "BIODIV",
        "CountryCode": "AUS",
        "Year": 2018,
        "Score": None
    }
    tol = 10**-10
    eco.load(test_indicator_details[0], new_data)
    with pytest.raises(TypeError) as exception_info:
         eco.score()

@pytest.fixture()
def dummy_pillar_list(test_indicator_details, test_country_score_data):

    def get_pillar(pillar, pillar_code):
        for p in pillars:
            if p.code == pillar_code:
                return p
        return None

    pillars = []
    for i, detail in enumerate(test_indicator_details):
        matched_pillar = get_pillar(pillars, detail["Metadata"]["PillarCode"])
        if not matched_pillar:
            matched_pillar = Pillar(detail, test_country_score_data[i])
            pillars.append(matched_pillar)
        else:
            matched_pillar.load(detail, test_country_score_data[i])
    yield pillars

def test_pillar_construction(dummy_pillar_list):
    assert len(dummy_pillar_list) == 2
    assert len(dummy_pillar_list[0].categories) == 2

def test_pillar_score(dummy_pillar_list):
    scores = [0, 0]
    for i, pil in enumerate(dummy_pillar_list):
        scores[i] = pil.score()
    tol = 10**-10
    assert abs(scores[0] - (0.525 + 0.72)/2) < tol
    assert abs(scores[1] - 0.50) < tol

@pytest.fixture()
def sspi_overall(test_indicator_details, test_country_score_data):
    yield SSPI(test_indicator_details, test_country_score_data)

def test_sspi_construction(sspi_overall):
    assert len(sspi_overall.pillars) == 2
    assert len(sspi_overall.categories) == 3
    assert len(sspi_overall.indicators) == 4

def test_sspi_fails_on_mismatch(test_indicator_details, test_country_score_data):
    new_data = {
        "IndicatorCode": "FATINJ",
        "CountryCode": "AUS",
        "Year": 2018,
        "Score": 0.7
    }
    country_scores = list(test_country_score_data) + [new_data]
    with pytest.raises(DataOrderError):
        sspi = SSPI(test_indicator_details, country_scores)

def test_sspi_score(sspi_overall):
    tol = 10**-10
    assert abs(sspi_overall.score() - ((0.525 + 0.72)/2 + 0.5)/2) < tol

def test_sspi_pillar_scores(sspi_overall):
    scores = sspi_overall.pillar_scores()
    tol = 10**-10
    assert abs(scores["SUS"] - (0.525 + 0.72)/2) < tol
    assert abs(scores["MS"] - 0.50) < tol

def test_sspi_category_scores(sspi_overall):
    scores = sspi_overall.category_scores()
    tol = 10**-10
    assert abs(scores["ECO"] - 0.525) < tol
    assert abs(scores["LND"] - 0.72) < tol
    assert abs(scores["WEB"] - 0.50) < tol

def test_sspi_indicator_scores(sspi_overall):
    scores = sspi_overall.indicator_scores()
    tol = 10**-10
    assert abs(scores["BIODIV"] - 0.15) < tol
    assert abs(scores["REDLST"] - 0.90) < tol
    assert abs(scores["STKHLM"] - 0.72) < tol
    assert abs(scores["UNEMPL"] - 0.50) < tol

def test_sspi_score_tree(sspi_overall):
    score_tree = sspi_overall.score_tree()
    assert len(score_tree["SSPI"].keys()) == 2
    assert len(score_tree["SSPI"]["Pillars"]) == 2
    assert len(score_tree["SSPI"]["Pillars"][0].keys()) == 4
    assert len(score_tree["SSPI"]["Pillars"][1].keys()) == 4
    assert len(score_tree["SSPI"]["Pillars"][0]["Categories"]) == 2
    assert len(score_tree["SSPI"]["Pillars"][1]["Categories"]) == 1
    assert len(score_tree["SSPI"]["Pillars"][0]["Categories"][0].keys()) == 4
    assert len(score_tree["SSPI"]["Pillars"][0]["Categories"][1].keys()) == 4
    assert len(score_tree["SSPI"]["Pillars"][0]["Categories"][0]["Indicators"]) == 2
    assert len(score_tree["SSPI"]["Pillars"][0]["Categories"][1]["Indicators"]) == 1
