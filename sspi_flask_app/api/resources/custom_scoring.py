"""
Custom SSPI Scoring Pipeline

This module implements the core scoring logic for custom SSPI configurations:
1. Dataset preparation with imputation
2. Individual indicator scoring using validated ScoreFunctions
3. Hierarchy aggregation (Category → Pillar → SSPI)
4. Rank computation

Key Functions:
- prepare_indicator_datasets: Fetch and impute data for scoring
- score_custom_indicator: Score a single indicator
- aggregate_custom_sspi: Aggregate through hierarchy
- score_custom_configuration: Full scoring pipeline
"""

import logging
from copy import deepcopy
from collections import defaultdict
from typing import Any

from sspi_flask_app.api.resources.score_function_validator import (
    validate_score_function,
    safe_eval,
    ValidatedScoreFunction,
    ScoreFunctionValidationError,
)
from sspi_flask_app.api.resources.utilities import (
    interpolate_linear,
    extrapolate_forward,
    extrapolate_backward,
    goalpost,
    impute_dataset,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_START_YEAR = 2000
DEFAULT_END_YEAR = 2023
SSPI_COUNTRIES = 57  # Number of countries in SSPI


# =============================================================================
# Dataset Preparation
# =============================================================================

def prepare_indicator_datasets(
    indicator_code: str,
    dataset_codes: list[str],
    country_codes: list[str] | None = None,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    reference_group: str = "SSPI67"
) -> dict[str, list[dict]]:
    """
    Fetch and impute dataset values for an indicator.

    Uses the impute_dataset() function which handles:
    - Reference class averages for countries with no data
    - Backward/forward extrapolation and interpolation for partial data
    - Neutral fill (0.5) for globally empty datasets

    Args:
        indicator_code: The indicator being scored (for logging)
        dataset_codes: List of dataset codes needed
        country_codes: List of country codes to score (defaults to SSPI67)
        start_year: First year to ensure data for
        end_year: Last year to ensure data for
        reference_group: Country group for reference class averaging

    Returns:
        Dictionary mapping dataset_code -> list of imputed documents
    """
    from sspi_flask_app.models.database import sspi_metadata

    # Get country codes if not provided
    if country_codes is None:
        country_codes = sspi_metadata.country_group(reference_group) or []

    if not country_codes:
        logger.warning(f"No country codes found for reference group {reference_group}")
        return {}

    datasets = {}

    for dataset_code in dataset_codes:
        # Use the new impute_dataset() function
        imputed_dict = impute_dataset(
            dataset_code=dataset_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
            reference_group=reference_group
        )

        # Convert dict[(country,year)] -> record to list format
        imputed_list = list(imputed_dict.values())

        datasets[dataset_code] = imputed_list
        logger.debug(
            f"Prepared {len(imputed_list)} records for {dataset_code} "
            f"({start_year}-{end_year})"
        )

    return datasets


def merge_datasets_for_scoring(
    datasets: dict[str, list[dict]],
    required_codes: set[str]
) -> dict[tuple[str, int], dict[str, Any]]:
    """
    Merge multiple datasets into a lookup table for scoring.

    Args:
        datasets: Dictionary mapping dataset_code -> list of documents
        required_codes: Set of dataset codes required for scoring

    Returns:
        Dictionary mapping (CountryCode, Year) -> {dataset_code: value, ...}
        Each entry also includes "Imputed" flag if any value is imputed
    """
    merged = defaultdict(lambda: {"_imputed": False, "_imputation_methods": set()})

    for dataset_code, documents in datasets.items():
        if dataset_code not in required_codes:
            continue

        for doc in documents:
            country = doc.get("CountryCode")
            year = doc.get("Year")
            value = doc.get("Value")

            if country is None or year is None:
                continue

            key = (country, year)
            merged[key][dataset_code] = value

            # Track imputation
            if doc.get("Imputed"):
                merged[key]["_imputed"] = True
                method = doc.get("ImputationMethod")
                if method:
                    merged[key]["_imputation_methods"].add(method)

    return dict(merged)


# =============================================================================
# Indicator Scoring
# =============================================================================

def score_custom_indicator(
    indicator: dict,
    prepared_data: dict[tuple[str, int], dict[str, Any]],
    validated_function: ValidatedScoreFunction | None = None
) -> list[dict]:
    """
    Score a single indicator across all country-years.

    Args:
        indicator: Indicator metadata dict
        prepared_data: Merged dataset lookup from merge_datasets_for_scoring
        validated_function: Pre-validated score function (will validate if None)

    Returns:
        List of score documents ready for storage
    """
    indicator_code = indicator.get("ItemCode") or indicator.get("IndicatorCode")
    indicator_name = indicator.get("ItemName") or indicator.get("Indicator", indicator_code)
    score_function_str = indicator.get("ScoreFunction")

    if not score_function_str:
        logger.warning(f"No ScoreFunction for indicator {indicator_code}")
        return []

    # Validate score function if not already done
    if validated_function is None:
        try:
            validated_function = validate_score_function(score_function_str)
        except ScoreFunctionValidationError as e:
            logger.error(f"Invalid ScoreFunction for {indicator_code}: {e}")
            return []

    # Get goalpost values if used as variables
    lower_goalpost = indicator.get("LowerGoalpost")
    upper_goalpost = indicator.get("UpperGoalpost")

    scores = []
    required_datasets = validated_function.dataset_codes

    for (country, year), data_row in prepared_data.items():
        # Check if all required datasets are present
        missing = required_datasets - set(data_row.keys())
        if missing:
            # Skip this country-year - missing data
            continue

        # Extract dataset values
        dataset_values = {
            code: data_row[code]
            for code in required_datasets
            if code in data_row and data_row[code] is not None
        }

        # Skip if any required value is None
        if len(dataset_values) != len(required_datasets):
            continue

        try:
            score = safe_eval(
                validated_function,
                dataset_values,
                lower_goalpost=lower_goalpost,
                upper_goalpost=upper_goalpost
            )

            # Clamp score to valid range [0, 1]
            score = max(0.0, min(1.0, score))

            scores.append({
                "item_code": indicator_code,
                "item_name": indicator_name,
                "item_type": "Indicator",
                "country_code": country,
                "year": year,
                "score": score * 100,  # Convert to 0-100 scale
                "imputed": data_row.get("_imputed", False),
                "imputation_method": (
                    ",".join(sorted(data_row.get("_imputation_methods", set())))
                    or None
                ),
            })

        except Exception as e:
            logger.warning(
                f"Scoring failed for {indicator_code}/{country}/{year}: {e}"
            )
            continue

    logger.info(f"Scored {len(scores)} records for indicator {indicator_code}")
    return scores


def score_indicators_batch(
    indicators: list[dict],
    country_codes: list[str] | None = None,
    reference_group: str = "SSPI67",
    progress_callback=None
) -> dict[str, list[dict]]:
    """
    Score multiple indicators efficiently.

    Args:
        indicators: List of indicator metadata dicts
        country_codes: List of country codes to score (defaults to SSPI67)
        reference_group: Country group for reference class averaging
        progress_callback: Optional callback(indicator_code, index, total)

    Returns:
        Dictionary mapping indicator_code -> list of score documents
    """
    from sspi_flask_app.models.database import sspi_metadata

    all_scores = {}
    total = len(indicators)

    # Get country codes if not provided
    if country_codes is None:
        country_codes = sspi_metadata.country_group(reference_group) or []

    if not country_codes:
        logger.warning(f"No country codes found for reference group {reference_group}")
        return all_scores

    # Collect all required datasets
    all_dataset_codes = set()
    for ind in indicators:
        codes = ind.get("DatasetCodes", [])
        if codes:
            all_dataset_codes.update(codes)

    if not all_dataset_codes:
        logger.warning("No dataset codes found in indicators")
        return all_scores

    # Fetch and prepare all datasets at once
    logger.info(f"Preparing {len(all_dataset_codes)} datasets for {total} indicators")
    datasets = {}
    for code in all_dataset_codes:
        datasets.update(
            prepare_indicator_datasets(
                "batch", [code],
                country_codes=country_codes,
                reference_group=reference_group
            )
        )

    # Score each indicator
    for i, indicator in enumerate(indicators):
        indicator_code = indicator.get("ItemCode") or indicator.get("IndicatorCode")

        if progress_callback:
            progress_callback(indicator_code, i, total)

        # Get datasets required for this indicator
        required_codes = set(indicator.get("DatasetCodes", []))
        if not required_codes:
            logger.warning(f"No DatasetCodes for indicator {indicator_code}")
            continue

        # Merge datasets for this indicator
        indicator_datasets = {
            code: datasets.get(code, [])
            for code in required_codes
        }
        merged_data = merge_datasets_for_scoring(indicator_datasets, required_codes)

        # Score the indicator
        scores = score_custom_indicator(indicator, merged_data)
        all_scores[indicator_code] = scores

    return all_scores


# =============================================================================
# Hierarchy Aggregation
# =============================================================================

def aggregate_custom_sspi(
    metadata: list[dict],
    indicator_scores: dict[str, list[dict]]
) -> dict[str, list[dict]]:
    """
    Aggregate indicator scores through SSPI hierarchy.

    Computes:
    - Category scores (average of child indicators)
    - Pillar scores (average of child categories)
    - SSPI score (average of pillars)

    Args:
        metadata: Custom SSPI metadata structure
        indicator_scores: Dict mapping indicator_code -> list of score docs

    Returns:
        Dict mapping item_code -> list of score documents
        Includes: Indicators, Categories, Pillars, SSPI
    """
    # Build lookup tables
    items_by_code = {
        item.get("ItemCode"): item
        for item in metadata
    }

    # Find the SSPI root
    sspi_root = next(
        (item for item in metadata if item.get("ItemType") == "SSPI"),
        None
    )

    if not sspi_root:
        logger.error("No SSPI root found in metadata")
        return indicator_scores

    # Build aggregation from bottom up
    all_scores = dict(indicator_scores)

    # Collect all (country, year) combinations from indicator scores
    country_years = set()
    for scores_list in indicator_scores.values():
        for score_doc in scores_list:
            country_years.add((score_doc["country_code"], score_doc["year"]))

    # Score categories
    category_scores = {}
    for item in metadata:
        if item.get("ItemType") != "Category":
            continue

        category_code = item.get("ItemCode")
        category_name = item.get("ItemName", category_code)
        child_codes = item.get("IndicatorCodes") or item.get("Children", [])

        scores = _aggregate_children(
            category_code,
            category_name,
            "Category",
            child_codes,
            indicator_scores,
            country_years
        )
        category_scores[category_code] = scores
        all_scores[category_code] = scores

    # Score pillars
    pillar_scores = {}
    for item in metadata:
        if item.get("ItemType") != "Pillar":
            continue

        pillar_code = item.get("ItemCode")
        pillar_name = item.get("ItemName", pillar_code)
        child_codes = item.get("CategoryCodes") or item.get("Children", [])

        scores = _aggregate_children(
            pillar_code,
            pillar_name,
            "Pillar",
            child_codes,
            category_scores,
            country_years
        )
        pillar_scores[pillar_code] = scores
        all_scores[pillar_code] = scores

    # Score SSPI root
    sspi_code = sspi_root.get("ItemCode", "SSPI")
    sspi_name = sspi_root.get("ItemName", "SSPI")
    child_codes = sspi_root.get("PillarCodes") or sspi_root.get("Children", [])

    sspi_scores = _aggregate_children(
        sspi_code,
        sspi_name,
        "SSPI",
        child_codes,
        pillar_scores,
        country_years
    )
    all_scores[sspi_code] = sspi_scores

    return all_scores


def _aggregate_children(
    item_code: str,
    item_name: str,
    item_type: str,
    child_codes: list[str],
    child_scores: dict[str, list[dict]],
    country_years: set[tuple[str, int]]
) -> list[dict]:
    """
    Aggregate scores from children for a single parent item.

    Args:
        item_code: Code of the parent item
        item_name: Name of the parent item
        item_type: Type of the parent (Category, Pillar, SSPI)
        child_codes: List of child item codes
        child_scores: Dict mapping child_code -> list of score docs
        country_years: Set of (country, year) tuples to score

    Returns:
        List of score documents for the parent item
    """
    scores = []

    # Build lookup for child scores by (country, year)
    child_lookup = defaultdict(dict)
    for child_code in child_codes:
        child_docs = child_scores.get(child_code, [])
        for doc in child_docs:
            key = (doc["country_code"], doc["year"])
            child_lookup[key][child_code] = doc["score"]

    # Aggregate for each country-year
    for country, year in country_years:
        key = (country, year)
        available_scores = child_lookup.get(key, {})

        if not available_scores:
            continue

        # Compute average of available children
        child_values = list(available_scores.values())
        avg_score = sum(child_values) / len(child_values)

        # Track if any child was imputed
        any_imputed = any(
            doc.get("imputed", False)
            for child_code in child_codes
            for doc in child_scores.get(child_code, [])
            if doc.get("country_code") == country and doc.get("year") == year
        )

        scores.append({
            "item_code": item_code,
            "item_name": item_name,
            "item_type": item_type,
            "country_code": country,
            "year": year,
            "score": avg_score,
            "imputed": any_imputed,
            "imputation_method": None,
        })

    return scores


# =============================================================================
# Rank Computation
# =============================================================================

def compute_ranks(
    all_scores: dict[str, list[dict]]
) -> dict[str, list[dict]]:
    """
    Compute ranks for all items by country within each year.

    Higher scores get better (lower) ranks.

    Args:
        all_scores: Dict mapping item_code -> list of score docs

    Returns:
        Same structure with 'rank' field added to each document
    """
    ranked_scores = {}

    for item_code, score_docs in all_scores.items():
        # Group by year
        by_year = defaultdict(list)
        for doc in score_docs:
            by_year[doc["year"]].append(doc)

        ranked_docs = []
        for year, year_docs in by_year.items():
            # Sort by score descending (higher score = better = rank 1)
            sorted_docs = sorted(
                year_docs,
                key=lambda d: d.get("score") or 0,
                reverse=True
            )

            # Assign ranks
            for rank, doc in enumerate(sorted_docs, start=1):
                doc_copy = dict(doc)
                doc_copy["rank"] = rank
                ranked_docs.append(doc_copy)

        ranked_scores[item_code] = ranked_docs

    return ranked_scores


# =============================================================================
# Full Scoring Pipeline
# =============================================================================

def score_custom_configuration(
    metadata: list[dict],
    modified_indicators: set[str] | None = None,
    default_scores: dict[str, list[dict]] | None = None,
    country_codes: list[str] | None = None,
    reference_group: str = "SSPI67",
    progress_callback=None
) -> dict[str, list[dict]]:
    """
    Full scoring pipeline for a custom configuration.

    Args:
        metadata: Custom SSPI metadata structure
        modified_indicators: Set of indicator codes that need scoring
                           (if None, scores all indicators)
        default_scores: Pre-computed scores for unchanged indicators
        country_codes: List of country codes to score (defaults to SSPI67)
        reference_group: Country group for reference class averaging
        progress_callback: Optional callback(phase, percent, message)

    Returns:
        Dict mapping item_code -> list of ranked score documents
    """
    # Extract indicators to score
    all_indicators = [
        item for item in metadata
        if item.get("ItemType") == "Indicator"
    ]

    if modified_indicators is not None:
        indicators_to_score = [
            ind for ind in all_indicators
            if ind.get("ItemCode") in modified_indicators
        ]
    else:
        indicators_to_score = all_indicators

    logger.info(
        f"Scoring {len(indicators_to_score)}/{len(all_indicators)} indicators"
    )
    if progress_callback:
        progress_callback("scoring", 10, f"Scoring {len(indicators_to_score)} indicators...")
    indicator_scores = score_indicators_batch(
        indicators_to_score,
        country_codes=country_codes,
        reference_group=reference_group,
        progress_callback=lambda code, i, total: (
            progress_callback(
                "scoring",
                10 + int(60 * i / total),
                f"Scoring {code} ({i+1}/{total})..."
            ) if progress_callback else None
        )
    )
    # Merge with default scores for unchanged indicators
    if default_scores:
        for ind in all_indicators:
            code = ind.get("ItemCode")
            if code not in indicator_scores and code in default_scores:
                indicator_scores[code] = default_scores[code]
    # Progress: aggregation phase
    if progress_callback:
        progress_callback("aggregation", 75, "Aggregating hierarchy...")
    # Aggregate through hierarchy
    all_scores = aggregate_custom_sspi(metadata, indicator_scores)

    # Progress: ranking phase
    if progress_callback:
        progress_callback("ranking", 90, "Computing ranks...")

    # Compute ranks
    ranked_scores = compute_ranks(all_scores)

    # Progress: complete
    if progress_callback:
        total_docs = sum(len(docs) for docs in ranked_scores.values())
        progress_callback("complete", 100, f"Scored {total_docs} records")

    return ranked_scores


def flatten_scores_for_storage(
    all_scores: dict[str, list[dict]]
) -> list[dict]:
    """
    Flatten nested score dictionary into a flat list for database storage.

    Args:
        all_scores: Dict mapping item_code -> list of score docs

    Returns:
        Flat list of all score documents
    """
    flat_list = []
    for scores in all_scores.values():
        flat_list.extend(scores)
    return flat_list
