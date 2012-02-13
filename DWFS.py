#!/usr/bin/env python
import fuse

import logging
from stat import *
import os	  # for filesystem modes (O_RDONLY, etc)
import errno   # for error number codes (ENOENT, etc)
			   # - note: these must be returned as negatives

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

		logging.info('Init complete.')
	
	def fsinit(self):
		os.chdir(self.cwd)

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

		logging.info('*** getattr %s' % path)
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

	def readdir(self, path, offset):
		yield fuse.Direntry('.')
		yield fuse.Direntry('..')

		if path == '/':
			for plugin in self.plugins:
				for f in plugin.getAllFiles():
					yield fuse.Direntry(f.split('/')[-1])

	def getdir(self, path):
		"""
		return: [[('file1', 0), ('file2', 0), ... ]]
		"""

		logging.info('*** getdir %s' % path)
		return -errno.ENOSYS

	def mythread ( self ):
		logging.info('*** mythread')
		return -errno.ENOSYS

	def chmod ( self, path, mode ):
		logging.info('*** chmod', path, oct(mode))
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.changeMode(path, mode)
				return 0

		return -errno.ENOENT

	def chown ( self, path, uid, gid ):
		logging.info('*** chown', path, uid, gid)

		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.changeOwn(path, uid, gid)
				return 0

		return -errno.ENOENT

	def fsync ( self, path, isFsyncFile ):
		logging.info('*** fsync', path, isFsyncFile)
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.fsync(path)
				return 0

		return -errno.ENOENT

	def link ( self, targetPath, linkPath ):
		logging.info('*** link', targetPath, linkPath)
		return -errno.ENOSYS

	def mkdir ( self, path, mode ):
		logging.info('*** mkdir', path, oct(mode))
		return -errno.ENOSYS

	def mknod ( self, path, mode, dev ):
		logging.info('*** mknod', path, oct(mode), dev)
		
		if getDepth(path) != 1:
			return -errno.ENOSYS

		for plugin in self.plugins:
			if plugin.canStoreFile(path):
				plugin.createNewFile(path.replace('/', ''), mode, dev)
				break
		
		return 0

	def readlink ( self, path ):
		logging.info('*** readlink', path)
		return -errno.ENOSYS

	# TODO: make this do something when open does something
	def rename ( self, oldPath, newPath ):
		logging.info('*** rename', oldPath, newPath)
		return -errno.ENOSYS

	def rmdir ( self, path ):
		logging.info('*** rmdir', path)
		return -errno.ENOSYS

	def statfs ( self ):
		logging.info('*** statfs')
		return -errno.ENOSYS

	def symlink ( self, targetPath, linkPath ):
		logging.info('*** symlink', targetPath, linkPath)
		return -errno.ENOSYS

	def truncate ( self, path, size ):
		logging.info('*** truncate', path, size)
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.truncateFile(path)
				return 0

		return -errno.ENOENT

	def unlink ( self, path ):
		logging.info('*** unlink', path)
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.deleteFile(path)
				return 0

		return -errno.ENOENT

	def utime ( self, path, times ):
		logging.info('*** utime', path, times)
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.deleteFile(path)
				return 0

		return -errno.ENOENT

	def open ( self, path, flags ):
		logging.info('*** open %s %s' % (path, flags))
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.open(path, flags)
				return 0

		return -errno.ENOENT

	def read ( self, path, length, offset ):
		logging.info('*** read %s %i %i' % (path, length, offset))
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				data = plugin.read(path, length, offset)
				break

		logging.info('*** *** read %i bytes' % (len(data)))
		return data

	def write ( self, path, buf, offset ):
		logging.info('*** write %s %s %i' % (path, buf, offset))

		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.write(path, buf, offset)
				break

		return len(buf)

	def release ( self, path, flags ):
		logging.info('*** release %s %s' % (path, flags))

		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.release(path, flags)
				break

if __name__ == '__main__':
	import argparse, sys
	logging.basicConfig(level=logging.INFO)

	script_name = sys.argv[0]
	parser = argparse.ArgumentParser(description='Create a Distributed Web File System (DWFS)')
	plugin_classes = find_subclasses('plugins/', FSPlugin)
	
	for plugin_class in plugin_classes:
		plugin_class.addArguments(parser)

	parser.add_argument('-f', '--foreground', action='store_true', help='Run FUSE in the foreground')
	parser.add_argument('mount_point', help='Path to mount the file system')
	
	args = parser.parse_args()

	sys.argv = [script_name, args.mount_point]

	if args.foreground:
		sys.argv.append('-f')

	plugins = []
	for plugin_class in plugin_classes:
		p = plugin_class.createFromArgs(args)

		if p != None:
			plugins.extend(p)

	fuse.fuse_python_api = (0, 2)
	fs = DWFS(plugins)
	fs.flags = 0
	fs.multithreaded = 0
	fs.parse(errex=1)
	fs.main()
