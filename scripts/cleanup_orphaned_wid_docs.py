#!/usr/bin/env python3
"""
Clean up orphaned WID documentation directories that don't have corresponding Python cleaner files.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_orphaned_directories() -> List[str]:
    """Load the list of orphaned directories from the analysis file."""
    orphaned_file = project_root / "wid_orphaned_docs.txt"
    
    if not orphaned_file.exists():
        print(f"Error: Orphaned directories file {orphaned_file} not found.")
        print("Run find_orphaned_wid_docs.py first to generate the list.")
        sys.exit(1)
    
    orphaned = []
    with open(orphaned_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                orphaned.append(line)
    
    print(f"Loaded {len(orphaned)} orphaned documentation directories")
    return orphaned


def analyze_orphaned_directories(orphaned: List[str]):
    """Analyze the orphaned directories before deletion."""
    print("\n" + "="*60)
    print("ORPHANED WID DOCUMENTATION CLEANUP")
    print("="*60)
    
    # Group by family
    families = {}
    for code in orphaned:
        parts = code.split("_")
        if len(parts) >= 2:
            family = parts[1]  # WID_FAMILY_...
            if family not in families:
                families[family] = []
            families[family].append(code)
    
    print(f"Total orphaned directories: {len(orphaned)}")
    print(f"Families affected: {len(families)}")
    
    print("\nBreakdown by family:")
    for family, codes in sorted(families.items()):
        print(f"  {family}: {len(codes)} directories")
    
    print(f"\nThese directories will be permanently deleted:")
    for code in sorted(orphaned):
        doc_path = project_root / "datasets" / code.lower()
        print(f"  {doc_path}")
    
    return families


def confirm_deletion(orphaned: List[str]) -> bool:
    """Ask user to confirm deletion of orphaned directories."""
    print(f"\n" + "="*60)
    print("CONFIRMATION REQUIRED")
    print("="*60)
    print(f"You are about to delete {len(orphaned)} orphaned documentation directories.")
    print("These directories contain documentation for datasets that no longer have")
    print("corresponding Python cleaner files (likely removed in previous cleanup).")
    print()
    print("This action cannot be undone.")
    
    response = input(f"\nProceed with deletion of {len(orphaned)} directories? (yes/no): ").strip().lower()
    return response == "yes"


def delete_orphaned_directories(orphaned: List[str]) -> Dict:
    """Delete the orphaned documentation directories."""
    summary = {
        "deleted": [],
        "failed": [],
        "not_found": []
    }
    
    print("\nStarting deletion process...")
    
    for code in orphaned:
        doc_path = project_root / "datasets" / code.lower()
        
        try:
            if doc_path.exists():
                shutil.rmtree(doc_path)
                summary["deleted"].append(str(doc_path))
                print(f"  Deleted: {code.lower()}")
            else:
                summary["not_found"].append(str(doc_path))
                print(f"  Not found: {code.lower()}")
        except Exception as e:
            summary["failed"].append(f"{code}: {e}")
            print(f"  Error deleting {code}: {e}")
    
    return summary


def write_cleanup_summary(summary: Dict, orphaned: List[str]):
    """Write a summary of the cleanup operation."""
    summary_file = project_root / "wid_orphaned_docs_cleanup_summary.txt"
    
    with open(summary_file, "w") as f:
        f.write("WID ORPHANED DOCUMENTATION CLEANUP SUMMARY\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Directories deleted: {len(summary['deleted'])}\n")
        f.write(f"Directories failed: {len(summary['failed'])}\n")
        f.write(f"Directories not found: {len(summary['not_found'])}\n")
        
        total_attempted = len(orphaned)
        total_successful = len(summary['deleted'])
        
        f.write(f"\nTOTAL ATTEMPTED: {total_attempted}\n")
        f.write(f"TOTAL SUCCESSFUL: {total_successful}\n")
        f.write(f"SUCCESS RATE: {(total_successful/total_attempted)*100:.1f}%\n")
        
        # Write deleted directories list
        if summary['deleted']:
            f.write(f"\nSuccessfully Deleted ({len(summary['deleted'])}):\n")
            for path in sorted(summary['deleted']):
                f.write(f"  {path}\n")
        
        # Write failure details if any
        if summary['failed']:
            f.write(f"\nFailed Deletions ({len(summary['failed'])}):\n")
            for failure in summary['failed']:
                f.write(f"  {failure}\n")
        
        if summary['not_found']:
            f.write(f"\nDirectories Not Found ({len(summary['not_found'])}):\n")
            for path in sorted(summary['not_found']):
                f.write(f"  {path}\n")
    
    print(f"\nCleanup summary written to: {summary_file}")
    return summary_file


def main():
    """Main cleanup function."""
    print("WID Orphaned Documentation Cleanup Script")
    print("="*60)
    
    # Load orphaned directories list
    orphaned = load_orphaned_directories()
    
    if not orphaned:
        print("No orphaned directories found. Nothing to clean up!")
        return
    
    # Analyze what will be deleted
    families = analyze_orphaned_directories(orphaned)
    
    # Confirm deletion
    if not confirm_deletion(orphaned):
        print("Cleanup cancelled by user.")
        return
    
    # Perform deletion
    summary = delete_orphaned_directories(orphaned)
    
    # Write summary
    summary_file = write_cleanup_summary(summary, orphaned)
    
    # Final report
    print("\n" + "="*60)
    print("CLEANUP COMPLETE")
    print("="*60)
    
    total_deleted = len(summary['deleted'])
    total_failed = len(summary['failed'])
    
    print(f"Successfully deleted: {total_deleted} directories")
    if total_failed > 0:
        print(f"Failed deletions: {total_failed} (see {summary_file} for details)")
    
    print(f"\nThe datasets/ and sspi_flask_app/api/core/datasets/ directories")
    print(f"should now be in sync for WID datasets.")
    print("\nYou can verify with: python scripts/find_orphaned_wid_docs.py")
    print("You can review changes with: git status")


if __name__ == "__main__":
    main()