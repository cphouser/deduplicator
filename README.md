# Finding Duplicate Files in File Tree
Working project to summarize infomation for filesystem cleaning.

## Current Functionality
Tested with Python 3.5.3
```
python3 deduplicate.py path
```
Runs the scan for duplicate files in the directory *path*. Calculates a checksum of the first 4 MiB of each file at *path* and stores this along with each file's size in a *.deduplicator_record* file in the directory. Recursively generates this file for each subdirectory. Compares entries in these files to generate a list of duplicate files and a list of unique files. Store each of these lists in a *deduplicator_summary* file. If a directory already has a *.deduplicator_record* file, it doesn't generate a new one.

```
python3 deduplicate.py -r path
```
Runs the scan for duplicate files in the directory *path* as specified above but generates a *.deduplicator_record* file for each directory, regardless of whether one is already present. Renames the old file to *.deduplicator_record_prev* if found.

```
python3 deduplicate.py -c path
```
Deletes the *.deduplicator_record* and *.deduplicator_record_prev* files from directory *path* (if they exist) and from each nested subdirectory.

