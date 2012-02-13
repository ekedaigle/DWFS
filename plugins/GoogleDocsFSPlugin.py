import argparse
import getpass
import errno
import logging
import os
import random
import stat
import string
import tempfile
from threading import Event, Thread
import urllib
import urllib2
from FSPlugin import FSPlugin

OAUTH_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
OAUTH_TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
DOCS_SCOPE = 'https://docs.google.com/feeds/%20https://spreadsheets.google.com/feeds/%20https://docs.googleusercontent.com/'
CACHE_DIR = '/tmp/dwfs/'

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
		
		params = urllib.urlencode({
			'client_id' : self.client_id,
			'redirect_uri' : self.redirect_uri,
			'response_type' : 'code'
		})
		
		import webbrowser
		webbrowser.open_new('{0}?{1}&scope={2}'.format(OAUTH_AUTH_URL, params, DOCS_SCOPE))
		self.refresh_token = raw_input('Enter access code: ')
		self.getToken(False)

		import time
		self.refresh_time = 0

		self.files = dict()
		self.open_files = dict()
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

		def get_inner_text(tag):
			for node in tag.childNodes:
				if node.nodeType == node.TEXT_NODE:
					return str(node.data.encode('ascii', 'ignore'))

		if time.time() - self.refresh_time > 10:
			self.refresh_time = time.time()
			url = 'https://docs.google.com/feeds/default/private/full?v=3'

			try:
				request = urllib2.Request(url)
				request.add_header('GData-Version', '3.0')
				request.add_header('Authorization', 'OAuth %s' % self.access_token)
				f = urllib2.urlopen(request)
				data = f.read()
			except urllib2.HTTPError, msg:
				logging.error(msg)
				data = None

			if data != None:
				import xml.dom.minidom as minidom
				dom = minidom.parseString(data)
				files = dict()

				for entry in dom.getElementsByTagName('entry'):
					new_file = dict()
					
					title_tag = entry.getElementsByTagName('title')[0]
					path = '/' + get_inner_text(title_tag)

					content_tag = entry.getElementsByTagName('content')[0]
					new_file['file_url'] = content_tag.getAttribute('src')

					size_tag = entry.getElementsByTagName('gd:quotaBytesUsed')[0]
					new_file['size'] = int(get_inner_text(size_tag))

					self.files[path] = new_file

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
		if self.containsFile(path):
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
			attr[stat.ST_SIZE] = self.files[path]['size']
			attr[stat.ST_ATIME] = 0
			attr[stat.ST_MTIME] = 0
			attr[stat.ST_CTIME] = 0

			return attr
		else:
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
		entry = self.files[path]
		file_url = entry['file_url'].replace('&amp;', '&')
		temp_file_name = 'dwfs_' + ''.join(random.choice(string.digits) for x in range(10))
		temp_file_path = CACHE_DIR + temp_file_name

		try:
			logging.info('*** *** Downloading file: %s' % file_url)
			request = urllib2.Request(file_url)
			request.add_header('GData-Version', '3.0')
			request.add_header('Authorization', 'OAuth %s' % self.access_token)
			url = urllib2.urlopen(request)
			logging.info('*** *** Got code: %i' % url.getcode())

			if not os.path.exists(CACHE_DIR):
				os.mkdir(CACHE_DIR)

			temp_file = open(temp_file_path, 'wb')
			temp_file.write(url.read())
			temp_file.close()
		except urllib2.HTTPError, msg:
			logging.error(msg)
			raise

		return os.open(CACHE_DIR + temp_file_name, flags)
	
	def download_file(self, url, open_file):
		file_url = url.replace('&amp;', '&')

		try:
			logging.info('*** *** Downloading file: %s' % file_url)
			request = urllib2.Request(file_url)
			request.add_header('GData-Version', '3.0')
			request.add_header('Authorization', 'OAuth %s' % self.access_token)
			url = urllib2.urlopen(request)
			logging.info('*** *** Got code: %i' % url.getcode())
			
			open_file[0].write(url.read())
			open_file[1].set()

		except urllib2.HTTPError, msg:
			logging.error(msg)
			raise

	def open(self, path, flags):
		logging.info('*** *** Opening file')

		if not os.path.exists(CACHE_DIR):
			os.mkdir(CACHE_DIR)

		temp_file_name = 'dwfs_' + ''.join(random.choice(string.digits) for x in range(10))
		temp_file_path = CACHE_DIR + temp_file_name

		if path in self.open_files:
			logging.info('*** *** File already open')
			return

		self.open_files[path] = (open(temp_file_path, 'w+b'), Event())

		entry = self.files[path]
		file_url = entry['file_url'].replace('&amp;', '&')
		Thread(target = self.download_file, args = (file_url, self.open_files[path])).start()
		logging.info('*** *** Starting download')

	def read(self, path, length, offset):
		open_file = self.open_files[path]
		open_file[1].wait() # wait until the file is finished downloading

		open_file[0].seek(offset)
		return open_file[0].read(length)
	
	def write(self, path, buf, offset):
		pass
	
	def release(self, path, flags):
		open_file = self.open_files[path]
		open_file[1].wait() # wait until the file is finished downloading
		open_file[0].close()
		del self.open_files[path]
