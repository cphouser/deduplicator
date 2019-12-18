# Finding Duplicate Files in File Tree
Working project to summarize infomation and provide macros for filesystem cleaning.

## Current Functionality
Tested with Python 3.5.3
```
usage: deduplicate.py [-h] [-s {depth,list}] [-a] [-e]
                      {build,list,delete,clean} path [{full,light,none}]

optional arguments:
  -h, --help            show this help message and exit
  -e, --emptysearch     report list of all empty directories at path

general:
  {build,list,delete,clean}
                        Mode to operate the script in
                        build   Write a deduplicator_summary file
                                identifying duplicate files
                        list    Sort and list the results in the
                                deduplicator_summary file
                        delete  Sort and delete duplicates in the
                                deduplicator_summary file
                        clean   Remove all .deduplicator_record and
                                .deduplicator_record_prev files
  path                  Directory to find duplicates within

build options:
  {full,light,none}     options for building a new deduplicator_summary

list/delete options:
  -s {depth,list}, --sort {depth,list}
                        Specify a rule for sorting the paths of a duplicate
                        file. Paths with lower values are considered the
                        file's primary location.
                        depth   The number of nested directories in a file
                                path
                        list    1 if a file path contains directories listed
                                in deduplicate.ini
                        length  The length of the filename in each path
  -a, --all             consider all paths with the lowest sort value to be
                        a primary location
```
the file *deduplicate.ini* is checked for in the same directory as *deduplicate.py*
## Some Examples
```
python3 deduplicate.py build <path>
```
Runs the scan for duplicate files in the directory *path*. Calculates a checksum of the first 4 MiB of each file at *path* and stores this along with each file's size in a *.deduplicator_record* file in the directory. Recursively generates this file for each subdirectory. Compares entries in these files to generate a list of duplicate files and a list of unique files. Store each of these lists in a *deduplicator_summary* file. If a directory already has a *.deduplicator_record* file, it doesn't generate a new one.

```
python3 deduplicate.py build <path> full
```
Runs the scan for duplicate files in the directory *path* as specified above but generates a *.deduplicator_record* file for each directory, regardless of whether one is already present. Renames the old file to *.deduplicator_record_prev* if found.

```
python3 deduplicate.py build <path> light
```
Runs the scan for duplicate files in the directory *path* as specified above but reads the current *.deduplicator_record* file for each directory if found. Skip scan for any file already in the record and use that data for rebuilding the file.

```
python3 deduplicate.py clean path
```
Deletes the *.deduplicator_record* and *.deduplicator_record_prev* files from directory *path* (if they exist) and from each nested subdirectory.

