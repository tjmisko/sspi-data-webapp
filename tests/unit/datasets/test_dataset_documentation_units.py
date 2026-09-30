from pathlib import Path

import frontmatter
import pytest

DATASETS_ROOT = Path(__file__).resolve().parents[3] / "datasets"

IEA_TOTAL_ENERGY_SUPPLY_DOCS = [
    "iea/iea_biowas",
    "iea/iea_fsloil",
    "iea/iea_geopwr",
    "iea/iea_hydrop",
    "iea/iea_natgas",
    "iea/iea_nclear",
    "iea/iea_tlcoal",
]


def load_metadata(relative_dir):
    return frontmatter.load(DATASETS_ROOT / relative_dir / "documentation.md").metadata


@pytest.mark.parametrize("relative_dir", IEA_TOTAL_ENERGY_SUPPLY_DOCS)
def test_should_describe_terajoules_of_supply_when_iea_tesbysource_unit_is_tj(relative_dir):
    # Raw TESbySource rows carry flowLabel "Total energy supply" and units "TJ".
    metadata = load_metadata(relative_dir)
    assert metadata["Unit"] == "TJ"
    assert "Total energy supply" in metadata["Description"]
    assert "terajoules" in metadata["Description"]
    assert "Percentage" not in metadata["Description"]


def test_should_state_total_kilograms_when_tco2em_is_mt_times_1e9():
    # Raw CO2BySector units are "Mt CO2"; the cleaner stores value * 1e9 (kg), not per inhabitant.
    metadata = load_metadata("iea/iea_tco2em")
    assert metadata["Unit"] == "kg CO2"
    assert "per inhabitant" not in metadata["Unit"]
    assert "kilograms of CO2" in metadata["Description"]


@pytest.mark.parametrize("relative_dir", ["unfao/unfao_crbnav", "unfao/unfao_crbnlv"])
def test_should_state_million_tonnes_when_fao_carbon_stock_unit_is_million_t(relative_dir):
    # Raw FAO RL element 7215 rows carry Unit "million t".
    metadata = load_metadata(relative_dir)
    assert metadata["Unit"].startswith("million t")
    assert "million tonnes" in metadata["Description"]
    assert "kg" not in metadata["Description"]


@pytest.mark.parametrize("relative_dir", ["unfao/unfao_frstav", "unfao/unfao_frstlv"])
def test_should_state_thousand_hectares_when_fao_forest_area_unit_is_1000_ha(relative_dir):
    # Raw FAO RL element 5110 rows carry Unit "1000 ha".
    metadata = load_metadata(relative_dir)
    assert metadata["Unit"].startswith("1000 ha")
    assert "1000 ha" in metadata["Description"]


def test_should_state_micrograms_of_pm25_only_when_airpol_series_is_en_atm_pm25():
    metadata = load_metadata("unsdg/unsdg_airpol")
    assert metadata["Unit"] == "μg/m^3"
    assert "PM2.5" in metadata["Description"]
    assert "PM10" not in metadata["Description"]
