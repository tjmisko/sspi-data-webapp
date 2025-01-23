from sspi_flask_app.models.rank import SSPIRankingTable
import pytest


@pytest.fixture()
def test_country_score_data():
    yield [
        {
            "IndicatorCode": "BIODIV",
            "CountryCode": "AUS",
            "Value": 15.0,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.15
        },
        {
            "IndicatorCode": "REDLST",
            "CountryCode": "AUS",
            "Value": 90,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.90
        },
        {
            "IndicatorCode": "STKHLM",
            "CountryCode": "AUS",
            "Value": 72,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.72
        },
        {
            "IndicatorCode": "UNEMPL",
            "CountryCode": "AUS",
            "Value": 50.0,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.50
        },
        {
            "IndicatorCode": "CHILDW",
            "CountryCode": "AUS",
            "Value": 50,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.50
        },
        {
            "IndicatorCode": "LFPART",
            "CountryCode": "AUS",
            "Value": 50,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.50
        },
        {
            "IndicatorCode": "PRISON",
            "CountryCode": "AUS",
            "Value": 15.0,
            "LowerGoalpost": 0,
            "UpperGoalpost": 100,
            "Year": 2018,
            "Score": 0.15
        }
    ]


def test_basic_rankings(test_country_score_data):
    rankings = SSPIRankingTable(test_country_score_data[0:4])
    assert len(rankings.classes) == 4
    assert all([len(rankings.classes[x].data) == 1 for x in range(4)])
    assert rankings.classes[0].value == 90
    assert rankings.classes[0].data[0]["Rank"] == 1
    assert rankings.classes[1].value == 72
    assert rankings.classes[1].data[0]["Rank"] == 2
    assert rankings.classes[2].value == 50
    assert rankings.classes[2].data[0]["Rank"] == 3
    assert rankings.classes[3].value == 15
    assert rankings.classes[3].data[0]["Rank"] == 4


def test_ranking_under_switched_goalposts(test_country_score_data):
    data = list(test_country_score_data[0:4])
    for obs in data:
        lg = obs["LowerGoalpost"]
        obs["LowerGoalpost"] = obs["UpperGoalpost"]
        obs["UpperGoalpost"] = lg
    rankings = SSPIRankingTable(data)
    assert len(rankings.classes) == 4
    assert all([len(rankings.classes[x].data) == 1 for x in range(4)])
    assert rankings.classes[0].value == 15
    assert rankings.classes[0].data[0]["Rank"] == 1
    assert rankings.classes[1].value == 50
    assert rankings.classes[1].data[0]["Rank"] == 2
    assert rankings.classes[2].value == 72
    assert rankings.classes[2].data[0]["Rank"] == 3
    assert rankings.classes[3].value == 90
    assert rankings.classes[3].data[0]["Rank"] == 4


def test_ranking_standard_ties(test_country_score_data):
    rankings = SSPIRankingTable(test_country_score_data[0:6])
    assert rankings.classes[0].value == 90
    assert rankings.classes[0].data[0]["Rank"] == 1
    assert rankings.classes[1].value == 72
    assert rankings.classes[1].data[0]["Rank"] == 2
    assert rankings.classes[2].value == 50
    assert len(rankings.classes[2].data) == 3
    assert rankings.classes[2].data[0]["Rank"] == 3
    assert rankings.classes[2].data[1]["Rank"] == 3
    assert rankings.classes[2].data[2]["Rank"] == 3
    assert rankings.classes[3].value == 15
    assert rankings.classes[3].data[0]["Rank"] == 6


def test_ranking_end_ties(test_country_score_data):
    rankings = SSPIRankingTable(test_country_score_data)
    assert len(rankings.classes) == 4
    assert rankings.classes[0].value == 90
    assert rankings.classes[0].data[0]["Rank"] == 1
    assert rankings.classes[1].value == 72
    assert rankings.classes[1].data[0]["Rank"] == 2
    assert rankings.classes[2].value == 50
    assert len(rankings.classes[2].data) == 3
    assert rankings.classes[2].data[0]["Rank"] == 3
    assert rankings.classes[2].data[1]["Rank"] == 3
    assert rankings.classes[2].data[2]["Rank"] == 3
    assert rankings.classes[3].value == 15
    assert len(rankings.classes[3].data) == 2
    assert rankings.classes[3].data[0]["Rank"] == 7
    assert rankings.classes[3].data[0]["Rank"] == 7
