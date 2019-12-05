import os,sys
import filecmp
import inspect

def main():
    path_arg = sys.argv[1]
    #print(path)
    #recPrint(path)
    file_list = []
    walkPath(path_arg, file_list)
    #ascending sort file list by size
    file_list.sort(key=lambda x: x[2])
    for entry, path, size in file_list:
        print(size, entry, path)
    print('**condense list**')
    condensed_list = condenseFileList(file_list)
    print('**list condensed**')
    for names, paths, size in condensed_list:
        if type(names) is list:
            print(', '.join(names))
            for path in paths:
                print('--' + path)
        
def walkPath(path_str, file_list):
    walk_item = os.walk(path_str)
    #print(walk_item)
    #print(repr(walk_item))
    for root, dirs, files in walk_item:
        print(root, "\ndir list:", dirs, "\nfile list:", files)
        for file_entry in files:
            file_path = os.path.join(root,file_entry)
            file_size = os.path.getsize(file_path)
            file_list.append((file_entry, file_path, file_size))

def condenseFileList(file_list):
    condensed_list = [file_list.pop(0)]
    for f_name, f_path, f_size in file_list:
        if f_size == 0:
            condensed_list.append((f_name, f_path, f_size))
            continue
        other_name, other_path, other_size = condensed_list[-1]
        if f_size == other_size:
            if type(other_path) is list:
                print('**', other_path[0], f_path)
                if filecmp.cmp(other_path[0], f_path, shallow=False):
                    condensed_list[-1] = (other_name.append(f_name),
                            other_path.append(f_path), f_size)
                continue
            else:
                print(other_path, f_path)
                if filecmp.cmp(other_path, f_path, shallow=False):
                    condensed_list[-1] = ([other_name, f_name],
                            [other_path, f_path], f_size)
                    continue
        condensed_list.append((f_name, f_path, f_size))
    return condensed_list
            
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
        print(indent + '..')
    for dir_entry in dir_list:
        recPrint(dir_entry, indent)

if __name__ == '__main__':
    main()
