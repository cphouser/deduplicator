import os,sys
import filecmp
import csv
import zlib
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from operator import itemgetter
import yaml
import argparse
import configparser

SCAN_RECORD = '.deduplicator_record'
PREV_SCAN_RECORD = '.deduplicator_record_prev'
CONFIG_FILE = 'deduplicate.ini'
SCAN_SUMMARY = 'deduplicator_summary'
PREV_SCAN_SUMMARY = 'deduplicator_summary_prev'
RECORD_FIELDNAMES = ['name', 'size', 'csum', 'm_time', 'dups']
max_checksum_mb = 4
FileRecord = namedtuple('FileRecord', RECORD_FIELDNAMES)

def main():
    modeparser = argparse.ArgumentParser(add_help=False)
    modegroup = modeparser.add_argument_group('general')
    modegroup.add_argument('mode', choices=['build','list','delete','clean']
            , help='''Mode to operate the script in \
                    \nbuild\tWrite a {} file \n\tidentifying duplicate files \
                    \nlist\tSort and list the results in the \n\t{} file \
                    \ndelete\tSort and delete duplicates in the \n\t{} file \
                    \nclean\tRemove all {} and \n\t{} files'''.format(
                        SCAN_SUMMARY, SCAN_SUMMARY, SCAN_SUMMARY
                        , SCAN_RECORD, PREV_SCAN_RECORD))
                    
    modegroup.add_argument('path', help='Directory to find duplicates within')

    buildparser = argparse.ArgumentParser(add_help=False)
    buildgroup = buildparser.add_argument_group('build options')
    buildgroup.add_argument('rescan', choices=['full','light','none']
            , default='none', nargs='?', help=
            'options for building a new {}'.format(SCAN_SUMMARY))

    listparser = argparse.ArgumentParser(add_help=False)
    listgroup = listparser.add_argument_group('list/delete options')
    listgroup.add_argument('-s', '--sort'
            , choices=['depth', 'list', 'length', 'date'], help=
            '''Specify a rule for sorting the paths of a duplicate 
file. Paths with lower values are considered the  
file\'s primary location. 
depth\tThe number of nested directories in a file 
\tpath 
list\t1 if a file path contains directories listed 
\tin deduplicate.ini
length\tThe length of the filename in each path
date\tThe last modified value of the file''')
    listgroup.add_argument('-a', '--all', action='store_true', help=
            '''consider all paths with the lowest sort value to be
a primary location''')
    listgroup.add_argument('-p', '--printall', action='store_true', help=
            '''when listing duplicates, print entries where all 
copies are primary''')

    parser = argparse.ArgumentParser(parents=[modeparser, buildparser
        , listparser]
            #, usage='%(prog)s build|list|delete|clean [options]'
            , formatter_class=argparse.RawTextHelpFormatter)
    #parser.add_argument('-e', '--emptysearch', action='store_true', help=
    #        'report list of all empty directories at path')
    args = parser.parse_args()
    path_arg = args.path
    print(args)
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(sys.argv[0]),CONFIG_FILE))

    #if args.emptysearch:
    #    print('empty directories: [warning: false positives!]')
    #    emptyDirSearch(path_arg)
    if args.mode == 'clean':
        print('clean', path_arg)
        removeScanFiles(path_arg)
    elif args.mode == 'build':
        print('building scan records')

        if args.rescan == 'none':
            recrScan(path_arg)
        elif args.rescan == 'light':
            recrReScan(path_arg)
        elif args.rescan == 'full':
            recrScan(path_arg, rescan=True)

        print('checking for duplicates')
        # add duplicates to each scan record
        file_dict = recrDupSearch(path_arg)

        print('writing summary file to ', os.path.join(path_arg, SCAN_SUMMARY))
        # write summary for found duplicates
        writeSummary(path_arg, file_dict)
    else:
        print('read {} from {} and {} duplicates by {}'.format(
            SCAN_SUMMARY, path_arg, args.mode, args.sort))
        d_flag = False
        if args.mode == 'delete': d_flag = True
        if args.all == True:
            print('keep all minimum files')

        dup_dict = readSummary(path_arg)
        print('{} unique files in {} paths'.format(len(dup_dict),
            sum([len(paths) for paths in dup_dict.values()])))
        print('summarizing list of duplicate directories')
        dup_dirs, file_dups = condenseDups(dup_dict)
        #print('{} unique files\tin {} paths'.format(len(file_dups),
        #    sum([len(paths) for _, _, paths in file_dups])))

        if args.sort == 'list':
            if 'sorting' in config:
                dir_list = config['sorting']['duplicate directories'].split(
                        '\n')
                print(dir_list)
            printCondensed(dup_dirs, file_dups, d_flag, args.all, args.printall
                    , lambda path: pathIncludes(dir_list, path))
        elif args.sort == 'depth':
            printCondensed(dup_dirs, file_dups, d_flag, args.all, args.printall
                    , subdirDepth)
        elif args.sort == 'length':
            printCondensed(dup_dirs, file_dups, d_flag, args.all, args.printall
                    , pathFileLen)
        elif args.sort == 'date':
            printCondensed(dup_dirs, file_dups, d_flag, args.all, args.printall
                    , fileLastModified)

def deleteTailFiles(dup_list, path_sort_func):
    #print(*dup_list, sep='\n')
    for csum, size, paths in dup_list:
        paths.sort(key=lambda x: x.lower(), reverse=True)
        paths.sort(key=path_sort_func, reverse=True)
        remaining_copy = paths.pop()
        #print('for file {}'.format(remaining_copy))
        for path in paths:
            try:
                os.remove(path)
            except FileNotFoundError:
                print('deletion warning: could not find {}'.format(path))
    #dup_list.sort(key=lambda x: x[2][0].lower())
    #print('sorted entries', *dup_list, sep='\n')
    
def printCondensed(dup_dirs, file_dups, d_flag, a_flag, p_flag, path_sort_func):
    print('duplicate directories')
    dup_dirs.sort(key=lambda x: x[0].lower())
    print(*dup_dirs, sep='\n')

    for csum, size, paths in file_dups:
        paths.sort(key=lambda x: x.lower(), reverse=True)
        paths.sort(key=path_sort_func, reverse=True)
        prim_paths = [paths.pop()]
        if a_flag and not all([path_sort_func(path) == 1 for path in paths]):
            while len(paths) > 0 and (path_sort_func(prim_paths[0]) 
                    == path_sort_func(paths[-1])):
                prim_paths.append(paths.pop())
        if len(paths) > 0 or p_flag:
            print('primary copies:',*prim_paths, sep='\n\t')
        if len(paths) > 0:
            print('duplicate copies:' + ('[DELETED]' if d_flag else '')
                    , *paths, sep='\n\t')
        if d_flag:
            for path in paths:
                try:
                    os.remove(path)
                except FileNotFoundError:
                    print('deletion warning: could not find {}'.format(path))

def pathIncludes(path_list, path):
    def recrSplit(path_list, path):
        remaining, dir_name = os.path.split(path)
        if dir_name in path_list:
            return 1
        if len(remaining) == 0:
            return 0
        else: return recrSplit(path_list, remaining)
    #print(recrSplit(path_list, path))
    return recrSplit(path_list, path)

def pathFileLen(path):
    return len(os.path.basename(path))

def fileLastModified(path):
    return os.stat(path).st_mtime

def subdirDepth(path):
    def recrSplit(path):
        remaining, _ = os.path.split(path)
        if len(remaining) == 0:
            return 0
        else: return 1 + recrSplit(remaining)
    return recrSplit(path)

def condenseDups(dup_dict):
    local_duplicates = []
    dup_dirs = []
    misc_duplicates = []
    for (csum, size), path_list in dup_dict.items():
        dir_list = [os.path.dirname(path) for path in path_list]
        if len(set(dir_list)) == 1:
            #print('local duplicate',*path_list, sep='\n')
            local_duplicates.append((csum, size, path_list))
            continue
        #if len(set(dir_list)) < len(dir_list):
        #    print('mixed local duplicate',*path_list, sep='\n')
            #continue

        part_of_dup_dir = False
        for dir_path in dir_list:
            if dir_path in [dup_dir[0] for dup_dir in dup_dirs]:
                #print(dir_path, 'in duplicate dir list')
                part_of_dup_dir = True
                break
        if part_of_dup_dir:
            misc_duplicates.append((csum, size, path_list))
            continue

        file_dict_list = [(loadScanRecordAsDict(path), path) 
                for path in set(dir_list)]
        duplicate_dirs = compareFileDicts(file_dict_list)
        if len(duplicate_dirs) == 0:
            misc_duplicates.append((csum, size, path_list))
        else:
            dup_dirs.extend(duplicate_dirs)
            misc_duplicates.append((csum, size, path_list))
    return (dup_dirs, local_duplicates + misc_duplicates)

def compareFileDicts(dict_list):
    '''list of tuples (x,y) where dir y has all files in dir x'''
    dict_list.sort(key=lambda file_dict: len(file_dict[0]))
    #print([len(file_dict[0]) for file_dict in dict_list])
    file_dict, path = dict_list.pop(0)
    dup_dirs = []
    for other_dict, other_path in dict_list:
        if subsetDict(file_dict, other_dict):
            dup_dirs.append((path, other_path))
    return dup_dirs

def subsetDict(sub_dict, file_dict):
    for key in sub_dict:
        if key in file_dict:
            continue
        else:
            return False
    return True

def removeScanFiles(path):
    dir_list, _, _ = scanDir(path)
    for dir_entry in dir_list:
        removeScanFiles(dir_entry.path)
    try:
        os.remove(os.path.join(path, SCAN_RECORD))
    except FileNotFoundError:
        print(SCAN_RECORD, 'not found in', path)
    try:
        os.remove(os.path.join(path, PREV_SCAN_RECORD))
    except FileNotFoundError:
        print(PREV_SCAN_RECORD, 'not found in', path)

def readSummary(s_path):
    dup_dict = {}
    with open(os.path.join(s_path,SCAN_SUMMARY), newline='') as sum_file:
        yaml_obj = yaml.load_all(sum_file)
        unique_list = next(yaml_obj)
        for path, size, csum in unique_list:
            mergeFileDict(dup_dict, {(csum, size): [path]})   
        #print(*dup_dict.items(), sep='\n')
    return dup_dict

def writeSummary(s_path, file_dict):
    dup_list = []
    unique_list = []
    for (chksm, size), dups in file_dict.items():
        if len(dups) > 1:
            for path in dups:
                #name = os.path.basename(path)
                dup_list.append((path, size, chksm))
        else:
            #name = os.path.basename(dups[0])
            unique_list.append((dups[0], size, chksm))
    
    dup_list.sort(key=itemgetter(1), reverse=True)
    unique_list.sort(key=itemgetter(1), reverse=True)
    with open(os.path.join(s_path,SCAN_SUMMARY), 'w', newline='') as sum_file:
        yaml.dump_all((dup_list, unique_list), sum_file)

    #print('duplicate list')
    #print(yaml.dump_all((dup_list, unique_list)))
    #print('unique list')
    #print(*unique_list, sep='\n')

def recrDupSearch(path):
    dir_list, _, _ = scanDir(path)
    subdir_file_dict = {}
    for dir_entry in dir_list:
        mergeFileDict(subdir_file_dict, recrDupSearch(dir_entry.path))
    resaveScanRecord(path, subdir_file_dict)

    #margin_len = path.count('/')
    #margin = ''
    #for i in range(margin_len):
    #    margin = margin + ' '
    #print(margin+path)
    #print(margin+str(empty_file_list), *local_file_dict.items()
    #        , sep='\n'+margin)
    local_file_dict = loadScanRecordAsDict(path)
    mergeFileDict(local_file_dict, subdir_file_dict)
    return local_file_dict

def resaveScanRecord(path, subdir_file_dict):
    '''Open a SCAN_RECORD from the path and use the data while rewriting it.

    For each entry in subdir_file_dict, create a FileRecord using previous
    SCAN_RECORD data if it exists for the file.
    '''
    record_path = os.path.join(path, SCAN_RECORD)
    fr_list = []
    with open(record_path, newline='') as scanrecord_csv:
        reader = csv.DictReader(scanrecord_csv, fieldnames=RECORD_FIELDNAMES)
        for row in reader:
            fr = FileRecord(row['name'], int(row['size']), int(row['csum'])
                , float(row['m_time']), [])
            fr_list.append(fr)
    for fr in fr_list:
        if fr.size == 0:
            continue
        if (fr.csum, fr.size) in subdir_file_dict:
            dup_list = subdir_file_dict[fr.csum, fr.size]
            for dup_path in dup_list:
                dup_relpath = os.path.relpath(dup_path, path)
                fr.dups.append(dup_relpath)
    listToFile(record_path, fr_list)

def loadScanRecordAsDict(path):
    """load a SCAN_RECORD in directory 'path' and return entries as dict

    exclude all empty files. Keys in dict are tuples (file_chksum, file_size)
    and values are singleton lists of relative paths to each file.
    """
    record_path = os.path.join(path, SCAN_RECORD)
    file_dict = {}
    #empty_file_list = []
    with open(record_path, newline='') as scanrecord_csv:
        reader = csv.DictReader(scanrecord_csv, fieldnames=RECORD_FIELDNAMES)
        for row in reader:
            file_path = os.path.join(path, row['name'])
            if row['size'] != '0':
            #    empty_file_list.append(file_path)
            #else:
            #    file_dict.update({(int(row['csum']), int(row['size'])): 
            #        [file_path]})
                mergeFileDict(file_dict,
                        {(int(row['csum']), int(row['size'])): [file_path]})
    return file_dict

def mergeFileDict(root_dict, sub_dict):
    """modify root_dict to add items from sub_dict. assume values are lists.
    
    if a key exists in both, extend value of the key in root_dict with the 
    value in sub_dict
    """
    for key, paths in sub_dict.items():
        if key in root_dict:
            r_paths = root_dict[key]
            r_paths.extend(paths)
        else:
            root_dict.update({key: paths})

def recrReScan(root):
    """store a csv SCAN_RECORD at path 'root' and in all of its subdirectories

    fields defined by RECORD_FIELDNAMES, rows list each file located in the
    directory. dups field is not populated. If a SCAN_RECORD is already
    present in the directory, Use file data from that file in building the new
    SCAN_RECORD
    """
    dir_list, file_list, sym_list = scanDir(root)
    # build SCAN_RECORD in 'root'
    # 1) make sure subdirectories have SCAN_RECORDs
    for dir_entry in dir_list:
        recrReScan(dir_entry.path)
    # check for an existing SCAN_RECORD
    dedup_record_path = os.path.join(root, SCAN_RECORD)
    if os.path.isfile(dedup_record_path):
        #load scan_record as fileRecord list
        fr_list = []
        sr_dict = loadScanRecordAsNameDict(root)
        for dir_entry in file_list:
            if dir_entry.name in sr_dict:
                size, csum, mtime, _ = sr_dict[dir_entry.name]
                fr_list.append(
                        FileRecord(dir_entry.name, size, csum, mtime, []))
            else:
                print('no entry for', dir_entry.name)
                fr_list.append(fileData(dir_entry))


    else:
        # 2) fill initial SCAN_RECORD for this folder
        print('building record for {} [{} files]'.format(root, len(file_list)))
        fr_list = [fileData(dir_entry) for dir_entry in file_list]
    fr_list.sort(key=lambda x: x.size)
    listToFile(dedup_record_path, fr_list)

def loadScanRecordAsNameDict(path):
    """load a SCAN_RECORD in directory 'path' and return entries as dict

    exclude all empty files. Keys in dict are the names of each file
    and values are the other entries in the row
    """
    record_path = os.path.join(path, SCAN_RECORD)
    file_dict = {}
    #empty_file_list = []
    with open(record_path, newline='') as scanrecord_csv:
        reader = csv.DictReader(scanrecord_csv, fieldnames=RECORD_FIELDNAMES)
        for row in reader:
            file_dict.update({row['name']: (int(row['size']), int(row['csum'])
                , float(row['m_time']), row['dups'])})
    return file_dict

def recrScan(root, rescan=False):
    """store a csv SCAN_RECORD at path 'root' and in all of its subdirectories

    fields defined by RECORD_FIELDNAMES, rows list each file located in the
    directory. dups field is not populated. If rescan is False, ignore paths
    that alread have a SCAN_RECORD
    """
    # check for an existing SCAN_RECORD
    dedup_record_path = os.path.join(root, SCAN_RECORD)
    if os.path.isfile(dedup_record_path):
        if rescan == True:
            old_path = os.path.join(root, PREV_SCAN_RECORD)
            os.replace(dedup_record_path, old_path)
        else:
            print(dedup_record_path, '\n\tfound! using previous results')
            return
    else:
        print(dedup_record_path, '\n\tdoesn\'t exist! (new dir found)')

    # build SCAN_RECORD in 'root'
    dir_list, file_list, sym_list = scanDir(root)
    # 1) make sure subdirectories have SCAN_RECORDs
    for dir_entry in dir_list:
        recrScan(dir_entry.path, rescan=rescan)
    # 2) fill initial SCAN_RECORD for this folder
    print('building record for {} [{} files]'.format(root, len(file_list)))
    fr_list = [fileData(dir_entry) for dir_entry in file_list]
    fr_list.sort(key=lambda x: x.size)
    listToFile(dedup_record_path, fr_list)

def listToFile(save_path, filerecord_list):
    """save a list of FileRecord objects to save_path/SCAN_RECORD

    Assume save_path points to a directory. Clobber any existing
    SCAN_RECORD
    """
    #print(save_path)
    with open(save_path, mode='w', newline='') as scanrecord_csv:
        writer = csv.DictWriter(scanrecord_csv, fieldnames=RECORD_FIELDNAMES)
        for filerecord in filerecord_list:
            writer.writerow(filerecord._asdict())
        
def fileData(dir_entry):
    """return a FileRecord of the corresponding directory entry

    Assume dir_entry points to a file. Populate 'dups' field w/ empty list
    """
    file_stat = dir_entry.stat()
    #print('scanning {} at {}. size: {}'.format(dir_entry.name, dir_entry.path,
    #    file_stat.st_size))
    return FileRecord(name=dir_entry.name, size=file_stat.st_size
            , csum=crc32(dir_entry.path)
            , m_time=file_stat.st_mtime, dups=[])

def crc32(filename):
    """open specified file and calculate crc32, return as hex string

    copied from CrouZ's answer: 
    stackoverflow.com/questions/1742866/compute-crc-of-file-in-python
    """
    max_chunks = max_checksum_mb * 16
    fh = open(filename, 'rb')
    result = 0
    for i in range(max_chunks):
        #read in 64 kb chunks
        s = fh.read(65536)
        if not s:
            break
        result = zlib.crc32(s, result)
    fh.close()
    #print(hex(result))
    #return "%08X" % (result & 0xFFFFFFFF)
    return result

def scanDir(root):
    """return a 3-tuple of directories, files, and symlinks in dir_path

    each item is a list of dirEntry objects as returned by os.scanDir()
    entries with name matching SCAN_RECORD are not included in file list
    entries in directories and files are not symbolic links. 
    entries in symlinks may link to either directories or files
    """
    dir_list = os.scandir(root)
    directories = []
    files = []
    symlinks = []
    for entry in dir_list:
        if entry.is_dir(follow_symlinks=False):
            directories.append(entry)
        elif entry.is_file(follow_symlinks=False):
            if (entry.name != SCAN_RECORD
                    and entry.name != PREV_SCAN_RECORD):
                files.append(entry)
        elif entry.is_symlink():
            symlinks.append(entry)
    return (directories, files, symlinks)
    
if __name__ == '__main__':
    main()
