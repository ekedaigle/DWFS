import argparse
import os
from FSPlugin import FSPlugin

class GoogleDocsFSPlugin(FSPlugin):
	@staticmethod
	def addArguments(parser):
		parser.add_argument('--googledocs',  action='store_true', help='Use the given Google Docs account')
	
	@staticmethod
	def createFromArgs(args):
		if args.googledocs:
			return GoogleDocsFSPlugin(account[0], account[1])
		else:
			return None

	def __init__(self):
		pass
	
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
