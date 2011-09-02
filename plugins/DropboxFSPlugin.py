import argparse
import os
from FSPlugin import FSPlugin

class DropboxFSPlugin(FSPlugin):
	@staticmethod
	def addArguments(parser):
		parser.add_argument('--dropbox', dest='dropbox_dirs', nargs='+', help='Use the given Dropbox folder')
	
	@staticmethod
	def createFromArgs(args):
		dirs = args.dropbox_dirs
		dropbox_plugins = []

		if dirs != None:
			for d in dirs:
				dropbox_plugins.append(DropboxFSPlugin(d))
		
		return dropbox_plugins

	def __init__(self, dropbox_dir):
		self.source_dir = dropbox_dir
	
	def getAllFiles(self):
		for f in os.listdir(self.source_dir):
			yield '/' + f
	
	def containsFile(self, path):
		return path.replace('/', '') in os.listdir(self.source_dir)

	# TODO: actually check
	def canStoreFile(self, f):
		return True
	
	def createNewFile(self, name, mode, dev):
		os.mknod(self.source_dir + '/' + name, mode, dev)
	
	def getAttributes(self, path):
		return os.stat(self.source_dir + path)
	
	def changeMode(self, path, mode):
		os.chmod(self.source_dir + path, mode)
	
	def changeOwn(self, path, uid, gid):
		os.chown(self.source_dir + path, uid, gid)
	
	def fsync(self, path):
		os.fsync(self.source_dir + path)
	
	def truncateFile(self, path, size):
		os.truncate(self.source_dir + path, size)
	
	def deleteFile(self, path):
		os.remove(self.source_dir + path)
	
	def setTimes(self, path, times):
		os.utime(self.source_dir + path, times)

	def getFileHandle(self, path, flags):
		return os.open(self.source_dir + path, flags)
	
	def closedFile(self, path):
		pass
