from credmon.CredentialMonitors.AbstractCredentialMonitor import AbstractCredentialMonitor
from credmon.utils import atomic_rename
from requests_oauthlib import OAuth2Session
import os
import time
import json
import glob
import tempfile

class OAuthCredmon(AbstractCredentialMonitor):

    def should_renew(self, username, token_name):

        access_token_path = os.path.join(self.cred_dir, username, token_name + '.use')
        metadata_path = os.path.join(self.cred_dir, username, token_name + '.meta')

        # check if access token exists
        if not os.path.exists(access_token_path):
            return True

        try:
            with open(access_token_path, 'r') as f:
                access_token = json.load(f)
        except IOError:
            self.log.warning("Could not open access token %s", access_token_path)
            return True
        except ValueError:
            self.log.warning("The format of the access token file %s is invalid", access_token_path)
            return True

        # load metadata to check if access token uses a refresh token
        try:
            with open(metadata_path, 'r') as f:
                token_metadata = json.load(f)
        except IOError:
            self.log.warning("Could not find metadata file %s", metadata_path)
        except ValueError:
            self.log.warning("The format of the metadata file %s is invalid", metadata_path)
        else:
            if 'use_refresh_token' in token_metadata:
                if token_metadata['has_refresh_token'] == False:
                    return False

        # get token half-life
        create_time = os.path.getctime(access_file)
        refresh_time = start_time + float(token['expires_in'])/2

        # check if token is past its half-life
        if time.time() > refresh_time:
            return True
            
        return False

    def refresh_access_token(self, username, token_name):

        # load the refresh token
        refresh_token_path = os.path.join(self.cred_dir, username, token_name + '.top')
        try:
            with open(refresh_token_path, 'r') as f:
                refresh_token = json.load(f)
        except IOError:
            self.log.error("Could not open refresh token %s", refresh_token_path)
            return False
        except ValueError:
            self.log.error("The format of the refresh token file %s is invalid", refresh_token_path)
            return False

        # load metadata
        metadata_path = os.path.join(self.cred_dir, username, token_name + '.meta')
        try:
            with open(metadata_path, 'r') as f:
                token_metadata = json.load(f)
        except IOError:
            self.log.error("Could not open metadata file %s", metadata_path)
            return False
        except ValueError:
            self.log.error("The format of the metadata file %s is invalid", metadata_path)
            return False

        # refresh the token (provides both new refresh and access tokens)
        oauth_client = OAuth2Session(token_metadata['client_id'], token = refresh_token)
        new_token = oauth_client.refresh_token(token_metadata['token_url'],
                                                   client_id = token_metadata['client_id'],
                                                   client_secret = token_metadata['client_secret'])
        try:
            refresh_token = {u'refresh_token': new_token.pop('refresh_token')}
        except KeyError:
            self.log.error("No %s refresh token returned for %s", token_name, username)
            return False

        # write tokens to tmp files
        (tmp_fd, tmp_refresh_token_path) = tempfile.mkstemp(dir = self.cred_dir)
        with os.fdopen(tmp_fd, 'w') as f:
            json.dump(refresh_token, f)
        (tmp_fd, tmp_access_token_path) = tempfile.mkstemp(dir = self.cred_dir)
        with os.fdopen(tmp_fd, 'w') as f:
            json.dump(new_token, f)

        # atomically move new tokens in place
        access_token_path = os.path.join(self.cred_dir, username, token_name + '.use')
        try:
            atomic_rename(tmp_access_token_path, access_token_path)
            atomic_rename(tmp_refresh_token_path, refresh_token_path)
        except OSError as e:
            self.log.error(e)
            return False
        else:
            return True

    def check_access_token(self, access_token_path):

        (basename, token_filename) = os.path.split(access_token_path)
        (cred_dir, username) = os.path.split(basename)
        token_name = os.path.splitext(token_filename)[0] # strip .use

        if self.should_renew(username, token_name):
            self.log.info('Refreshing %s tokens for user %s', token_name, username)
            success = self.refresh_access_token(username, token_name)
            if success:
                self.log.info('Successfully refreshed %s tokens for user %s', token_name, username)
            else:
                self.log.error('Failed to refresh %s tokens for user %s', token_name, username)

    def scan_tokens(self):

        # loop over all access tokens in the cred_dir
        access_token_files = glob.glob(os.path.join(self.cred_dir, '*', '*.use'))
        for access_token_file in access_token_files:
            self.check_access_token(access_token_file)


