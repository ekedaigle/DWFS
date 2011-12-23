import argparse
import os
import stat
import getpass
import urllib
import urllib2
from FSPlugin import FSPlugin

OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
OAUTH_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
DOCS_SCOPE = 'https://docs.google.com/feeds/ https://spreadsheets.google.com/feeds/ https://docs.googleusercontent.com/'

class GoogleDocsFSPlugin(FSPlugin):
	@staticmethod
	def addArguments(parser):
		parser.add_argument('--googledocs',  action='store_true', help='Use the given Google Docs account')
	
	@staticmethod
	def createFromArgs(args):
		if args.googledocs:
			return [GoogleDocsFSPlugin(args.mount_point)]
		else:
			return None

	def __init__(self, top_dir):
		import ConfigParser
		parser = ConfigParser.RawConfigParser()
		parser.read('plugins/GoogleDocsFSPlugin.cfg')
		self.client_id = parser.get('API Keys', 'client_id')
		self.client_secret = parser.get('API Keys', 'client_secret')
		self.redirect_uri = parser.get('API Keys', 'redirect_uri')
		
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

		self.files = dict()
		self.top_dir = top_dir
		self.cache_dir = '/tmp/dwfs-' + getpass.getuser()
	
	def getToken(self, refresh):
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

					for node in title_tag.childNodes:
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
		os_stat = os.stat('.')
		attr = [0] * 10
		attr[stat.ST_MODE] = os_stat[stat.ST_MODE]
		attr[stat.ST_MODE] &= ~(stat.S_IFDIR | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
		attr[stat.ST_MODE] |= stat.S_IFREG
		attr[stat.ST_INO] =  os_stat[stat.ST_INO]
		attr[stat.ST_DEV] = os_stat[stat.ST_DEV]
		attr[stat.ST_NLINK] = 1
		attr[stat.ST_UID] = os_stat[stat.ST_UID]
		attr[stat.ST_GID] = os_stat[stat.ST_GID]
		attr[stat.ST_SIZE] = 32
		attr[stat.ST_ATIME] = 0
		attr[stat.ST_MTIME] = 0
		attr[stat.ST_CTIME] = 0

		return attr
	
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
		entry = self.files[path]
		content_tag = entry.getElementsByTagName('content')[0]
		file_url = content_tag.getAttribute('src')
		print 'url:', file_url
		url = urllib2.urlopen(file_url)
		temp_file = open(self.cache_dir + '/' + path, 'w')
		temp_file.write(url.read())
		temp_file.close()
		return os.open(temp_file, flags)
	
	def closedFile(self, path):
		pass
