import argparse
import os
from FSPlugin import FSPlugin

OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
OAUTH_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
DOCS_SCOPE = 'https://www.google.com/m8/feeds/'

class GoogleDocsFSPlugin(FSPlugin):
	@staticmethod
	def addArguments(parser):
		parser.add_argument('--googledocs',  action='store_true', help='Use the given Google Docs account')
	
	@staticmethod
	def createFromArgs(args):
		if args.googledocs:
			return [GoogleDocsFSPlugin()]
		else:
			return None

	def __init__(self):
		import ConfigParser
		parser = ConfigParser.RawConfigParser()
		parser.read('plugins/GoogleDocsFSPlugin.cfg')
		self.client_id = parser.get('API Keys', 'client_id')
		self.client_secret = parser.get('API Keys', 'client_secret')
		self.redirect_uri = parser.get('API Keys', 'redirect_uri')
		
		import urllib
		params = urllib.urlencode({
			'client_id' : self.client_id,
			'redirect_uri' : self.redirect_uri,
			'scope' : DOCS_SCOPE,
			'response_type' : 'code'
		})
		
		import webbrowser
		webbrowser.open_new('{0}?{1}'.format(OAUTH_AUTH_URL, params))
		self.refresh_token = raw_input('Enter access code: ')
		self.getToken(False)

		print self.access_token
		print self.refresh_token
	
	def getToken(self, refresh):
		import urllib, urllib2

		if refresh:
			params = urllib.urlencode({
				'client_id' : self.client_id,
				'client_secret' : self.client_secret,
				'refresh_token' : self.refresh_token,
				'grant_type' : 'refresh_token'
			})
		else:
			params = urllib.urlencode({
				'client_id' :  self.client_id,
				'client_secret' : self.client_secret,
				'code' : self.refresh_token,
				'redirect_uri' : self.redirect_uri,
				'grant_type' : 'authorization_code'
			})

		print OAUTH_TOKEN_URL
		print params
		f = urllib2.urlopen(OAUTH_TOKEN_URL, params)
		data = f.read()

		import json
		response = json.loads(data)
		self.access_token = response['access_token']
		self.refresh_token = response['refresh_token']

	
	def getAllFiles(self):
		pass
#		for f in os.listdir(self.source_dir):
#			yield '/' + f
	
	def containsFile(self, path):
		pass
#		return path.replace('/', '') in os.listdir(self.source_dir)

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
