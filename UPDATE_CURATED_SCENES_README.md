# Update Curated Scenes Script

## Purpose
This script updates `test_obj_curated.csv` with scenes from `asset_samples/lvis_curated/` directory and automatically removes any duplicate entries.

## Usage

### Direct execution:
```bash
python3 update_curated_scenes.py
```

### Via setup.sh shortcut:
```bash
# The script is included in setup.sh
source setup.sh
# Or just the relevant line:
python3 update_curated_scenes.py
```

## What it does

1. **Scans** all PNG images in `asset_samples/lvis_curated/`
2. **Extracts** scene IDs from filenames (removes .png extension)
3. **Looks up** each scene ID in `filtered_uids.csv` to get the full entry (category,uid)
4. **Checks** against existing entries in `test_obj_curated.csv` to avoid duplicates
5. **Adds** new entries to `test_obj_curated.csv`
6. **Deduplicates** all entries based on UID (second column)
7. **Backs up** the original file to `test_obj_curated_backup.csv`
8. **Writes** the cleaned, deduplicated list back to `test_obj_curated.csv`

## Files

- **Input files:**
  - `asset_samples/lvis_curated/*.png` - Curated scene preview images
  - `filtered_uids.csv` - Master list of all valid scene entries
  - `test_obj_curated.csv` - Existing curated scene list

- **Output files:**
  - `test_obj_curated.csv` - Updated and deduplicated curated scene list
  - `test_obj_curated_backup.csv` - Backup of the previous version

## Example Output

```
======================================================================
Updating test_obj_curated.csv with curated scenes
======================================================================

✓ Loaded 2302 existing unique UIDs from test_obj_curated.csv
✓ Found 2442 scenes in asset_samples/lvis_curated
✓ Loaded 82575 entries from filtered_uids.csv

✓ Found 150 new entries to add
⚠ Warning: 140 scene IDs not found in filtered_uids.csv

✓ Total entries before deduplication: 2452
✓ Removed 50 duplicate entries
✓ Final unique entries: 2402

✓ Backed up original to test_obj_curated_backup.csv
✓ Updated test_obj_curated.csv

======================================================================
✅ Complete! test_obj_curated.csv now has 2402 unique scenes
======================================================================
```

## Notes

- The script always creates a backup before modifying `test_obj_curated.csv`
- Scene IDs that don't exist in `filtered_uids.csv` will be reported but skipped
- Duplicate entries are automatically removed (keeps the first occurrence)
- The script is idempotent - running it multiple times is safe
