#!/usr/bin/env python
import fuse

import logging
from stat import *
import os
import errno # these must be returned as negatives
import verbose
verbose.print_func = logging.info

from FSPlugin import FSPlugin

def getDepth(path):
    """
    Return the depth of a given path, zero-based from root ('/')
    """
    if path == '/':
        return 0
    else:
        return path.count('/')

def find_subclasses(path, cls):
    """
    Find all subclass of cls in py files located below path
    (does look in sub directories)
 
    @param path: the path to the top level folder to walk
    @type path: str
    @param cls: the base class that all subclasses should inherit from
    @type cls: class
    @rtype: list
    @return: a list if classes that are subclasses of cls
    """
 
    subclasses=[]
 
    def look_for_subclass(modulename):
        module=__import__(modulename)
 
        #walk the dictionaries to get to the last one
        d=module.__dict__
        for m in modulename.split('.')[1:]:
            d=d[m].__dict__
 
        #look through this dictionary for things
        #that are subclass of Job
        #but are not Job itself
        for key, entry in d.items():
            if key == cls.__name__:
                continue
 
            try:
                if issubclass(entry, cls):
                    subclasses.append(entry)
            except TypeError:
                #this happens when a non-type is passed in to issubclass. We
                #don't care as it can't be a subclass of Job if it isn't a
                #type
                continue
 
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".py") and not name.startswith("__"):
                path = os.path.join(root, name)
                modulename = path.rsplit('.', 1)[0].replace('/', '.')
                look_for_subclass(modulename)
 
    return subclasses

class DWFS(fuse.Fuse):

    def __init__(self, plugins, *args, **kw):
        fuse.Fuse.__init__(self, *args, **kw)
        self.cwd = os.path.abspath(os.getcwd())
        self.plugins = plugins
        self.open_files = dict()

        logging.info('Initialized with %i plugins' % len(self.plugins))
    
    def fsinit(self):
        os.chdir(self.cwd)

    @verbose.verbose
    def getattr(self, path):
        """
        - st_mode (protection bits)
        - st_ino (inode number)
        - st_dev (device)
        - st_nlink (number of hard links)
        - st_uid (user ID of owner)
        - st_gid (group ID of owner)
        - st_size (size of file, in bytes)
        - st_atime (time of most recent access)
        - st_mtime (time of most recent content modification)
        - st_ctime (platform dependent; time of most recent metadata change on Unix,
                    or the time of creation on Windows).
        """

        os_stat = None

        if path == '/':
            os_stat = os.stat('.')
        else:
            for plugin in self.plugins:
                if plugin.containsFile(path):
                    os_stat = plugin.getAttributes(path)
                    break

        if os_stat != None:
            st = fuse.Stat()
            st.st_mode = os_stat[ST_MODE]
            st.st_ino = os_stat[ST_INO]
            st.st_dev = os_stat[ST_DEV]
            st.st_nlink = os_stat[ST_NLINK]
            st.st_uid = os_stat[ST_UID]
            st.st_gid = os_stat[ST_GID]
            st.st_size = os_stat[ST_SIZE]
            st.st_atime = os_stat[ST_ATIME]
            st.st_mtime = os_stat[ST_MTIME]
            st.st_ctime = os_stat[ST_CTIME]
            return st
        else:
            return -errno.ENOENT

    @verbose.verbose
    def readdir(self, path, offset):
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        for plugin in self.plugins:
            if plugin.containsFile(path):
                for f in plugin.readdir(path):
                    yield fuse.Direntry(f.split('/')[-1])

    @verbose.verbose
    def getdir(self, path):
        """
        return: [[('file1', 0), ('file2', 0), ... ]]
        """

        return -errno.ENOSYS

    @verbose.verbose
    def mythread ( self ):
        return -errno.ENOSYS

    @verbose.verbose
    def chmod ( self, path, mode ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.changeMode(path, mode)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def chown ( self, path, uid, gid ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.changeOwn(path, uid, gid)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def fsync ( self, path, isFsyncFile ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.fsync(path)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def link ( self, targetPath, linkPath ):
        return -errno.ENOSYS

    @verbose.verbose
    def mkdir ( self, path, mode ):
        return -errno.ENOSYS

    @verbose.verbose
    def mknod ( self, path, mode, dev ):
        if getDepth(path) != 1:
            return -errno.ENOSYS

        for plugin in self.plugins:
            if plugin.canStoreFile(path):
                plugin.createNewFile(path.replace('/', ''), mode, dev)
                break
        
        return 0

    @verbose.verbose
    def readlink ( self, path ):
        return -errno.ENOSYS

    # TODO: make this do something when open does something
    @verbose.verbose
    def rename ( self, oldPath, newPath ):
        return -errno.ENOSYS

    @verbose.verbose
    def rmdir ( self, path ):
        return -errno.ENOSYS

    @verbose.verbose
    def statfs(self):
        st = fuse.StatVfs()
        st.f_bsize = 1024
        st.f_frsize = 1024

        total_bytes = 0
        free_bytes = 0

        for plugin in self.plugins:
            space = plugin.getSpace()
            total_bytes += space[0]
            free_bytes += space[1]

        st.f_blocks = total_bytes / st.f_bsize
        st.f_bfree = free_bytes / st.f_bsize
        st.f_bavail = st.f_bfree

        return st

    @verbose.verbose
    def symlink ( self, targetPath, linkPath ):
        return -errno.ENOSYS

    @verbose.verbose
    def truncate ( self, path, size ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.truncateFile(path)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def unlink ( self, path ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.deleteFile(path)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def utime ( self, path, times ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.deleteFile(path)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def open ( self, path, flags ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.open(path, flags)
                return 0

        return -errno.ENOENT

    @verbose.verbose
    def read ( self, path, length, offset ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                data = plugin.read(path, length, offset)
                break

        return data

    @verbose.verbose
    def write ( self, path, buf, offset ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.write(path, buf, offset)
                break

        return len(buf)

    @verbose.verbose
    def release ( self, path, flags ):
        for plugin in self.plugins:
            if plugin.containsFile(path):
                plugin.release(path, flags)
                break

if __name__ == '__main__':
    import argparse, ConfigParser, sys
    logging.basicConfig(level=logging.INFO)

    # setup the argument parser
    script_name = sys.argv[0]
    parser = argparse.ArgumentParser(description='Create a Distributed Web File System (DWFS)')
    plugin_classes = find_subclasses('plugins/', FSPlugin)
    plugin_classes = list(set(plugin_classes)) # remove duplicates
    
    for plugin_class in plugin_classes:
        plugin_class.addArguments(parser)

    parser.add_argument('-f', '--foreground', action='store_true', help='Run FUSE in the foreground')
    parser.add_argument('mount_point', help='Path to mount the file system')
    
    args = parser.parse_args()

    sys.argv = [script_name, args.mount_point]

    if args.foreground:
        sys.argv.append('-f')

    # load all the plugins
    plugins = []
    for plugin_class in plugin_classes:
        p = plugin_class.createFromArgs(args)

        if p != None:
            plugins.extend(p)

    # load the config file
    config = ConfigParser.RawConfigParser()
    __location__ = os.path.realpath(os.path.join(os.getcwd(),
        os.path.dirname(__file__)))
    config_path = os.path.join(__location__, 'config.cfg')

    config.read(config_path)

    for plugin in plugins:
        config_params = plugin.getConfigParams()

        if not config_params:
            continue

        configuration = dict()
        section_exists = config.has_section(config_params[0])

        if not section_exists:
            config.add_section(config_params[0])

        for param in config_params[1]:
            if not section_exists:
                config.set(config_params[0], param, '')

            configuration[param] = config.get(config_params[0], param)

        plugin.updateConfig(configuration)

        for key in configuration:
            config.set(config_params[0], key, configuration[key])
    
    with open(config_path, 'wb') as config_file:
        config.write(config_file)

    fuse.fuse_python_api = (0, 2)
    fs = DWFS(plugins)
    fs.flags = 0
    fs.multithreaded = 0
    fs.parse(errex=1)
    fs.main()
