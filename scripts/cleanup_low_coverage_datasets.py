#!/usr/bin/env python3
"""
Clean up WID datasets with low country coverage based on coverage analysis results.
"""

import os
import sys
import csv
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_coverage_report() -> List[Dict]:
    """Load the country coverage analysis report."""
    coverage_file = project_root / "wid_country_coverage_report.csv"
    if not coverage_file.exists():
        print(f"Error: Coverage report {coverage_file} not found. Run analyze_wid_country_coverage.py first.")
        sys.exit(1)
    
    with open(coverage_file, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_dataset_paths() -> Dict[str, Dict[str, str]]:
    """Load dataset file paths from the original status report."""
    status_file = project_root / "wid_datasets_status.csv"
    if not status_file.exists():
        print(f"Error: Status file {status_file} not found.")
        sys.exit(1)
    
    paths = {}
    with open(status_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Status"] == "KEEP":
                paths[row["DatasetCode"]] = {
                    "python_file": row["PythonFilePath"],
                    "doc_dir": row["DocumentationPath"]
                }
    
    return paths


def filter_datasets_by_coverage(coverage_data: List[Dict], min_coverage: float) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter datasets by coverage threshold.
    Returns: (datasets_to_keep, datasets_to_delete)
    """
    keep = []
    delete = []
    
    for dataset in coverage_data:
        coverage_percent = float(dataset["CoveragePercent"])
        if coverage_percent >= min_coverage:
            keep.append(dataset)
        else:
            delete.append(dataset)
    
    return keep, delete


def confirm_deletion(datasets_to_delete: List[Dict], min_coverage: float) -> bool:
    """Ask user to confirm deletion based on coverage threshold."""
    print("\n" + "="*60)
    print("LOW COUNTRY COVERAGE DELETION SUMMARY")
    print("="*60)
    print(f"Coverage threshold: {min_coverage}%")
    print(f"Datasets to delete: {len(datasets_to_delete)}")
    
    # Show deletion breakdown by coverage category
    categories = {}
    for dataset in datasets_to_delete:
        cat = dataset["CoverageCategory"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(dataset)
    
    print("\nDeletion breakdown by coverage category:")
    for category, datasets in categories.items():
        print(f"  {category}: {len(datasets)} datasets")
    
    print(f"\nFiles to delete:")
    print(f"  - Python cleaner files: {len(datasets_to_delete)}")
    print(f"  - Documentation directories: {len(datasets_to_delete)}")
    print(f"  - TOTAL: {len(datasets_to_delete) * 2}")
    
    print(f"\nWorst coverage datasets to be deleted (first 10):")
    worst = sorted(datasets_to_delete, key=lambda x: float(x["CoveragePercent"]))[:10]
    for dataset in worst:
        print(f"  {dataset['DatasetCode']:<40} {int(dataset['CountryCount']):2d} countries ({dataset['CoveragePercent']}%)")
    
    if len(datasets_to_delete) > 10:
        print(f"  ... and {len(datasets_to_delete) - 10} more datasets")
    
    response = input(f"\nProceed with deletion of {len(datasets_to_delete)} datasets? (yes/no): ").strip().lower()
    return response == "yes"


def delete_low_coverage_datasets(datasets_to_delete: List[Dict], dataset_paths: Dict[str, Dict[str, str]]) -> Dict:
    """Delete files and directories for low-coverage datasets."""
    summary = {
        "python_files_deleted": [],
        "python_files_failed": [],
        "doc_dirs_deleted": [],
        "doc_dirs_failed": [],
        "datasets_not_found": []
    }
    
    print("\nStarting deletion process...")
    
    for dataset in datasets_to_delete:
        dataset_code = dataset["DatasetCode"]
        
        if dataset_code not in dataset_paths:
            summary["datasets_not_found"].append(dataset_code)
            print(f"  Warning: Path info not found for {dataset_code}")
            continue
        
        paths = dataset_paths[dataset_code]
        
        # Delete Python file
        if paths["python_file"]:
            py_path = project_root / paths["python_file"]
            try:
                if py_path.exists():
                    py_path.unlink()
                    summary["python_files_deleted"].append(str(py_path))
                    print(f"  Deleted Python file: {paths['python_file']}")
                else:
                    print(f"  Warning: Python file not found: {paths['python_file']}")
            except Exception as e:
                summary["python_files_failed"].append(f"{paths['python_file']}: {e}")
                print(f"  Error deleting Python file {paths['python_file']}: {e}")
        
        # Delete documentation directory
        if paths["doc_dir"]:
            doc_path = project_root / paths["doc_dir"]
            try:
                if doc_path.exists():
                    shutil.rmtree(doc_path)
                    summary["doc_dirs_deleted"].append(str(doc_path))
                    print(f"  Deleted documentation: {paths['doc_dir']}")
                else:
                    print(f"  Warning: Documentation not found: {paths['doc_dir']}")
            except Exception as e:
                summary["doc_dirs_failed"].append(f"{paths['doc_dir']}: {e}")
                print(f"  Error deleting documentation {paths['doc_dir']}: {e}")
    
    return summary


def write_cleanup_summary(summary: Dict, datasets_deleted: List[Dict], min_coverage: float):
    """Write a summary of the cleanup operation."""
    summary_file = project_root / "wid_low_coverage_cleanup_summary.txt"
    
    with open(summary_file, "w") as f:
        f.write("WID LOW COUNTRY COVERAGE CLEANUP SUMMARY\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Coverage threshold: {min_coverage}%\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Python files deleted: {len(summary['python_files_deleted'])}\n")
        f.write(f"Python files failed: {len(summary['python_files_failed'])}\n")
        f.write(f"Documentation directories deleted: {len(summary['doc_dirs_deleted'])}\n")
        f.write(f"Documentation directories failed: {len(summary['doc_dirs_failed'])}\n")
        f.write(f"Datasets not found: {len(summary['datasets_not_found'])}\n")
        
        total_deleted = (len(summary['python_files_deleted']) + 
                        len(summary['doc_dirs_deleted']))
        total_failed = (len(summary['python_files_failed']) + 
                       len(summary['doc_dirs_failed']))
        
        f.write(f"\nTOTAL DELETED: {total_deleted}\n")
        f.write(f"TOTAL FAILED: {total_failed}\n")
        
        # Write deleted datasets list
        f.write(f"\nDeleted Datasets ({len(datasets_deleted)}):\n")
        for dataset in sorted(datasets_deleted, key=lambda x: float(x["CoveragePercent"])):
            f.write(f"  {dataset['DatasetCode']:<40} {int(dataset['CountryCount']):2d} countries ({dataset['CoveragePercent']}%)\n")
        
        # Write failure details if any
        if summary['python_files_failed']:
            f.write("\n\nFailed Python file deletions:\n")
            for failure in summary['python_files_failed']:
                f.write(f"  - {failure}\n")
        
        if summary['doc_dirs_failed']:
            f.write("\n\nFailed documentation directory deletions:\n")
            for failure in summary['doc_dirs_failed']:
                f.write(f"  - {failure}\n")
        
        if summary['datasets_not_found']:
            f.write("\n\nDatasets not found in path mapping:\n")
            for dataset in summary['datasets_not_found']:
                f.write(f"  - {dataset}\n")
    
    print(f"\nCleanup summary written to {summary_file}")
    return summary_file


def main():
    """Main cleanup function."""
    print("WID Low Country Coverage Cleanup Script")
    print("="*60)
    
    # Get coverage threshold from user
    while True:
        try:
            min_coverage = float(input("Enter minimum coverage percentage threshold (e.g., 30): "))
            if 0 <= min_coverage <= 100:
                break
            else:
                print("Please enter a percentage between 0 and 100.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Load data
    coverage_data = load_coverage_report()
    dataset_paths = load_dataset_paths()
    
    # Filter datasets
    keep_datasets, delete_datasets = filter_datasets_by_coverage(coverage_data, min_coverage)
    
    if not delete_datasets:
        print(f"\nNo datasets found with coverage below {min_coverage}%. No cleanup needed.")
        return
    
    print(f"\nFound {len(delete_datasets)} datasets with coverage below {min_coverage}%")
    print(f"Will keep {len(keep_datasets)} datasets with adequate coverage")
    
    # Confirm deletion
    if not confirm_deletion(delete_datasets, min_coverage):
        print("Deletion cancelled by user.")
        return
    
    # Perform deletion
    summary = delete_low_coverage_datasets(delete_datasets, dataset_paths)
    
    # Write summary
    summary_file = write_cleanup_summary(summary, delete_datasets, min_coverage)
    
    # Final report
    print("\n" + "="*60)
    print("CLEANUP COMPLETE")
    print("="*60)
    total_deleted = (len(summary['python_files_deleted']) + 
                    len(summary['doc_dirs_deleted']))
    total_failed = (len(summary['python_files_failed']) + 
                   len(summary['doc_dirs_failed']))
    
    print(f"Successfully deleted: {total_deleted} files/directories")
    print(f"Datasets removed: {len(delete_datasets)}")
    if total_failed > 0:
        print(f"Failed deletions: {total_failed} (see {summary_file} for details)")
    
    print(f"\nRemaining datasets: {len(keep_datasets)} (with ≥{min_coverage}% coverage)")
    print("\nYou can now review the changes with 'git status'")


if __name__ == "__main__":
    main()