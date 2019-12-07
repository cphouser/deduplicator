import os,sys
import filecmp
import inspect

def main():
    path_arg = sys.argv[1]
    #print(path)
    recScan(path_arg)
    #file_list = walkPath(path_arg)
    #ascending sort file list by size
    
    #file_list.sort(key=lambda x: x[1])
    #for entry, size, path in file_list:
    #    print(size, entry, path)
    #print('**condense list**')
    #condensed_list = condenseFileList(file_list)
    #print('**list condensed**')
    #for names, size, paths in condensed_list:
    #    print(size, names, paths)
    #    if type(names) is list:
    #        print(', '.join(names))
    #        for path in paths:
    #            print('--' + path)

def recScan(root):
    dir_list = os.scandir(root)
    directories = [entry for entry in dir_list if entry.is_dir()]
    for dir_entry in directories:
        print(dir_entry.name, dir_entry.path)
        #if 
        #dir_stat = dir_entry.stat()
        #print('|mode:', dir_stat.st_mode)
        #print('|size:', dir_stat.st_size)
        #print('|ctime:', dir_stat.st_ctime,
        #        'mtime:', dir_stat.st_mtime,
        #        'atime:', dir_stat.st_atime)
        #print('|owner uid:', dir_stat.st_uid, '\n')

def recPrint(root, indent=''): 
    print(indent + root)
    indent += '|'
    os.listdir(root)
    file_list = []
    dir_list = []
    for dir_entry in os.listdir(root):
        entry_path = os.path.join(root,dir_entry)
        if os.path.isfile(entry_path):
            file_list.append(dir_entry)
        if os.path.isdir(entry_path):
            dir_list.append(entry_path)
    for file_entry in file_list:
        print(indent + file_entry)
    else:
        print(indent + '_')
    for dir_entry in dir_list:
        recPrint(dir_entry, indent)

def walkPath(path_str):
    """Return list of all files in path_str and subdirectories
    
    Each item in returned list is a tuple (file_name, file_size, file_path)
    """
    walk_item = os.walk(path_str)
    file_list = []
    #print(walk_item)
    #print(repr(walk_item))
    for root, dirs, files in walk_item:
        #print(root, "\ndir list:", dirs, "\nfile list:", files)
        for file_entry in files:
            file_path = os.path.join(root,file_entry)
            file_size = os.path.getsize(file_path)
            file_list.append((file_entry, file_size, file_path))
    return file_list

def condenseFileList(file_list):
    condensed_list = [file_list.pop(0)]
    for f_name, f_size, f_path in file_list:
        if f_size == 0:
            condensed_list.append((f_name, f_size, f_path))
            continue
        other_name, other_size, other_path = condensed_list[-1]
        if f_size == other_size:
            if type(other_path) is list:
                print('aa')
                print('**', other_path[0], f_path)
                if filecmp.cmp(other_path[0], f_path, shallow=False):
                    condensed_list[-1] = (other_name.append(f_name),
                            f_size, other_path.append(f_path))
                continue
            else:
                print('bb')
                print(other_path, f_path)
                if filecmp.cmp(other_path, f_path, shallow=False):
                    condensed_list[-1] = ([other_name, f_name],
                            f_size, [other_path, f_path])
                    continue
        condensed_list.append((f_name, f_size, f_path))
    return condensed_list

if __name__ == '__main__':
    main()
