import deduplicate
import argparse
import shutil

def main():
    parser = argparse.ArgumentParser(description=
            'Find all empty directories (paths with no files after them)')
    parser.add_argument('path', help='Path to search after')
    parser.add_argument('-d', action='store_true', help=
            'Delete all empty directories')
    args = parser.parse_args()
    delete_flag = args.d
    emptydirs = emptyDirSearch(args.path)
    print('Empty Directories', *emptydirs, sep='\n-\t')
    if delete_flag:
        deleteDirs(emptydirs)

def deleteDirs(dir_list):
    def deletePath(path_arg):
        dirs, files, symlinks = deduplicate.scanDir(path_arg)
        #print('[F:{}]\t[D:{}]\tat path {}'.format(len(files), len(dirs)
        #    , path_arg))
        if len(files) != 0:
            return False
        for entry in symlinks:
            print('symlink:', entry.name)
        if all([deletePath(entry.path) for entry in dirs]):
            print('deleting', path_arg) 
            shutil.rmtree(path_arg)
            return True
        else: return False
    for dir_path in dir_list:
        if not deletePath(dir_path):
            print('COULD NOT DELETE:', dir_path)

    

def emptyDirSearch(path_arg):
    dirs, files, symlinks = deduplicate.scanDir(path_arg)
    empty_dirs = []
    current_empty = True
    #print('[F:{}]\t[D:{}]\tat path {}'.format(len(files), len(dirs)
    #    , path_arg))
    for entry in symlinks:
        print('symlink:', entry.name)
    for entry in dirs:
        result_list = emptyDirSearch(entry.path)
        if entry.path not in result_list:
            current_empty = False
        empty_dirs.extend(result_list)
    if len(files) != 0:
        current_empty = False
    if current_empty: return [path_arg]
    else: return empty_dirs

if __name__ == '__main__':
    main()
