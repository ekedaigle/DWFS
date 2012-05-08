import os

class FSPluginMetaclass(type):
    def __new__(cls, name, base, attr):
        attr['instance_count'] = 0
        return type.__new__(cls, name, base, attr)

# This is the base class for all plugins
class FSPlugin(object):
    __metaclass__ = FSPluginMetaclass
    instance_count = 0
    config_section = None
    config_keys = None

    @classmethod
    def addArguments(cls, parser):
        pass

    @classmethod
    def createFromArgs(cls, args):
        return []

    def __init__(self):
        self.instance_num = self.__class__.instance_count
        self.__class__.instance_count += 1
        pass

    def getConfigParams(self):
        if self.config_section and self.config_keys:
            section_name = ''.join([self.config_section, ' ', str(self.instance_num)])
            return (section_name, self.config_keys)
        else:
            return None

    def updateConfig(self, conifg):
        pass
    
    def getAllFiles(self):
        return []
    
    def containsFile(self, f):
        return False

    def canStoreFile(self, f):
        return False

    def createNewFile(self, name, mode, dev):
        pass
    
    def getAttributes(self, path):
        return None
    
    def changeMode(self, path, mode):
        pass
    
    def changeOwn(self, path, uid, gid):
        pass
    
    def fsync(self, path):
        pass
    
    def truncateFile(self, path, size):
        pass
    
    def deleteFile(self, path):
        pass
    
    def setTimes(self, path, times):
        pass

    def getFileHandle(self, path, flags):
        return open('/dev/null', flags)
