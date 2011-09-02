import argparse
import os
from FSPlugin import FSPlugin

OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
OAUTH_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
DOCS_SCOPE = 'https://docs.google.com/feeds/'

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

		import time
		self.refresh_time = 0
	
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

		f = urllib2.urlopen(OAUTH_TOKEN_URL, params)
		data = f.read()

		import json
		response = json.loads(data)
		self.access_token = response['access_token']
		self.refresh_token = response['refresh_token']
	
	def refreshFiles(self):
		import time

		if time.time() - self.refresh_time > 10:
			self.refresh_time = time.time()
			url = 'https://docs.google.com/feeds/default/private/full?v=3&access_token=' + self.access_token

			try:
				f = urllib2.urlopen(url)
				data = f.read()
			except urllib2.HTTPError, msg:
				print msg
				data = None

			if data != None:
				import xml.dom.minidom as minidom
				dom = minidom.parseString(data)
				files = dict()

				for entry in dom.getElementsByTagName('entry'):
					title_tag = entry.getElementsByTagName('title')[0]

					for node in title.childNodes:
						if node.nodeType == node.TEXT_NODE:
							path = '/' + str(node.data.encode('ascii', 'ignore'))

					self.files[path] = entry

	def getAllFiles(self):
		self.refreshFiles()

		for path in self.files:
			yield path
	
	def containsFile(self, path):
		return path in self.files

	# TODO: actually check
	def canStoreFile(self, f):
		return True
	
	def createNewFile(self, name, mode, dev):
		pass
#		os.mknod(self.source_dir + '/' + name, mode, dev)
	
	def getAttributes(self, path):
		return os.stat(self.source_dir + path)
	
	def changeMode(self, path, mode):
		pass
	
	def changeOwn(self, path, uid, gid):
		pass
	
	def fsync(self, path):
		os.fsync(self.source_dir + path)
	
	def truncateFile(self, path, size):
		os.truncate(self.source_dir + path, size)
	
	def deleteFile(self, path):
		os.remove(self.source_dir + path)
	
	def setTimes(self, path, times):
		pass

	def getFileHandle(self, path, flags):
		return os.open(self.source_dir + path, flags)
	
	def closedFile(self, path):
		pass
