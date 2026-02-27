#!/usr/bin/env python3
"""
Update test_obj_curated.csv with scenes from asset_samples/lvis_curated/
and remove any duplicate entries.

Usage:
    python update_curated_scenes.py
"""
import os
import csv
from pathlib import Path

# Paths
LVIS_DIR = Path("asset_samples/lvis_curated")
FILTERED_UIDS = "filtered_uids.csv"
TEST_OBJ_CURATED = "test_obj_curated.csv"
BACKUP_FILE = "test_obj_curated_backup.csv"

def load_existing_entries(filepath):
    """Load existing entries from test_obj_curated.csv"""
    existing_uids = set()
    existing_rows = []
    
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found, starting fresh")
        return existing_uids, existing_rows
    
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                uid = row[1]
                existing_uids.add(uid)
                existing_rows.append(','.join(row))
    
    return existing_uids, existing_rows

def get_lvis_scene_ids():
    """Get all scene IDs from lvis_curated directory"""
    scene_ids = set()
    
    if not LVIS_DIR.exists():
        print(f"Warning: {LVIS_DIR} not found")
        return scene_ids
    
    for img_file in LVIS_DIR.glob("*.png"):
        scene_id = img_file.stem  # Remove .png extension
        scene_ids.add(scene_id)
    
    return scene_ids

def load_filtered_uids():
    """Load filtered_uids.csv into a dict: {uid: full_entry}"""
    uid_to_entry = {}
    
    with open(FILTERED_UIDS, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                uid = row[1]
                uid_to_entry[uid] = ','.join(row)
    
    return uid_to_entry

def deduplicate_entries(entries):
    """Remove duplicate entries based on UID (second column)"""
    seen_uids = set()
    unique_entries = []
    duplicate_count = 0
    
    for entry in entries:
        parts = entry.split(',')
        if len(parts) >= 2:
            uid = parts[1]
            
            if uid in seen_uids:
                duplicate_count += 1
            else:
                seen_uids.add(uid)
                unique_entries.append(entry)
        else:
            unique_entries.append(entry)
    
    return unique_entries, duplicate_count

def main():
    print("=" * 70)
    print("Updating test_obj_curated.csv with curated scenes")
    print("=" * 70)
    
    # 1. Load existing entries
    existing_uids, existing_rows = load_existing_entries(TEST_OBJ_CURATED)
    print(f"\n✓ Loaded {len(existing_uids)} existing unique UIDs from {TEST_OBJ_CURATED}")
    
    # 2. Get all scene IDs from lvis_curated directory
    lvis_scene_ids = get_lvis_scene_ids()
    print(f"✓ Found {len(lvis_scene_ids)} scenes in {LVIS_DIR}")
    
    # 3. Load filtered_uids.csv
    uid_to_entry = load_filtered_uids()
    print(f"✓ Loaded {len(uid_to_entry)} entries from {FILTERED_UIDS}")
    
    # 4. Find new entries to add
    new_entries = []
    not_found = []
    
    for scene_id in sorted(lvis_scene_ids):
        # Check if already exists
        if scene_id in existing_uids:
            continue
        
        # Look up in filtered_uids.csv
        if scene_id in uid_to_entry:
            new_entries.append(uid_to_entry[scene_id])
        else:
            not_found.append(scene_id)
    
    print(f"\n✓ Found {len(new_entries)} new entries to add")
    if not_found:
        print(f"⚠ Warning: {len(not_found)} scene IDs not found in {FILTERED_UIDS}")
    
    # 5. Combine all entries
    all_entries = existing_rows + new_entries
    print(f"\n✓ Total entries before deduplication: {len(all_entries)}")
    
    # 6. Deduplicate
    unique_entries, duplicate_count = deduplicate_entries(all_entries)
    print(f"✓ Removed {duplicate_count} duplicate entries")
    print(f"✓ Final unique entries: {len(unique_entries)}")
    
    # 7. Backup original file if it exists
    if os.path.exists(TEST_OBJ_CURATED):
        import shutil
        shutil.copy(TEST_OBJ_CURATED, BACKUP_FILE)
        print(f"\n✓ Backed up original to {BACKUP_FILE}")
    
    # 8. Write deduplicated entries
    with open(TEST_OBJ_CURATED, 'w') as f:
        for entry in unique_entries:
            f.write(entry + '\n')
    
    print(f"✓ Updated {TEST_OBJ_CURATED}")
    
    print("\n" + "=" * 70)
    print(f"✅ Complete! {TEST_OBJ_CURATED} now has {len(unique_entries)} unique scenes")
    print("=" * 70)

if __name__ == "__main__":
    main()
