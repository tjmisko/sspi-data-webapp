#!/usr/bin/env python3
"""
Find and analyze orphaned WID documentation directories that don't have corresponding Python cleaner files.
"""

import os
import sys
from pathlib import Path
from typing import Set, List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_wid_python_files() -> Set[str]:
    """Get set of WID dataset codes that have Python cleaner files."""
    python_dir = project_root / "sspi_flask_app" / "api" / "core" / "datasets"
    
    if not python_dir.exists():
        print(f"Error: Python datasets directory {python_dir} not found")
        sys.exit(1)
    
    wid_codes = set()
    for file_path in python_dir.glob("wid_*.py"):
        # Extract dataset code from filename (remove .py extension and convert to uppercase)
        dataset_code = file_path.stem.upper()
        wid_codes.add(dataset_code)
    
    print(f"Found {len(wid_codes)} WID Python cleaner files")
    return wid_codes


def get_wid_documentation_dirs() -> Set[str]:
    """Get set of WID dataset codes that have documentation directories."""
    docs_dir = project_root / "datasets"
    
    if not docs_dir.exists():
        print(f"Error: Documentation directory {docs_dir} not found")
        sys.exit(1)
    
    wid_codes = set()
    for dir_path in docs_dir.iterdir():
        if dir_path.is_dir() and dir_path.name.upper().startswith("WID_"):
            # Extract dataset code from directory name (convert to uppercase)
            dataset_code = dir_path.name.upper()
            wid_codes.add(dataset_code)
    
    print(f"Found {len(wid_codes)} WID documentation directories")
    return wid_codes


def find_orphaned_directories(python_codes: Set[str], doc_codes: Set[str]) -> List[str]:
    """Find documentation directories that don't have corresponding Python files."""
    orphaned = []
    
    for doc_code in doc_codes:
        if doc_code not in python_codes:
            orphaned.append(doc_code)
    
    return sorted(orphaned)


def analyze_discrepancy(python_codes: Set[str], doc_codes: Set[str], orphaned: List[str]):
    """Analyze and report on the discrepancy between directories."""
    print("\n" + "="*70)
    print("WID DATASET DIRECTORY ANALYSIS")
    print("="*70)
    
    print(f"Python cleaner files:        {len(python_codes)}")
    print(f"Documentation directories:   {len(doc_codes)}")
    print(f"Orphaned documentation:      {len(orphaned)}")
    
    # Find datasets with Python but no docs (shouldn't happen after our cleanup)
    missing_docs = python_codes - doc_codes
    if missing_docs:
        print(f"Missing documentation:       {len(missing_docs)}")
    
    print(f"\nDiscrepancy: {len(doc_codes) - len(python_codes)} extra documentation directories")
    
    if orphaned:
        print(f"\nOrphaned documentation directories ({len(orphaned)}):")
        print("(These have documentation but no Python cleaner file)")
        
        # Group by family for better analysis
        families = {}
        for code in orphaned:
            parts = code.split("_")
            if len(parts) >= 2:
                family = parts[1]  # WID_FAMILY_...
                if family not in families:
                    families[family] = []
                families[family].append(code)
        
        for family, codes in sorted(families.items()):
            print(f"\n  {family} family ({len(codes)} orphaned):")
            for code in sorted(codes)[:5]:  # Show first 5
                print(f"    {code}")
            if len(codes) > 5:
                print(f"    ... and {len(codes) - 5} more")
    
    return orphaned


def generate_cleanup_commands(orphaned: List[str]):
    """Generate commands to clean up orphaned directories."""
    if not orphaned:
        print("\nNo cleanup needed - directories are in sync!")
        return
    
    print(f"\nTo clean up {len(orphaned)} orphaned documentation directories:")
    print("="*70)
    
    # Generate rm commands
    docs_dir = project_root / "datasets"
    
    print("# Remove orphaned WID documentation directories:")
    for code in orphaned:
        doc_path = docs_dir / code.lower()
        print(f"rm -rf '{doc_path}'")
    
    print(f"\n# Or remove all at once:")
    print("cd", str(project_root))
    dirs_to_remove = " ".join([f"'datasets/{code.lower()}'" for code in orphaned])
    print(f"rm -rf {dirs_to_remove}")


def main():
    """Main analysis function."""
    print("WID Documentation Directory Analysis")
    print("="*70)
    
    # Get current state
    python_codes = get_wid_python_files()
    doc_codes = get_wid_documentation_dirs()
    
    # Find orphaned directories
    orphaned = find_orphaned_directories(python_codes, doc_codes)
    
    # Analyze and report
    orphaned = analyze_discrepancy(python_codes, doc_codes, orphaned)
    
    # Generate cleanup commands
    generate_cleanup_commands(orphaned)
    
    # Write orphaned list to file for potential cleanup script
    if orphaned:
        orphaned_file = project_root / "wid_orphaned_docs.txt"
        with open(orphaned_file, "w") as f:
            f.write("# Orphaned WID documentation directories\n")
            f.write(f"# Found {len(orphaned)} directories without corresponding Python files\n")
            f.write("# Generated by find_orphaned_wid_docs.py\n\n")
            for code in orphaned:
                f.write(f"{code}\n")
        
        print(f"\nOrphaned directories list saved to: {orphaned_file}")


if __name__ == "__main__":
    main()