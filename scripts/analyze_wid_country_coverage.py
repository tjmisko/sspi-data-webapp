#!/usr/bin/env python3
"""
Analyze country coverage for WID datasets to identify those with insufficient geographic coverage.
Generates comprehensive reports for deletion recommendations.
"""

import os
import sys
import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sspi_flask_app.models.database import sspi_metadata


def get_sspi_countries() -> Set[str]:
    """Get the set of SSPI67 countries as reference."""
    try:
        sspi_countries = set(sspi_metadata.country_group("SSPI67"))
        print(f"Reference: {len(sspi_countries)} SSPI countries")
        return sspi_countries
    except Exception as e:
        print(f"Error getting SSPI countries: {e}")
        return set()


def get_remaining_datasets() -> List[str]:
    """Get list of datasets marked as KEEP from previous analysis."""
    status_file = project_root / "wid_datasets_status.csv"
    if not status_file.exists():
        print(f"Error: Status file {status_file} not found. Run evaluate_wid_datasets.py first.")
        sys.exit(1)
    
    datasets = []
    with open(status_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Status"] == "KEEP":
                datasets.append(row["DatasetCode"])
    
    return sorted(datasets)


def query_dataset_countries(dataset_code: str) -> Tuple[Set[str], int]:
    """
    Query country coverage for a dataset.
    Returns: (set of country codes, total record count)
    """
    try:
        # Query the dataset
        cmd = f"sspi query clean {dataset_code}"
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"  Error querying {dataset_code}: {result.stderr}")
            return set(), 0
        
        # Parse JSON response
        data = json.loads(result.stdout)
        
        if not data:
            return set(), 0
        
        # Extract unique country codes
        countries = set()
        for record in data:
            if "CountryCode" in record:
                countries.add(record["CountryCode"])
        
        return countries, len(data)
        
    except subprocess.TimeoutExpired:
        print(f"  Timeout querying {dataset_code}")
        return set(), 0
    except json.JSONDecodeError as e:
        print(f"  JSON decode error for {dataset_code}: {e}")
        return set(), 0
    except Exception as e:
        print(f"  Error querying {dataset_code}: {e}")
        return set(), 0


def categorize_coverage(coverage_percent: float) -> str:
    """Categorize coverage percentage."""
    if coverage_percent >= 90:
        return "Excellent"
    elif coverage_percent >= 68:
        return "Good"
    elif coverage_percent >= 30:
        return "Fair"
    elif coverage_percent >= 15:
        return "Poor"
    else:
        return "Very Poor"


def analyze_dataset_family(dataset_code: str) -> Tuple[str, str, str]:
    """
    Extract dataset family, subcategory, and percentile range.
    Returns: (family, subcategory, percentile)
    """
    parts = dataset_code.replace("WID_", "").split("_")
    
    if not parts:
        return "Unknown", "Unknown", "Unknown"
    
    # Extract family (first part)
    family = parts[0] if parts else "Unknown"
    
    # Extract percentile (last part)
    percentile = "Unknown"
    if parts and parts[-1].startswith("P"):
        percentile = parts[-1]
        parts = parts[:-1]  # Remove percentile for subcategory analysis
    
    # Extract subcategory (remaining parts)
    if len(parts) > 1:
        subcategory = "_".join(parts[1:])
    else:
        subcategory = "Base"
    
    return family, subcategory, percentile


def analyze_coverage():
    """Main analysis function."""
    print("Starting WID Dataset Country Coverage Analysis")
    print("=" * 60)
    
    # Get reference data
    sspi_countries = get_sspi_countries()
    datasets = get_remaining_datasets()
    
    if not sspi_countries:
        print("Error: Could not get SSPI countries reference")
        return
    
    sspi_count = len(sspi_countries)
    print(f"Analyzing {len(datasets)} datasets against {sspi_count} SSPI countries")
    print()
    
    # Analyze each dataset
    results = []
    family_stats = defaultdict(list)
    percentile_stats = defaultdict(list)
    
    for i, dataset_code in enumerate(datasets, 1):
        print(f"Analyzing {i}/{len(datasets)}: {dataset_code}...", end=" ")
        
        # Query dataset
        dataset_countries, record_count = query_dataset_countries(dataset_code)
        
        if not dataset_countries and record_count == 0:
            print("ERROR - no data")
            continue
        
        # Calculate metrics
        country_count = len(dataset_countries)
        coverage_percent = (country_count / sspi_count) * 100
        records_per_country = record_count / country_count if country_count > 0 else 0
        coverage_category = categorize_coverage(coverage_percent)
        
        # Missing countries
        missing_countries = sspi_countries - dataset_countries
        missing_count = len(missing_countries)
        
        # Analyze dataset structure
        family, subcategory, percentile = analyze_dataset_family(dataset_code)
        
        print(f"{country_count} countries ({coverage_percent:.1f}%) - {coverage_category}")
        
        # Build result record
        result = {
            "DatasetCode": dataset_code,
            "Family": family,
            "Subcategory": subcategory,
            "Percentile": percentile,
            "CountryCount": country_count,
            "CoveragePercent": round(coverage_percent, 1),
            "RecordCount": record_count,
            "RecordsPerCountry": round(records_per_country, 1),
            "CoverageCategory": coverage_category,
            "MissingCountries": missing_count,
            "MissingCountryList": ",".join(sorted(missing_countries)) if missing_count <= 10 else f"{missing_count} countries"
        }
        results.append(result)
        
        # Collect statistics
        family_stats[family].append(coverage_percent)
        percentile_stats[percentile].append(coverage_percent)
    
    # Sort results by coverage percentage (descending)
    results.sort(key=lambda x: x["CoveragePercent"], reverse=True)
    
    # Write main coverage report
    coverage_file = project_root / "wid_country_coverage_report.csv"
    with open(coverage_file, "w", newline="") as f:
        fieldnames = [
            "DatasetCode", "Family", "Subcategory", "Percentile",
            "CountryCount", "CoveragePercent", "RecordCount", 
            "RecordsPerCountry", "CoverageCategory", "MissingCountries",
            "MissingCountryList"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nWrote main coverage report to {coverage_file}")
    
    # Generate category summary
    category_file = project_root / "wid_coverage_by_category.csv"
    category_summary = []
    
    # Family statistics
    for family, coverages in family_stats.items():
        category_summary.append({
            "Category": f"Family_{family}",
            "DatasetCount": len(coverages),
            "AvgCoverage": round(sum(coverages) / len(coverages), 1),
            "MinCoverage": round(min(coverages), 1),
            "MaxCoverage": round(max(coverages), 1),
            "ExcellentCount": sum(1 for c in coverages if c >= 90),
            "PoorCount": sum(1 for c in coverages if c < 30)
        })
    
    # Percentile statistics
    for percentile, coverages in percentile_stats.items():
        category_summary.append({
            "Category": f"Percentile_{percentile}",
            "DatasetCount": len(coverages),
            "AvgCoverage": round(sum(coverages) / len(coverages), 1),
            "MinCoverage": round(min(coverages), 1),
            "MaxCoverage": round(max(coverages), 1),
            "ExcellentCount": sum(1 for c in coverages if c >= 90),
            "PoorCount": sum(1 for c in coverages if c < 30)
        })
    
    with open(category_file, "w", newline="") as f:
        fieldnames = [
            "Category", "DatasetCount", "AvgCoverage", "MinCoverage", 
            "MaxCoverage", "ExcellentCount", "PoorCount"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(category_summary)
    
    print(f"Wrote category summary to {category_file}")
    
    # Generate low-coverage candidates
    low_coverage = [r for r in results if r["CoveragePercent"] < 30]
    
    if low_coverage:
        candidates_file = project_root / "wid_low_coverage_candidates.csv"
        with open(candidates_file, "w", newline="") as f:
            fieldnames = [
                "DatasetCode", "Family", "Subcategory", "Percentile", "CountryCount", 
                "CoveragePercent", "RecordCount", "RecordsPerCountry", "CoverageCategory",
                "MissingCountries", "MissingCountryList"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(low_coverage)
        
        print(f"Wrote {len(low_coverage)} low-coverage candidates to {candidates_file}")
    
    # Generate summary statistics
    total_datasets = len(results)
    excellent_count = sum(1 for r in results if r["CoverageCategory"] == "Excellent")
    good_count = sum(1 for r in results if r["CoverageCategory"] == "Good")
    fair_count = sum(1 for r in results if r["CoverageCategory"] == "Fair")
    poor_count = sum(1 for r in results if r["CoverageCategory"] == "Poor")
    very_poor_count = sum(1 for r in results if r["CoverageCategory"] == "Very Poor")
    
    print("\n" + "="*60)
    print("COUNTRY COVERAGE ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total datasets analyzed: {total_datasets}")
    print(f"Reference countries (SSPI67): {sspi_count}")
    print()
    print("Coverage Distribution:")
    print(f"  Excellent (90%+):     {excellent_count:3d} datasets")
    print(f"  Good (68-89%):        {good_count:3d} datasets")
    print(f"  Fair (30-67%):        {fair_count:3d} datasets")
    print(f"  Poor (15-29%):        {poor_count:3d} datasets")
    print(f"  Very Poor (<15%):     {very_poor_count:3d} datasets")
    print()
    print("Deletion Recommendations:")
    print(f"  Low coverage (<30%):  {len(low_coverage):3d} datasets")
    print(f"  Very low (<15%):      {very_poor_count:3d} datasets")
    
    if low_coverage:
        print(f"\nTop 10 deletion candidates (lowest coverage):")
        worst_coverage = sorted(low_coverage, key=lambda x: x["CoveragePercent"])[:10]
        for dataset in worst_coverage:
            print(f"  {dataset['DatasetCode']:<40} {dataset['CountryCount']:2d} countries ({dataset['CoveragePercent']:4.1f}%)")
    
    return results, family_stats, percentile_stats


if __name__ == "__main__":
    analyze_coverage()