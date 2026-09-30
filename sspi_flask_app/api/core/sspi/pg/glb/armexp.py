from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)

ARMEXP_PANEL_START_YEAR = 2000
ARMEXP_PANEL_END_YEAR = 2023


def build_armexp_score_function(lower_goalpost, upper_goalpost):
    """Score function bound by name to the SIPRI_ARMEXP dataset code."""
    return lambda SIPRI_ARMEXP: goalpost(SIPRI_ARMEXP, lower_goalpost, upper_goalpost)


def build_armexp_imputations(
    clean_armexp: list[dict],
    start_year: int = ARMEXP_PANEL_START_YEAR,
    end_year: int = ARMEXP_PANEL_END_YEAR,
) -> list[dict]:
    """
    Edge extrapolations only. The SIPRI_ARMEXP cleaner records blank cells
    and SSPI countries absent from the exporter table as observed 0 TIV
    (owner ruling 2026-09-13), so every series is dense over the years SIPRI
    reports and no interpolation or reference-class fill is needed. A carry
    is produced only when the SIPRI table itself ends before end_year or
    starts after start_year; each carried row discloses its
    ImputationDistance.
    """
    series_id = ["CountryCode", "DatasetCode"]
    forward = extrapolate_forward(clean_armexp, end_year, series_id, impute_only=True)
    backward = extrapolate_backward(clean_armexp, start_year, series_id, impute_only=True)
    return forward + backward


def missing_armexp_cells(
    indicator_docs: list[dict],
    country_codes: list[str],
    start_year: int = ARMEXP_PANEL_START_YEAR,
    end_year: int = ARMEXP_PANEL_END_YEAR,
) -> list[tuple[str, int]]:
    """(CountryCode, Year) cells in the panel window with no ARMEXP row."""
    present_cells = {(doc["CountryCode"], doc["Year"]) for doc in indicator_docs}
    return [
        (country_code, year)
        for country_code in country_codes
        for year in range(start_year, end_year + 1)
        if (country_code, year) not in present_cells
    ]


@compute_bp.route("/ARMEXP", methods=['POST'])
@admin_required
def compute_armexp():
    app.logger.info("Running /api/v1/compute/ARMEXP")
    sspi_indicator_data.delete_many({"IndicatorCode": "ARMEXP"})
    clean_armexp = sspi_clean_api_data.find({"DatasetCode": "SIPRI_ARMEXP"})
    lg, ug = sspi_metadata.get_goalposts("ARMEXP")
    scored_list, _ = score_indicator(
        clean_armexp, "ARMEXP",
        score_function=build_armexp_score_function(lg, ug),
        unit="Expenditure"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/ARMEXP", methods=['POST'])
@admin_required
def impute_armexp():
    app.logger.info("Running /api/v1/impute/ARMEXP")
    sspi_imputed_data.delete_many({"IndicatorCode": "ARMEXP"})
    clean_armexp = sspi_clean_api_data.find({"DatasetCode": "SIPRI_ARMEXP"})
    lg, ug = sspi_metadata.get_goalposts("ARMEXP")
    imputed_armexp, _ = score_indicator(
        build_armexp_imputations(clean_armexp), "ARMEXP",
        score_function=build_armexp_score_function(lg, ug),
        unit="Expenditure"
    )
    observed_armexp = sspi_indicator_data.find({"IndicatorCode": "ARMEXP"})
    uncovered_cells = missing_armexp_cells(
        observed_armexp + imputed_armexp, sspi_metadata.country_group("SSPI67")
    )
    if uncovered_cells:
        app.logger.warning(
            f"ARMEXP: {len(uncovered_cells)} SSPI67 country-years in "
            f"{ARMEXP_PANEL_START_YEAR}-{ARMEXP_PANEL_END_YEAR} have no row; "
            f"re-run `sspi clean SIPRI_ARMEXP` and `sspi compute ARMEXP` "
            f"(first missing: {uncovered_cells[:5]})"
        )
    app.logger.info(f"ARMEXP: {len(imputed_armexp)} edge extrapolations imputed")
    if imputed_armexp:
        sspi_imputed_data.insert_many(imputed_armexp)
    return parse_json(imputed_armexp)
