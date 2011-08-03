import os

# This is the base class for all plugins
class FSPlugin:
	@staticmethod
	def addArguments(parser):
		pass

	def __init__(self, args):
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
