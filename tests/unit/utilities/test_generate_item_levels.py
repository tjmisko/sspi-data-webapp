from sspi_flask_app.api.resources.utilities import generate_item_levels


def test_generate_item_levels_default_keys():
    data = [
        {
            "CountryCode": "CAN", "ItemCode": "SENLEM", "SEX": "M", "Value": 80.9, "Year": 2022
        },
        {
            "CountryCode": "CAN", "ItemCode": "SENLEM", "SEX": "F", "Value": 84.8, "Year": 2022
        },
        {
            "CountryCode": "DEU", "ItemCode": "SENLEM", "SEX": "M", "Value": 78.5, "Year": 2022
        },
        {
            "CountryCode": "DEU", "ItemCode": "SENLEM", "SEX": "F", "Value": 83.5, "Year": 2022
        }
    ]
    levels = generate_item_levels(data)
    assert len(levels) == 2
    assert all("ItemCode" in d for d in levels)
    assert all("SEX" in d for d in levels)
    assert all("CountryCode" not in d for d in levels)  # excluded by default
    assert all("Value" not in d for d in levels)
    assert all("Year" not in d for d in levels)


def test_generate_item_levels_exclude_additional_field():
    data = [
        {
            "CountryCode": "CAN", "ItemCode": "SENLEM", "SEX": "M", "Value": 80.9, "Year": 2022, "Unit": "Years"
        },
        {
            "CountryCode": "CAN", "ItemCode": "SENLEM", "SEX": "M", "Value": 81.0, "Year": 2021, "Unit": "Years"
        }
    ]
    levels = generate_item_levels(data, exclude_fields=["Unit"])
    assert len(levels) == 1  # Only one unique level after excluding Unit
    assert "Unit" not in levels[0]


def test_generate_item_levels_custom_keys():
    data = [
        {
            "REF_AREA": "CAN", "ItemCode": "SENLEM", "SEX": "M", "VAL": 80.9, "TIME": 2022
        },
        {
            "REF_AREA": "CAN", "ItemCode": "SENLEM", "SEX": "F", "VAL": 84.8, "TIME": 2022
        }
    ]
    levels = generate_item_levels(
        data, entity_id="REF_AREA", value_id="VAL", time_id="TIME")
    assert len(levels) == 2
    assert all("ItemCode" in d and "SEX" in d for d in levels)
    assert all(
        "VAL" not in d and "TIME" not in d and "REF_AREA" not in d for d in levels)


def test_generate_item_levels_duplicate_records_ignored():
    data = [
        {"CountryCode": "CAN", "ItemCode": "SENLEM",
            "SEX": "M", "Value": 80.9, "Year": 2022},
        {"CountryCode": "CAN", "ItemCode": "SENLEM",
            "SEX": "M", "Value": 81.0, "Year": 2023}
    ]
    levels = generate_item_levels(data)
    assert len(levels) == 1  # Same non-excluded fields, considered same level


def test_generate_item_levels_handles_empty_list():
    levels = generate_item_levels([])
    assert levels == []


def test_generate_item_levels_ignores_list_values():
    data = [
        {"CountryCode": "CAN", "ItemCode": "SENLEM",
            "Value": 80.9, "Year": 2022, "Tags": ["LE", "Health"]}
    ]
    levels = generate_item_levels(data)
    assert len(levels) == 1
    assert "Tags" not in levels[0]
