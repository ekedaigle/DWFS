import logging
import webbrowser
from FolderFSPlugin import FolderFSPlugin
from dropbox import client, session

class DropboxFolderFSPlugin(FolderFSPlugin):
    arg_name = 'dropbox'
    config_section = 'Dropbox'
    config_keys = ['app_key', 'app_secret', 'access_type', 'access_token']

    def __init__(self, folder_dir):
        super(DropboxFolderFSPlugin, self).__init__(folder_dir)
        self.free_space = 0
        self.total_space = 0

    def updateConfig(self, config):
        self.app_key = config['app_key']
        self.app_secret = config['app_secret']
        self.access_type = config['access_type']
        
        if self.app_key == '' or self.app_secret == '' or self.access_type == '':
            logging.error('Dropbox not configured properly')
            return

        sess = session.DropboxSession(self.app_key, self.app_secret, self.access_type)

        if config['access_token'] == '':
            request_token = sess.obtain_request_token()
            url = sess.build_authorize_url(request_token)
            webbrowser.open(url)
            raw_input('Press Enter when auth is complete')
            config['access_token'] = sess.obtain_access_token(request_token)
        else:
            token_parts = [x.split('=') for x in config['access_token'].split('&')]
            
            if token_parts[0][0] == 'oauth_token_secret':
                sess.set_token(token_parts[1][1], token_parts[0][1])
            elif token_parts[0][0] == 'oauth_token':
                sess.set_token(token_parts[0][1], token_parts[1][1])
            else:
                logging.error('Bad Dropbox token')
        
        self.dropbox_client = client.DropboxClient(sess)
        self.updateSpace()
            
    def updateSpace(self):
        quota_info = self.dropbox_client.account_info()['quota_info']
        self.free_space = quota_info['quota'] - quota_info['normal']
        self.total_space = quota_info['quota']

    def getSpace(self):
        return (self.total_space, self.free_space)
