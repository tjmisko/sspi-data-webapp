"""
Fast Custom SSPI Scoring Pipeline

This module implements a high-performance scoring pipeline using:
1. MongoDB aggregation for efficient data fetching
2. NumPy vectorized operations for imputation and scoring
3. Matrix multiplication for hierarchy aggregation

Key Components:
- fetch_all_datasets_aggregated: Single-query data fetch
- impute_dataset_vectorized: NumPy-based imputation
- FastCustomSSPI: Matrix-based hierarchy aggregation
- score_indicators_vectorized: Vectorized indicator scoring
- score_custom_configuration_fast: Main pipeline entry point
"""

import logging
import numpy as np
from typing import Callable

from sspi_flask_app.models.database import sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.score_function_validator import (
    validate_score_function,
    safe_eval,
    ValidatedScoreFunction,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

DEFAULT_START_YEAR = 2000
DEFAULT_END_YEAR = 2023


# =============================================================================
# Phase 1: Data Fetching Infrastructure
# =============================================================================

def fetch_all_datasets_aggregated(
    dataset_codes: list[str],
    country_codes: list[str],
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR
) -> dict[str, np.ndarray]:
    """
    Fetch all datasets in one MongoDB aggregation query.

    Uses a single aggregation pipeline to fetch all requested datasets,
    avoiding N separate queries.

    Args:
        dataset_codes: List of dataset codes to fetch
        country_codes: List of country codes to include
        start_year: Start of year range (inclusive)
        end_year: End of year range (inclusive)

    Returns:
        Dict mapping dataset_code -> array of shape (n_countries, n_years)
        Arrays contain np.nan for missing values.
    """
    if not dataset_codes:
        logger.warning("fetch_all_datasets_aggregated called with empty dataset_codes")
        return {}

    if not country_codes:
        logger.warning("fetch_all_datasets_aggregated called with empty country_codes")
        return {}

    n_countries = len(country_codes)
    n_years = end_year - start_year + 1

    # Create index mappings for efficient array placement
    country_to_idx = {code: idx for idx, code in enumerate(country_codes)}
    dataset_to_idx = {code: idx for idx, code in enumerate(dataset_codes)}

    logger.info(f"Fetching {len(dataset_codes)} datasets for {n_countries} countries, years {start_year}-{end_year}")

    # MongoDB aggregation pipeline
    pipeline = [
        {
            "$match": {
                "DatasetCode": {"$in": dataset_codes},
                "CountryCode": {"$in": country_codes},
                "Year": {"$gte": start_year, "$lte": end_year}
            }
        },
        {
            "$project": {
                "_id": 0,
                "DatasetCode": 1,
                "CountryCode": 1,
                "Year": 1,
                "Value": 1
            }
        }
    ]

    # Execute query
    cursor = sspi_clean_api_data.aggregate(pipeline)

    # Initialize result arrays with NaN
    result = {
        ds_code: np.full((n_countries, n_years), np.nan, dtype=float)
        for ds_code in dataset_codes
    }

    # Fill arrays with fetched data
    for doc in cursor:
        ds_code = doc.get("DatasetCode")
        country_code = doc.get("CountryCode")
        year = doc.get("Year")
        value = doc.get("Value")

        # Skip if missing required fields or value is None
        if ds_code is None or country_code is None or year is None or value is None:
            continue

        # Get array indices
        country_idx = country_to_idx.get(country_code)
        year_idx = year - start_year

        # Skip if indices out of bounds
        if country_idx is None or year_idx < 0 or year_idx >= n_years:
            continue

        # Place value in appropriate array
        result[ds_code][country_idx, year_idx] = float(value)

    logger.info(f"Fetched data for {len(result)} datasets")

    return result


def impute_dataset_vectorized(
    data: np.ndarray,
    reference_mask: np.ndarray,
    neutral_fill: float = 0.5
) -> tuple[np.ndarray, np.ndarray]:
    """
    Vectorized imputation for a dataset array.

    Handles three scenarios:
    1. Entire dataset empty: fill with neutral_fill (0.5)
    2. Country has no data: use reference class average
    3. Country has partial data: forward/backward extrapolation

    Args:
        data: Array of shape (n_countries, n_years), may contain np.nan
        reference_mask: Boolean array indicating reference group countries
        neutral_fill: Value to use when no data exists (default 0.5)

    Returns:
        Tuple of:
        - imputed_data: Array with all np.nan replaced
        - imputation_flags: Boolean array, True where imputation occurred
    """
    n_countries, n_years = data.shape
    imputed_data = data.copy()
    imputation_flags = np.isnan(data)

    # Scenario 1: Entire dataset is empty
    if np.all(np.isnan(data)):
        logger.debug("Entire dataset empty, filling with neutral value")
        imputed_data.fill(neutral_fill)
        return imputed_data, imputation_flags

    # Scenario 2: Countries with no data at all - use reference class average
    has_data_per_country = ~np.all(np.isnan(data), axis=1)  # True if country has any data
    no_data_countries = ~has_data_per_country

    if np.any(no_data_countries):
        # Compute reference class average across all years
        reference_data = data[reference_mask, :]
        if reference_data.size > 0:
            # Average over reference countries, ignoring NaN
            reference_avg = np.nanmean(reference_data)
            if not np.isnan(reference_avg):
                imputed_data[no_data_countries, :] = reference_avg
                logger.debug(f"Filled {np.sum(no_data_countries)} countries with reference average {reference_avg:.4f}")
            else:
                # Reference group also has no data, use neutral fill
                imputed_data[no_data_countries, :] = neutral_fill
                logger.debug(f"Reference group empty, filled {np.sum(no_data_countries)} countries with neutral value")
        else:
            # No reference countries, use neutral fill
            imputed_data[no_data_countries, :] = neutral_fill
            logger.debug(f"No reference countries, filled {np.sum(no_data_countries)} countries with neutral value")

    # Scenario 3: Countries with partial data - forward/backward fill
    for country_idx in range(n_countries):
        if no_data_countries[country_idx]:
            # Already handled in scenario 2
            continue

        country_data = imputed_data[country_idx, :]
        missing_mask = np.isnan(country_data)

        if not np.any(missing_mask):
            # No missing data for this country
            continue

        # Find first and last valid indices
        valid_indices = np.where(~missing_mask)[0]
        if len(valid_indices) == 0:
            # This shouldn't happen as we checked has_data_per_country, but handle it
            continue

        first_valid = valid_indices[0]
        last_valid = valid_indices[-1]

        # Backward extrapolation: fill from start to first valid
        if first_valid > 0:
            imputed_data[country_idx, :first_valid] = country_data[first_valid]

        # Forward extrapolation: fill from last valid to end
        if last_valid < n_years - 1:
            imputed_data[country_idx, last_valid + 1:] = country_data[last_valid]

        # Linear interpolation: fill gaps between valid values
        # Find all NaN positions between first_valid and last_valid
        for year_idx in range(first_valid, last_valid + 1):
            if np.isnan(imputed_data[country_idx, year_idx]):
                # Find previous and next valid values
                prev_valid = year_idx - 1
                while prev_valid >= first_valid and np.isnan(country_data[prev_valid]):
                    prev_valid -= 1

                next_valid = year_idx + 1
                while next_valid <= last_valid and np.isnan(country_data[next_valid]):
                    next_valid += 1

                if prev_valid >= first_valid and next_valid <= last_valid:
                    # Linear interpolation
                    prev_value = country_data[prev_valid]
                    next_value = country_data[next_valid]
                    span = next_valid - prev_valid
                    weight = (year_idx - prev_valid) / span
                    imputed_data[country_idx, year_idx] = prev_value + weight * (next_value - prev_value)

    return imputed_data, imputation_flags


# =============================================================================
# Phase 2: FastCustomSSPI Class
# =============================================================================

class FastCustomSSPI:
    """
    Fast scoring for custom SSPI configurations using matrix multiplication.

    Builds a score matrix that maps indicator scores to all hierarchy levels
    (categories, pillars, SSPI) in a single matrix multiplication.

    Attributes:
        metadata: Original metadata list
        indicator_codes: Ordered list of indicator codes
        category_codes: Ordered list of category codes
        pillar_codes: Ordered list of pillar codes
        item_codes: All non-indicator codes (categories + pillars + SSPI)
        score_matrix: Matrix of shape (n_indicators, n_items)
    """

    def __init__(self, metadata: list[dict]):
        """
        Initialize FastCustomSSPI from custom metadata.

        Args:
            metadata: List of item metadata dicts with ItemType, ItemCode,
                     Children/IndicatorCodes/CategoryCodes/PillarCodes fields
        """
        self.metadata = metadata
        self.items_by_code = {item["ItemCode"]: item for item in metadata}

        # Extract ordered code lists
        self.indicator_codes = [
            item["ItemCode"] for item in metadata
            if item.get("ItemType") == "Indicator"
        ]
        self.category_codes = [
            item["ItemCode"] for item in metadata
            if item.get("ItemType") == "Category"
        ]
        self.pillar_codes = [
            item["ItemCode"] for item in metadata
            if item.get("ItemType") == "Pillar"
        ]

        # Non-indicator items in order: categories, pillars, SSPI
        self.item_codes = self.category_codes + self.pillar_codes + ["SSPI"]

        # Build the aggregation matrix
        self.score_matrix = self._build_score_matrix()

    def _build_score_matrix(self) -> np.ndarray:
        """
        Build matrix mapping indicator scores to all hierarchy levels.

        Each row represents an indicator.
        Each column represents a parent item (category, pillar, or SSPI).
        Values are the weight contribution of that indicator to each parent.

        Returns:
            Matrix of shape (n_indicators, n_categories + n_pillars + 1)
        """
        n_indicators = len(self.indicator_codes)
        n_categories = len(self.category_codes)
        n_pillars = len(self.pillar_codes)
        n_items = n_categories + n_pillars + 1

        logger.debug(
            f"Building score matrix: {n_indicators} indicators, "
            f"{n_categories} categories, {n_pillars} pillars"
        )

        score_matrix = np.zeros((n_indicators, n_items), dtype=float)

        for ind_idx, ind_code in enumerate(self.indicator_codes):
            category = self._find_parent(ind_code, "Category")
            if not category:
                logger.warning(f"Indicator {ind_code} has no parent category")
                continue

            category_code = category["ItemCode"]
            category_children = (
                category.get("IndicatorCodes") or
                category.get("Children") or
                []
            )
            n_indicators_in_category = len(category_children)

            if n_indicators_in_category == 0:
                logger.warning(f"Category {category_code} has no indicators")
                continue

            category_weight = 1.0 / n_indicators_in_category
            category_idx = self.category_codes.index(category_code)
            score_matrix[ind_idx, category_idx] = category_weight

            pillar = self._find_parent(category_code, "Pillar")
            if not pillar:
                logger.warning(f"Category {category_code} has no parent pillar")
                continue

            pillar_code = pillar["ItemCode"]
            pillar_children = (
                pillar.get("CategoryCodes") or
                pillar.get("Children") or
                []
            )
            n_categories_in_pillar = len(pillar_children)

            if n_categories_in_pillar == 0:
                logger.warning(f"Pillar {pillar_code} has no categories")
                continue

            pillar_weight = category_weight / n_categories_in_pillar
            pillar_idx = self.pillar_codes.index(pillar_code)
            score_matrix[ind_idx, n_categories + pillar_idx] = pillar_weight

            sspi = self._find_parent(pillar_code, "SSPI")
            if not sspi:
                logger.warning(f"Pillar {pillar_code} has no SSPI parent")
                continue

            sspi_children = (
                sspi.get("PillarCodes") or
                sspi.get("Children") or
                []
            )
            n_pillars_in_sspi = len(sspi_children)

            if n_pillars_in_sspi == 0:
                logger.warning("SSPI has no pillars")
                continue

            sspi_weight = pillar_weight / n_pillars_in_sspi
            sspi_idx = n_categories + n_pillars
            score_matrix[ind_idx, sspi_idx] = sspi_weight

        logger.debug(f"Score matrix built with shape {score_matrix.shape}")
        return score_matrix

    def _find_parent(self, child_code: str, parent_type: str) -> dict | None:
        """
        Find the parent item of a given type for a child code.

        Args:
            child_code: Code of the child item
            parent_type: Type of parent to find (Category, Pillar, SSPI)

        Returns:
            Parent item dict or None if not found
        """
        for item in self.metadata:
            if item.get("ItemType") != parent_type:
                continue
            children = (
                item.get("IndicatorCodes") or
                item.get("CategoryCodes") or
                item.get("PillarCodes") or
                item.get("Children") or
                []
            )
            if child_code in children:
                return item
        return None

    def aggregate(self, indicator_scores: np.ndarray) -> np.ndarray:
        """
        Aggregate indicator scores to all hierarchy levels via matrix multiplication.

        Args:
            indicator_scores: Array of shape (n_indicators, n_countries, n_years)

        Returns:
            Array of shape (n_items, n_countries, n_years)
            where n_items = n_categories + n_pillars + 1 (SSPI)
        """
        n_indicators, n_countries, n_years = indicator_scores.shape
        n_items = len(self.item_codes)

        logger.debug(
            f"Aggregating scores: {n_indicators} indicators -> {n_items} items "
            f"for {n_countries} countries, {n_years} years"
        )

        # Reshape to (n_indicators, n_countries * n_years) for matrix multiplication
        flat_scores = indicator_scores.reshape(n_indicators, n_countries * n_years)

        # Matrix multiply: score_matrix.T @ flat_scores
        # score_matrix shape: (n_indicators, n_items)
        # score_matrix.T shape: (n_items, n_indicators)
        # flat_scores shape: (n_indicators, n_countries * n_years)
        # result shape: (n_items, n_countries * n_years)
        aggregated_flat = self.score_matrix.T @ flat_scores

        # Reshape back to (n_items, n_countries, n_years)
        aggregated_scores = aggregated_flat.reshape(n_items, n_countries, n_years)

        logger.debug(f"Aggregation complete: {aggregated_scores.shape}")
        return aggregated_scores


# =============================================================================
# Phase 3: Vectorized Indicator Scoring
# =============================================================================

def _is_simple_goalpost(score_function: str, dataset_codes: list[str]) -> bool:
    """
    Check if a score function is a simple goalpost call.

    Simple goalpost patterns:
    - "Score = goalpost(DATASET, lower, upper)"
    - "Score = goalpost(-DATASET, -upper, -lower)"  (inverted)

    Args:
        score_function: The score function string
        dataset_codes: List of dataset codes for this indicator

    Returns:
        True if this is a simple goalpost function
    """
    if not score_function or len(dataset_codes) != 1:
        return False

    # Normalize whitespace
    normalized = ' '.join(score_function.split())

    # Check for simple patterns
    dataset_code = dataset_codes[0]

    # Pattern 1: Score = goalpost(DATASET, ...)
    if f"goalpost({dataset_code}," in normalized.replace(" ", ""):
        return True

    # Pattern 2: Score = goalpost(-DATASET, ...) (inverted)
    if f"goalpost(-{dataset_code}," in normalized.replace(" ", ""):
        return True

    return False


def _is_inverted_goalpost(score_function: str) -> bool:
    """
    Check if a goalpost function is inverted (uses negative dataset value).

    Args:
        score_function: The score function string

    Returns:
        True if the function uses -DATASET pattern
    """
    # Remove whitespace for easier pattern matching
    normalized = score_function.replace(" ", "")

    # Look for goalpost(-DATASET pattern
    return "goalpost(-" in normalized


def score_indicators_vectorized(
    indicators: list[dict],
    dataset_arrays: dict[str, np.ndarray],
    country_codes: list[str],
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR
) -> np.ndarray:
    """
    Score all indicators using vectorized NumPy operations.

    For standard goalpost scoring, applies the formula vectorized.
    For custom score functions, falls back to element-wise evaluation.

    Args:
        indicators: List of indicator metadata dicts
        dataset_arrays: Dict mapping dataset_code -> (n_countries, n_years) array
        country_codes: List of country codes (for array ordering)
        start_year: Start year of data range
        end_year: End year of data range

    Returns:
        Array of shape (n_indicators, n_countries, n_years) with scores in [0, 1]
    """
    n_indicators = len(indicators)
    n_countries = len(country_codes)
    n_years = end_year - start_year + 1

    # Initialize output array
    indicator_scores = np.full((n_indicators, n_countries, n_years), np.nan, dtype=np.float64)

    logger.info(f"Scoring {n_indicators} indicators across {n_countries} countries, {n_years} years")

    for i, indicator in enumerate(indicators):
        indicator_code = indicator.get("ItemCode") or indicator.get("IndicatorCode")
        score_function_str = indicator.get("ScoreFunction", "")
        dataset_codes = indicator.get("DatasetCodes", [])
        lower_goalpost = indicator.get("LowerGoalpost")
        upper_goalpost = indicator.get("UpperGoalpost")

        if not dataset_codes:
            logger.warning(f"No DatasetCodes for indicator {indicator_code}, skipping")
            continue

        # Stack the required datasets
        # If a dataset is missing, fill with NaN
        dataset_stack = []
        missing_datasets = []
        for ds_code in dataset_codes:
            if ds_code in dataset_arrays:
                dataset_stack.append(dataset_arrays[ds_code])
            else:
                missing_datasets.append(ds_code)
                # Fill with NaN for missing dataset
                dataset_stack.append(np.full((n_countries, n_years), np.nan))

        if missing_datasets:
            logger.warning(
                f"Missing datasets for {indicator_code}: {missing_datasets}. "
                f"Scores will be NaN where data is missing."
            )

        # Convert to array of shape (n_datasets, n_countries, n_years)
        dataset_stack = np.array(dataset_stack)

        # Check if this is a simple goalpost function
        is_simple_goalpost = _is_simple_goalpost(score_function_str, dataset_codes)

        if is_simple_goalpost and lower_goalpost is not None and upper_goalpost is not None:
            # Fast path: vectorized goalpost scoring
            # For simple goalpost, there should be exactly one dataset
            values = dataset_stack[0]  # shape: (n_countries, n_years)

            # Check if inverted (e.g., "Score = goalpost(-DATASET, -100, 0)")
            inverted = _is_inverted_goalpost(score_function_str)

            indicator_scores[i] = _apply_goalpost_vectorized(
                values, lower_goalpost, upper_goalpost, inverted
            )

            logger.debug(f"Scored {indicator_code} using vectorized goalpost")
        else:
            # Slow path: custom score function evaluation
            try:
                indicator_scores[i] = _apply_custom_score_function(
                    score_function_str,
                    dataset_stack,
                    dataset_codes,
                    lower_goalpost,
                    upper_goalpost
                )
                logger.debug(f"Scored {indicator_code} using custom score function")
            except Exception as e:
                logger.error(f"Failed to score {indicator_code}: {e}")
                # Leave as NaN

    return indicator_scores


def _apply_goalpost_vectorized(
    values: np.ndarray,
    lower_goalpost: float,
    upper_goalpost: float,
    inverted: bool = False
) -> np.ndarray:
    """
    Apply goalpost formula to entire array at once.

    Formula: score = (value - lower) / (upper - lower)
    If inverted: score = 1 - score

    Args:
        values: Array of any shape
        lower_goalpost: Lower bound value
        upper_goalpost: Upper bound value
        inverted: Whether to invert the score

    Returns:
        Array of same shape with scores clipped to [0, 1]
    """
    # Handle the edge case where upper == lower
    if upper_goalpost == lower_goalpost:
        # If value equals the single goalpost, score is 0.5; otherwise clamp
        scores = np.where(
            values == lower_goalpost,
            0.5,
            np.where(values > upper_goalpost, 1.0, 0.0)
        )
    else:
        # Standard goalpost formula
        scores = (values - lower_goalpost) / (upper_goalpost - lower_goalpost)

        # Clip to [0, 1] range
        scores = np.clip(scores, 0.0, 1.0)

    # Invert if needed
    if inverted:
        scores = 1.0 - scores

    return scores


def _apply_custom_score_function(
    score_function: str,
    dataset_stack: np.ndarray,
    dataset_codes: list[str],
    lower_goalpost: float | None,
    upper_goalpost: float | None
) -> np.ndarray:
    """
    Apply a custom score function element-wise.

    Falls back to Python loop when vectorization isn't possible.

    Args:
        score_function: Score function string
        dataset_stack: Array of shape (n_datasets, n_countries, n_years)
        dataset_codes: List of dataset codes matching first dimension
        lower_goalpost: Optional lower goalpost value
        upper_goalpost: Optional upper goalpost value

    Returns:
        Array of shape (n_countries, n_years) with scores
    """
    if not score_function:
        raise ValueError("Empty score function")

    # Validate the score function once
    try:
        validated_function = validate_score_function(score_function)
    except Exception as e:
        raise ValueError(f"Invalid score function: {e}")

    # Get dimensions
    n_datasets, n_countries, n_years = dataset_stack.shape

    # Initialize output array
    scores = np.full((n_countries, n_years), np.nan, dtype=np.float64)

    # Loop through each (country, year) cell
    for country_idx in range(n_countries):
        for year_idx in range(n_years):
            # Extract values for this (country, year)
            dataset_values = {}
            has_nan = False

            for ds_idx, ds_code in enumerate(dataset_codes):
                value = dataset_stack[ds_idx, country_idx, year_idx]
                if np.isnan(value):
                    has_nan = True
                    break
                dataset_values[ds_code] = float(value)

            # Skip if any dataset value is NaN
            if has_nan:
                continue

            # Evaluate the score function
            try:
                score = safe_eval(
                    validated_function,
                    dataset_values,
                    lower_goalpost=lower_goalpost,
                    upper_goalpost=upper_goalpost
                )

                # Clamp to [0, 1]
                score = max(0.0, min(1.0, score))
                scores[country_idx, year_idx] = score

            except Exception as e:
                # Log the error but continue (leave as NaN)
                logger.warning(
                    f"Score function evaluation failed at country {country_idx}, "
                    f"year {year_idx}: {e}"
                )
                continue

    return scores


# =============================================================================
# Phase 4: Ranking and Storage
# =============================================================================

def compute_ranks_vectorized(all_scores: np.ndarray) -> np.ndarray:
    """
    Compute ranks for all items using NumPy argsort.

    Higher scores get better (lower) ranks.

    Args:
        all_scores: Array of shape (n_items, n_countries, n_years)

    Returns:
        Array of shape (n_items, n_countries, n_years) with integer ranks
    """
    n_items, n_countries, n_years = all_scores.shape
    ranks = np.zeros_like(all_scores, dtype=int)

    # For each item and year, rank countries by score
    for item_idx in range(n_items):
        for year_idx in range(n_years):
            # Get scores for this item and year across all countries
            year_scores = all_scores[item_idx, :, year_idx]

            # Handle NaN values - they should get the worst rank
            # argsort returns indices that would sort the array
            # Use negative scores for descending order (higher score = rank 1)
            # NaN values will be sorted to the end
            valid_mask = ~np.isnan(year_scores)

            if not np.any(valid_mask):
                # All scores are NaN, assign no ranks (keep as 0)
                continue

            # Create a copy with NaN replaced by -inf to ensure they rank last
            scores_for_ranking = np.where(valid_mask, year_scores, -np.inf)

            # Get indices that would sort in descending order
            sorted_indices = np.argsort(-scores_for_ranking)

            # Assign ranks (1-based)
            # Countries with NaN scores won't get valid ranks (stay 0)
            rank_values = np.zeros(n_countries, dtype=int)
            rank_values[sorted_indices] = np.arange(1, n_countries + 1)

            # Only assign ranks to valid (non-NaN) scores
            rank_values = np.where(valid_mask, rank_values, 0)

            ranks[item_idx, :, year_idx] = rank_values

    return ranks


def flatten_to_documents(
    indicator_scores: np.ndarray,
    aggregated_scores: np.ndarray,
    indicator_ranks: np.ndarray,
    aggregated_ranks: np.ndarray,
    indicator_codes: list[str],
    item_codes: list[str],
    country_codes: list[str],
    start_year: int,
    metadata: list[dict],
    imputation_flags: dict[str, np.ndarray] | None = None
) -> list[dict]:
    """
    Convert NumPy arrays to list of score documents for MongoDB.

    Args:
        indicator_scores: Shape (n_indicators, n_countries, n_years)
        aggregated_scores: Shape (n_items, n_countries, n_years)
        indicator_ranks: Shape (n_indicators, n_countries, n_years)
        aggregated_ranks: Shape (n_items, n_countries, n_years)
        indicator_codes: Ordered list of indicator codes
        item_codes: Ordered list of category/pillar/SSPI codes
        country_codes: Ordered list of country codes
        start_year: First year in data
        metadata: Original metadata for item names/types
        imputation_flags: Optional dict of imputation flag arrays

    Returns:
        List of score documents ready for bulk insert
    """
    # Build metadata lookup tables
    items_by_code = {item["ItemCode"]: item for item in metadata}

    documents = []
    n_years = indicator_scores.shape[2]

    # Process indicator scores
    for ind_idx, ind_code in enumerate(indicator_codes):
        item = items_by_code.get(ind_code)
        if not item:
            logger.warning(f"No metadata found for indicator {ind_code}")
            continue

        item_name = item.get("ItemName", ind_code)

        for country_idx, country_code in enumerate(country_codes):
            for year_idx in range(n_years):
                year = start_year + year_idx
                score = indicator_scores[ind_idx, country_idx, year_idx]
                rank = indicator_ranks[ind_idx, country_idx, year_idx]

                # Skip NaN scores
                if np.isnan(score):
                    continue

                # Check imputation status if provided
                imputed = False
                imputation_method = None
                if imputation_flags and ind_code in imputation_flags:
                    imputed = bool(imputation_flags[ind_code][country_idx, year_idx])

                documents.append({
                    "item_code": ind_code,
                    "item_name": item_name,
                    "item_type": "Indicator",
                    "country_code": country_code,
                    "year": year,
                    "score": float(score * 100),  # Convert to 0-100 scale
                    "rank": int(rank),
                    "imputed": imputed,
                    "imputation_method": imputation_method,
                })

    # Process aggregated scores (categories, pillars, SSPI)
    for item_idx, item_code in enumerate(item_codes):
        item = items_by_code.get(item_code)

        # For SSPI root, might not be in metadata by code
        if not item and item_code == "SSPI":
            # Find SSPI item by type
            item = next(
                (m for m in metadata if m.get("ItemType") == "SSPI"),
                {"ItemCode": "SSPI", "ItemName": "SSPI", "ItemType": "SSPI"}
            )

        if not item:
            logger.warning(f"No metadata found for item {item_code}")
            continue

        item_name = item.get("ItemName", item_code)
        item_type = item.get("ItemType", "Unknown")

        for country_idx, country_code in enumerate(country_codes):
            for year_idx in range(n_years):
                year = start_year + year_idx
                score = aggregated_scores[item_idx, country_idx, year_idx]
                rank = aggregated_ranks[item_idx, country_idx, year_idx]

                # Skip NaN scores
                if np.isnan(score):
                    continue

                # Aggregated items inherit imputation from children
                # For now, mark as not imputed (would need child tracking for accuracy)
                documents.append({
                    "item_code": item_code,
                    "item_name": item_name,
                    "item_type": item_type,
                    "country_code": country_code,
                    "year": year,
                    "score": float(score * 100),  # Convert to 0-100 scale
                    "rank": int(rank),
                    "imputed": False,  # Could be improved to track child imputation
                    "imputation_method": None,
                })

    logger.info(f"Flattened {len(documents)} score documents")
    return documents


# =============================================================================
# Phase 5: Main Pipeline
# =============================================================================

def score_custom_configuration_fast(
    metadata: list[dict],
    modified_indicators: set[str] | None = None,
    default_scores: dict[str, list[dict]] | None = None,
    country_codes: list[str] | None = None,
    reference_group: str = "SSPI67",
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    progress_callback: Callable[[str, int, str], None] | None = None
) -> dict[str, list[dict]]:
    """
    Fast scoring pipeline using vectorized operations and matrix multiplication.

    Drop-in replacement for score_custom_configuration() with same interface.

    NOTE: This function always scores ALL indicators in the metadata because
    the matrix multiplication requires consistent dimensions. The metadata
    should be pre-filtered to remove indicators with empty datasets before
    calling this function.

    Args:
        metadata: Custom SSPI metadata structure (pre-filtered for data availability)
        modified_indicators: IGNORED - kept for interface compatibility
        default_scores: IGNORED - kept for interface compatibility
        country_codes: List of country codes to score (defaults to SSPI67)
        reference_group: Country group for reference class averaging
        start_year: Start year for scoring
        end_year: End year for scoring
        progress_callback: Optional callback(phase, percent, message)

    Returns:
        Dict mapping item_code -> list of ranked score documents
    """
    # Get country codes if not provided
    if country_codes is None:
        country_codes = sspi_metadata.country_group(reference_group) or []

    if not country_codes:
        logger.warning(f"No country codes found for reference group {reference_group}")
        return {}

    # Extract all indicators from metadata
    # NOTE: We always score ALL indicators in the metadata because the
    # aggregation matrix dimensions must match. The vectorized operations
    # are fast enough that partial scoring is not necessary.
    # The metadata should already be filtered to remove dropped indicators
    # (those with empty datasets) before calling this function.
    all_indicators = [
        item for item in metadata
        if item.get("ItemType") == "Indicator"
    ]

    # Always score all indicators - matrix multiplication requires consistent dimensions
    indicators_to_score = all_indicators

    logger.info(
        f"Fast pipeline: Scoring {len(indicators_to_score)} indicators"
    )

    # Phase 1: Fetch datasets
    if progress_callback:
        progress_callback("scoring", 5, "Fetching datasets...")

    # Collect all dataset codes needed
    dataset_codes = set()
    for ind in indicators_to_score:
        codes = ind.get("DatasetCodes", [])
        if codes:
            dataset_codes.update(codes)

    if not dataset_codes:
        logger.warning("No dataset codes found in indicators")
        return {}

    logger.info(f"Fetching {len(dataset_codes)} datasets")
    dataset_arrays = fetch_all_datasets_aggregated(
        list(dataset_codes),
        country_codes,
        start_year,
        end_year
    )

    # Phase 2: Impute datasets
    if progress_callback:
        progress_callback("scoring", 20, "Imputing missing data...")

    # Get reference mask for imputation
    reference_countries = sspi_metadata.country_group(reference_group) or []
    reference_mask = np.array([c in reference_countries for c in country_codes])

    imputation_flags = {}
    for dataset_code, data_array in dataset_arrays.items():
        imputed_data, imputed_flag = impute_dataset_vectorized(
            data_array,
            reference_mask,
            neutral_fill=0.5
        )
        dataset_arrays[dataset_code] = imputed_data
        imputation_flags[dataset_code] = imputed_flag

    # Phase 3: Score indicators
    if progress_callback:
        progress_callback("scoring", 40, "Scoring indicators...")

    indicator_scores = score_indicators_vectorized(
        indicators_to_score,
        dataset_arrays,
        country_codes,
        start_year,
        end_year
    )

    # Phase 4: Aggregate hierarchy
    if progress_callback:
        progress_callback("aggregation", 70, "Aggregating hierarchy...")

    fast_sspi = FastCustomSSPI(metadata)
    aggregated_scores = fast_sspi.aggregate(indicator_scores)

    # Phase 5: Compute ranks
    if progress_callback:
        progress_callback("ranking", 85, "Computing ranks...")

    # Stack all scores together
    all_scores = np.concatenate([indicator_scores, aggregated_scores], axis=0)
    all_codes = fast_sspi.indicator_codes + fast_sspi.item_codes

    all_ranks = compute_ranks_vectorized(all_scores)

    # Phase 6: Convert to dict format
    if progress_callback:
        progress_callback("complete", 95, "Formatting results...")

    result = _arrays_to_score_dicts(
        all_scores,
        all_ranks,
        all_codes,
        country_codes,
        start_year,
        metadata
    )

    # NOTE: default_scores parameter is ignored - we always score all indicators
    # in the metadata for correct matrix multiplication dimensions

    if progress_callback:
        total_docs = sum(len(docs) for docs in result.values())
        progress_callback("complete", 100, f"Scored {total_docs} records")

    return result


def _arrays_to_score_dicts(
    all_scores: np.ndarray,
    all_ranks: np.ndarray,
    all_codes: list[str],
    country_codes: list[str],
    start_year: int,
    metadata: list[dict]
) -> dict[str, list[dict]]:
    """
    Convert score/rank arrays to the dict format expected by callers.

    Args:
        all_scores: Shape (n_items, n_countries, n_years)
        all_ranks: Shape (n_items, n_countries, n_years)
        all_codes: Ordered list of all item codes
        country_codes: Ordered list of country codes
        start_year: First year in data
        metadata: Original metadata for item names/types

    Returns:
        Dict mapping item_code -> list of score dicts
    """
    # Build metadata lookup
    items_by_code = {item["ItemCode"]: item for item in metadata}

    # Result dictionary
    result = {}

    n_items, n_countries, n_years = all_scores.shape

    # Process each item
    for item_idx, item_code in enumerate(all_codes):
        item = items_by_code.get(item_code)

        # Handle SSPI root specially (might not be in metadata by exact code)
        if not item and item_code == "SSPI":
            item = next(
                (m for m in metadata if m.get("ItemType") == "SSPI"),
                {"ItemCode": "SSPI", "ItemName": "SSPI", "ItemType": "SSPI"}
            )

        if not item:
            logger.warning(f"No metadata found for item {item_code}")
            continue

        item_name = item.get("ItemName", item_code)
        item_type = item.get("ItemType", "Unknown")

        # Build list of score documents for this item
        item_docs = []

        for country_idx, country_code in enumerate(country_codes):
            for year_idx in range(n_years):
                year = start_year + year_idx
                score = all_scores[item_idx, country_idx, year_idx]
                rank = all_ranks[item_idx, country_idx, year_idx]

                # Skip NaN scores
                if np.isnan(score):
                    continue

                item_docs.append({
                    "item_code": item_code,
                    "item_name": item_name,
                    "item_type": item_type,
                    "country_code": country_code,
                    "year": year,
                    "score": float(score * 100),  # Convert to 0-100 scale
                    "rank": int(rank),
                    "imputed": False,  # Imputation tracking would require dataset-level flags
                    "imputation_method": None,
                })

        result[item_code] = item_docs

    logger.info(f"Converted {len(result)} items to score dicts")
    return result
