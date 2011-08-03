#!/usr/bin/env python
import fuse
import time

from stat import *
import os	  # for filesystem modes (O_RDONLY, etc)
import errno   # for error number codes (ENOENT, etc)
			   # - note: these must be returned as negatives

from DropboxFSPlugin import DropboxFSPlugin

PLUGIN_DIR='/home/ekern/WebFS/test_data'

def getDepth(path):
	"""
	Return the depth of a given path, zero-based from root ('/')
	"""
	if path == '/':
		return 0
	else:
		return path.count('/')

class NullFS(fuse.Fuse):
	"""
	"""

	def __init__(self, *args, **kw):
		fuse.Fuse.__init__(self, *args, **kw)
		self.plugins = [DropboxFSPlugin(PLUGIN_DIR + '/dir1'),
						DropboxFSPlugin(PLUGIN_DIR + '/dir2'),
						DropboxFSPlugin(PLUGIN_DIR + '/dir3'),
						DropboxFSPlugin(PLUGIN_DIR + '/dir4'),
						DropboxFSPlugin(PLUGIN_DIR + '/dir5')]
		self.open_files = dict()

		print 'Init complete.'

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

		print '*** getattr ', path
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

		print '*** getdir', path
		return -errno.ENOSYS

	def mythread ( self ):
		print '*** mythread'
		return -errno.ENOSYS

	def chmod ( self, path, mode ):
		print '*** chmod', path, oct(mode)
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.changeMode(path, mode)
				return 0

		return -errno.ENOENT

	def chown ( self, path, uid, gid ):
		print '*** chown', path, uid, gid

		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.changeOwn(path, uid, gid)
				return 0

		return -errno.ENOENT

	def fsync ( self, path, isFsyncFile ):
		print '*** fsync', path, isFsyncFile
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.fsync(path)
				return 0

		return -errno.ENOENT

	def link ( self, targetPath, linkPath ):
		print '*** link', targetPath, linkPath
		return -errno.ENOSYS

	def mkdir ( self, path, mode ):
		print '*** mkdir', path, oct(mode)
		return -errno.ENOSYS

	def mknod ( self, path, mode, dev ):
		print '*** mknod', path, oct(mode), dev
		
		if getDepth(path) != 1:
			return -errno.ENOSYS

		for plugin in self.plugins:
			if plugin.canStoreFile(path):
				plugin.createNewFile(path.replace('/', ''), mode, dev)
				break
		
		return 0

	def readlink ( self, path ):
		print '*** readlink', path
		return -errno.ENOSYS

	# TODO: make this do something when open does something
	def rename ( self, oldPath, newPath ):
		print '*** rename', oldPath, newPath
		return -errno.ENOSYS

	def rmdir ( self, path ):
		print '*** rmdir', path
		return -errno.ENOSYS

	def statfs ( self ):
		print '*** statfs'
		return -errno.ENOSYS

	def symlink ( self, targetPath, linkPath ):
		print '*** symlink', targetPath, linkPath
		return -errno.ENOSYS

	def truncate ( self, path, size ):
		print '*** truncate', path, size
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.truncateFile(path)
				return 0

		return -errno.ENOENT

	def unlink ( self, path ):
		print '*** unlink', path
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.deleteFile(path)
				return 0

		return -errno.ENOENT

	def utime ( self, path, times ):
		print '*** utime', path, times
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				plugin.deleteFile(path)
				return 0

		return -errno.ENOENT

	def open ( self, path, flags ):
		print '*** open', path, flags
		
		for plugin in self.plugins:
			if plugin.containsFile(path):
				try:
					fh = plugin.getFileHandle(path, flags)
				except IOError:
					return -errno.errno
				
				self.open_files[path] = fh
				return 0

		return -errno.ENOENT

	def read ( self, path, length, offset ):
		print '*** read', path, length, offset
		
		if path in self.open_files:
			fh = self.open_files[path]
		else:
			return -errno.ENOENT

		os.read(fh, offset)
		return os.read(fh, length)

	def write ( self, path, buf, offset ):
		print '*** write', path, buf, offset

		if path in self.open_files:
			fh = self.open_files[path]
		else:
			return -errno.ENOENT

		os.read(fh, offset)
		os.write(fh, buf)
		return len(buf)

	def release ( self, path, flags ):
		print '*** release', path, flags

		if path in self.open_files:
			del self.open_files[path]
			return 0
		else:
			return -errno.ENOENT

if __name__ == '__main__':
	fuse.fuse_python_api = (0, 2)
	fs = NullFS()
	fs.flags = 0
	fs.multithreaded = 0
	fs.parse(errex=1)
	fs.main()
