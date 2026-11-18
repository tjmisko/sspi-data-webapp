#!/usr/bin/env python
"""
Parity guard for custom scoring (read-only).

Scores the unedited default SSPI structure through the custom fast pipeline
(change detection must report 0 modified indicators, so every indicator row
comes from the official scores) and compares the SSPI, pillar and category
scores with the official scores in sspi_item_data for the SSPI67 countries and
all years.

Usage (from the repository root, with the dev MongoDB reachable):
    python scripts/check_custom_scoring_parity.py [--tolerance 1e-6]

Exits non-zero when any level differs by more than the tolerance, when change
detection finds modified indicators, or when an official score has no custom
counterpart. Never writes to the database.
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

LEVELS = ("Indicator", "Category", "Pillar", "SSPI")


def run(tolerance: float) -> int:
    from config import DevConfig
    from sspi_flask_app import init_app

    app = init_app(DevConfig)
    with app.app_context():
        from sspi_flask_app.models.database import sspi_item_data, sspi_metadata
        from sspi_flask_app.api.resources.change_detection import (
            identify_modified_indicators,
        )
        from sspi_flask_app.api.resources.custom_scoring import (
            DEFAULT_END_YEAR,
            DEFAULT_START_YEAR,
        )
        from sspi_flask_app.api.resources.fast_custom_scoring import (
            score_custom_configuration_fast,
        )

        # Same source as GET /api/v1/customize/default-structure
        metadata = sspi_metadata.item_details()
        countries = sspi_metadata.country_group("SSPI67")
        detection = identify_modified_indicators(metadata)
        print(f"Change detection: {len(detection.modified_indicators)} modified, "
              f"{len(detection.unchanged_indicators)} unchanged "
              f"(default_available={detection.default_available})")
        failed = bool(detection.modified_indicators) or not detection.default_available

        result = score_custom_configuration_fast(
            metadata,
            modified_indicators=detection.modified_indicators,
            country_codes=countries,
            start_year=DEFAULT_START_YEAR,
            end_year=DEFAULT_END_YEAR,
        )
        custom = {}
        item_type = {}
        for code, docs in result.items():
            for doc in docs:
                custom[(code, doc["country_code"], doc["year"])] = doc["score"] / 100.0
                item_type[code] = doc["item_type"]

        official = {}
        official_type = {}
        cursor = sspi_item_data.find(
            {"CountryCode": {"$in": countries},
             "Year": {"$gte": DEFAULT_START_YEAR, "$lte": DEFAULT_END_YEAR}},
            {"_id": 0, "ItemCode": 1, "ItemType": 1, "CountryCode": 1,
             "Year": 1, "Score": 1},
        )
        for doc in cursor:
            if doc.get("Score") is None:
                continue
            key = (doc["ItemCode"], doc["CountryCode"], doc["Year"])
            official[key] = float(doc["Score"])
            official_type[doc["ItemCode"]] = doc.get("ItemType")

        max_diff = defaultdict(float)
        worst = {}
        compared = defaultdict(int)
        missing_in_custom = defaultdict(list)
        for key, want in official.items():
            level = official_type.get(key[0])
            got = custom.get(key)
            if got is None:
                missing_in_custom[level].append(key)
                continue
            compared[level] += 1
            diff = abs(got - want)
            if diff > max_diff[level]:
                max_diff[level] = diff
                worst[level] = (key, want, got)
        extra_in_custom = defaultdict(int)
        for key in custom:
            if key not in official:
                extra_in_custom[item_type.get(key[0])] += 1

        print(f"\n{'level':<10} {'compared':>9} {'max abs diff':>14} "
              f"{'missing in custom':>18} {'extra in custom':>16}")
        for level in LEVELS:
            print(f"{level:<10} {compared[level]:>9} {max_diff[level]:>14.3e} "
                  f"{len(missing_in_custom[level]):>18} {extra_in_custom[level]:>16}")
            if max_diff[level] > tolerance or missing_in_custom[level]:
                failed = True
            if level in worst and max_diff[level] > tolerance:
                key, want, got = worst[level]
                print(f"    worst: {key} official={want:.8f} custom={got:.8f}")
            for key in missing_in_custom[level][:5]:
                print(f"    missing in custom: {key}")

        print("\nPARITY FAILED" if failed else "\nPARITY OK")
        return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tolerance", type=float, default=1e-6)
    sys.exit(run(parser.parse_args().tolerance))
