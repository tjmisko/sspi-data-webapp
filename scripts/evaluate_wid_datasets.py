#!/usr/bin/env python3
"""
Evaluate WID datasets to determine which have data and which should be deleted.
Generates status reports for cleanup process.
"""

import os
import sys
import csv
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sspi_flask_app.models.database import sspi_clean_api_data, sspi_metadata


def get_wid_datasets_from_git() -> Tuple[List[str], Dict[str, str], Dict[str, str]]:
    """
    Extract WID dataset information from git status.
    Returns:
        - List of unique dataset codes
        - Dict mapping dataset codes to Python file paths
        - Dict mapping dataset codes to documentation directory paths
    """
    # Get git status
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    dataset_codes = set()
    python_files = {}
    doc_dirs = {}
    
    for line in result.stdout.splitlines():
        if not line.startswith("??"):
            continue
            
        path = line[3:].strip()
        
        # Check for Python cleaner files
        if "sspi_flask_app/api/core/datasets/wid_" in path and path.endswith(".py"):
            dataset_name = path.split("/")[-1].replace(".py", "")
            dataset_code = dataset_name.upper()
            dataset_codes.add(dataset_code)
            python_files[dataset_code] = path
            
        # Check for documentation directories
        elif path.startswith("datasets/wid_") and path.endswith("/"):
            dataset_name = path.split("/")[1]
            dataset_code = dataset_name.upper()
            doc_dirs[dataset_code] = path
    
    return sorted(list(dataset_codes)), python_files, doc_dirs


def query_dataset_data(dataset_code: str) -> int:
    """Query sspi_clean_api_data for record count of a dataset."""
    try:
        count = sspi_clean_api_data.count_documents({"DatasetCode": dataset_code})
        return count
    except Exception as e:
        print(f"Error querying {dataset_code}: {e}")
        return -1


def evaluate_datasets():
    """Main evaluation function."""
    print("Starting WID dataset evaluation...")
    
    # Get dataset information from git
    dataset_codes, python_files, doc_dirs = get_wid_datasets_from_git()
    
    print(f"Found {len(dataset_codes)} unique dataset codes")
    print(f"Found {len(python_files)} Python cleaner files")
    print(f"Found {len(doc_dirs)} documentation directories")
    
    # Find orphaned documentation directories
    orphaned_docs = []
    for doc_code, doc_path in doc_dirs.items():
        if doc_code not in python_files:
            orphaned_docs.append({
                "DatasetCode": doc_code,
                "DocumentationPath": doc_path,
                "Reason": "No corresponding Python cleaner file"
            })
    
    print(f"Found {len(orphaned_docs)} orphaned documentation directories")
    
    # Evaluate each dataset
    results = []
    for i, dataset_code in enumerate(dataset_codes, 1):
        print(f"Evaluating {i}/{len(dataset_codes)}: {dataset_code}...", end=" ")
        
        # Query for data
        record_count = query_dataset_data(dataset_code)
        
        # Determine status
        if record_count > 0:
            status = "KEEP"
            print(f"{record_count} records - KEEP")
        elif record_count == 0:
            status = "DELETE"
            print("0 records - DELETE")
        else:
            status = "ERROR"
            print("ERROR")
        
        # Build result record
        result = {
            "DatasetCode": dataset_code,
            "RecordCount": record_count,
            "Status": status,
            "HasPythonFile": dataset_code in python_files,
            "HasDocumentation": dataset_code in doc_dirs,
            "PythonFilePath": python_files.get(dataset_code, ""),
            "DocumentationPath": doc_dirs.get(dataset_code, "")
        }
        results.append(result)
    
    # Write main status report
    status_file = project_root / "wid_datasets_status.csv"
    with open(status_file, "w", newline="") as f:
        fieldnames = [
            "DatasetCode", "RecordCount", "Status", 
            "HasPythonFile", "HasDocumentation",
            "PythonFilePath", "DocumentationPath"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nWrote status report to {status_file}")
    
    # Write orphaned documentation report
    if orphaned_docs:
        orphan_file = project_root / "wid_orphaned_docs.csv"
        with open(orphan_file, "w", newline="") as f:
            fieldnames = ["DatasetCode", "DocumentationPath", "Reason"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(orphaned_docs)
        print(f"Wrote orphaned docs report to {orphan_file}")
    
    # Generate summary statistics
    total_datasets = len(results)
    keep_count = sum(1 for r in results if r["Status"] == "KEEP")
    delete_count = sum(1 for r in results if r["Status"] == "DELETE")
    error_count = sum(1 for r in results if r["Status"] == "ERROR")
    
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Total datasets evaluated: {total_datasets}")
    print(f"Datasets to KEEP: {keep_count}")
    print(f"Datasets to DELETE: {delete_count}")
    print(f"Datasets with ERRORS: {error_count}")
    print(f"Orphaned documentation directories: {len(orphaned_docs)}")
    print("\nFiles to be removed:")
    print(f"  - Python files: {delete_count}")
    print(f"  - Documentation directories: {delete_count + len(orphaned_docs)}")
    print(f"  - Total files/dirs to remove: {delete_count * 2 + len(orphaned_docs)}")
    
    return results, orphaned_docs


if __name__ == "__main__":
    evaluate_datasets()