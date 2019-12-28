import os
import configparser

class DupFilters:
    def sortBy(self, name):
        sort_by = {
                'depth': self.subdirDepth
                , 'dlist': self.pathIncludes1
                , 'plist': self.pathIncludes0
                , 'length': self.pathFileLen
                , 'date': self.fileLastModified
                }
        return sort_by[name]

    def __init__(self, config_path):
        self.primary_list = []
        self.duplicate_list = []
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'sorting' in config:
            if 'primary directories' in config['sorting']:
                self.primary_list = config['sorting']['primary directories']
            if 'duplicate directories' in config['sorting']:
                self.duplicate_list = config['sorting']['duplicate directories']

    def pathIncludes1(self, path):
        def recrSplit(path_list, path):
            remaining, dir_name = os.path.split(path)
            if dir_name in path_list:
                return 1
            if len(remaining) == 0:
                return 0
            else: return recrSplit(path_list, remaining)
        #print(recrSplit(path_list, path))
        return recrSplit(self.duplicate_list, path)

    def pathIncludes0(self, path):
        def recrSplit(path_list, path):
            remaining, dir_name = os.path.split(path)
            if dir_name in path_list:
                return 0
            if len(remaining) == 0:
                return 1
            else: return recrSplit(path_list, remaining)
        #print(recrSplit(path_list, path))
        return recrSplit(self.primary_list, path)

    @staticmethod
    def pathFileLen(path):
        return len(os.path.basename(path))

    @staticmethod
    def fileLastModified(path):
        return os.stat(path).st_mtime

    @staticmethod
    def subdirDepth(path):
        def recrSplit(path):
            remaining, _ = os.path.split(path)
            if len(remaining) == 0:
                return 0
            else: return 1 + recrSplit(remaining)
        return recrSplit(path)

