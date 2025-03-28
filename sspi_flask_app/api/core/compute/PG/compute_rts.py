from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)
import pandas as pd

@compute_bp.route("/EDEMOC", methods=['GET'])
@login_required
def compute_edemoc():
    if not sspi_raw_api_data.raw_data_available("EDEMOC"):
        return redirect(url_for("collect_bp.EDEMOC"))
    raw_data = sspi_raw_api_data.fetch_raw_data("EDEMOC")
    fragments = []
    for obs in raw_data:
        try:
            fragment_num = obs.get("FragmentNumber")
            csv_fragment = obs.get("Raw", {}).get("csv_fragment", "")
            if fragment_num is not None and csv_fragment:
                fragments.append((fragment_num, csv_fragment))
        except Exception as e:
            continue

    if not fragments:
        return "No CSV fragments found for EDEMOC."
    fragments.sort(key=lambda x: x[0])
    full_csv = "".join(fragment for _, fragment in fragments)
    try:
        df = pd.read_csv(StringIO(full_csv))
    except Exception as e:
        return f"Error reading CSV data: {e}"
    filtered_df = df[['country_text_id', 'year', 'v2x_polyarchy']]
    filtered_df = df[(df["year"] > 1900) & (df["year"] < 2030)]
    # Identify year columns. If none are found (since 'year' is already present), we use the existing 'year'.
    year_columns = [col for col in filtered_df.columns if col.isdigit()]
    id_vars = [col for col in filtered_df.columns if col not in year_columns]
    if year_columns:
        df_melted = filtered_df.melt(
            id_vars=id_vars,
            value_vars=year_columns,
            var_name="Year",
            value_name="Value"
        )
        df_melted["Year"] = df_melted["Year"].astype(int)
    else:
        df_melted = filtered_df.rename(columns={"year": "Year", "v2x_polyarchy": "Value"})
        df_melted["Year"] = df_melted["Year"].astype(int)

    df_sorted = df_melted.sort_values(by=["country_text_id", "Year"])
    df_sorted["CountryCode"] = df_sorted["country_text_id"]
    df_sorted["Unit"] = ""
    df_sorted["IndicatorCode"] = "EDEMOC"
    df_final = df_sorted[["CountryCode", "Year", "Value", "Unit", "IndicatorCode"]]
    records = df_final.to_dict(orient="records")
    scored_list = score_single_indicator(records, "EDEMOC")
    filtered_list, incomplete_observations = filter_incomplete_data(
         scored_list)
    sspi_clean_api_data.insert_many(filtered_list)

    return parse_json(filtered_list)

