import sys
from flask import Flask, request, redirect, render_template, session
from requests_oauthlib import OAuth2Session
import os
import tempfile
from credmon.utils import atomic_rename, get_cred_dir
import classad
import json
import re
import logging

logger = logging.getLogger('OAuthCredmonWebserver')

class LoggerWriter:
    '''Used to override sys.stdout and sys.stderr so that
    all messages are sent to the logger'''
    
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message != '\n':
            self.level(message.rstrip())

    def flush(self):
        return

# send stdout and stderr to the log
sys.stdout = LoggerWriter(logger.debug)
sys.stderr = LoggerWriter(logger.warning)

# initialize Flask
app = Flask(__name__)

# make sure the secret_key is randomized in case user fails to override before calling app.run()
app.secret_key = os.urandom(24)

def get_provider_str(provider):
    return '_'.join(provider).rstrip('_')

def get_provider_ad(provider, key_path):
    '''
    Returns the ClassAd for a given OAuth provider given 
    the provider name and path to file with ClassAds.
    '''
    
    if not os.path.exists(key_path):
        raise Exception("Key file {0} doesn't exist".format(key_path))

    with open(key_path, 'r') as key_file:
        for provider_ad in classad.parseAds(key_file):
            if (provider_ad['Provider'], provider_ad.get('Handle', '')) == provider:
                break
        else:
            raise Exception("Provider {0} not in key file {1}".format(provider, key_path))

    return provider_ad


@app.before_request
def before_request():
    '''
    Prepends request URL with https if insecure http is used.
    '''
    return
    # todo: figure out why this loops
    #if not request.is_secure:
    #if request.url.startswith("http://"):
    #    print(request.url)
    #    url = request.url.replace('http://', 'https://', 1)
    #    print(url)
    #    code = 301
    #    return redirect(url, code=code)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/key/<key>')
def key(key):
    # get the key from URL
    if not re.match("[0-9a-fA-F]+", key):
        raise Exception("Key id {0} is not a valid key".format(key))

    # check for the key file in the credmon directory
    cred_dir = get_cred_dir()
    key_path = os.path.join(cred_dir, key)
    if not os.path.exists(key_path):
        raise Exception("Key file {0} doesn't exist".format(key_path))
    
    # read in the key file, which is a list of classads
    session['providers'] = {}
    session['logged_in'] = False
    print('Creating new session from {0}'.format(key_path))
    with open(key_path, 'r') as key_file:
        
        # store the path to the key file since it will be accessed later in the session
        session['key_path'] = key_path
        
        # initialize data for each token provider
        for provider_ad in classad.parseAds(key_file):
            provider = (provider_ad['Provider'], provider_ad.get('Handle', ''))
            session['providers'][provider] = {}
            session['providers'][provider]['logged_in'] = False
            if 'Scopes' in provider_ad:
                session['providers'][provider]['requested_scopes'] = [s.rstrip().lstrip() for s in provider_ad['Scopes'].split(',')]
            if 'Audience' in provider_ad:
                session['providers'][provider]['requested_resource'] = provider_ad['Audience']

        # the local username is global to the session, just grab it from the last classad
        session['local_username'] = provider_ad['LocalUser']

    return render_template('index.html')

@app.route('/login/<provider>')
def oauth_login(provider):
    """
    Go to OAuth provider
    """

    if not (provider in session['providers']):
        raise Exception("Provider {0} not in list of providers".format(provider))
    provider_ad = get_provider_ad(provider, session['key_path'])

    # gather information from the key file classad
    oauth_kwargs = {}
    oauth_kwargs['client_id'] = provider_ad['ClientId']
    oauth_kwargs['redirect_uri'] = provider_ad['ReturnUrl']
    if 'Scopes' in provider_ad: # pass scope to the OAuth2Session object if requested
        scope = [s.rstrip().lstrip() for s in provider_ad['Scopes'].split(',')]
        oauth_kwargs['scope'] = scope

    auth_url_kwargs = {}
    auth_url_kwargs['url'] = provider_ad['AuthorizationUrl']

    # ***
    # ***                WARNING
    # *** Adding 'resource' to the authorization_url
    # *** is specific to scitokens OAuth server requests!
    # ***
    if 'Audience' in provider_ad:
        auth_url_kwargs['resource'] = provider_ad['Audience']

    # make the auth request and get the authorization url
    oauth = OAuth2Session(**oauth_kwargs)
    authorization_url, state = oauth.authorization_url(**auth_url_kwargs)

    # state is used to prevent CSRF, keep this for later.
    # todo: cleanup this way of changing the session variable
    providers_dict = session['providers']
    providers_dict[provider]['state'] = state
    session['providers'] = providers_dict

    # store the provider name since it could be different than the provider
    # argument to oauth_return() (e.g. if getting multiple tokens from the
    # same OAuth endpoint)
    session['outgoing_provider'] = provider
    
    return redirect(authorization_url)

@app.route('/return/<provider>')
def oauth_return(provider):
    """
    Returning from OAuth provider
    """

    # get the provider name from the outgoing_provider set in oauth_login()
    provider = session.pop('outgoing_provider', (provider, ''))
    if not (provider in session['providers']):
        raise Exception("Provider {0} not in list of providers".format(provider))

    provider_ad = get_provider_ad(provider, session['key_path'])

    # gather information from the key file classad
    client_id = provider_ad['ClientId']
    redirect_uri = provider_ad['ReturnUrl']
    print('session = {0}'.format(session))
    state = session['providers'][provider]['state']
    oauth = OAuth2Session(client_id, state=state, redirect_uri=redirect_uri)
    
    # convert http url to https if needed
    if request.url.startswith("http://"):
        updated_url = request.url.replace('http://', 'https://', 1)
    else:
        updated_url = request.url

    # fetch token
    client_secret = provider_ad['ClientSecret']
    token_url = provider_ad['TokenUrl']
    token = oauth.fetch_token(token_url,
        authorization_response=updated_url,
        client_secret=client_secret,
        method='POST')
    print('Got {0} token for user {1}'.format(provider, session['local_username']))
    
    # get user info if available
    # todo: make this more generic
    try:
        get_user_info = oauth.get(provider_ad['UserUrl'])
        user_info = get_user_info.json()
        if 'login' in user_info: # box
            session['providers'][provider]['username'] = user_info['login']
        elif 'sub' in user_info: # scitokens/jwt
            session['providers'][provider]['username'] = user_info['sub']
        else:
            session['providers'][provider]['username'] = 'Unknown'
    except ValueError:
        session['providers'][provider]['username'] = 'Unknown'

    # split off the refresh token from the access token if it exists
    try:
        refresh_token_string = token.pop('refresh_token')
    except KeyError: # no refresh token
        use_refresh_token = False
        refresh_token_string = ''
    else:
        use_refresh_token = True

    refresh_token = {
        'refresh_token': refresh_token_string
        }

    # create a metadata file for refreshing the token
    metadata = {
        'client_id': client_id,
        'client_secret': client_secret,
        'token_url': token_url,
        'use_refresh_token': use_refresh_token
        }

    # atomically write the tokens to the cred dir
    cred_dir = get_cred_dir()
    user_cred_dir = os.path.join(cred_dir, session['local_username'])
    if not os.path.isdir(user_cred_dir):
        os.makedirs(user_cred_dir)
    refresh_token_path = os.path.join(user_cred_dir, get_provider_str(provider) + '.top')
    access_token_path = os.path.join(user_cred_dir, get_provider_str(provider) + '.use')
    metadata_path = os.path.join(user_cred_dir, get_provider_str(provider) + '.meta')

    # write tokens to tmp files          
    (tmp_fd, tmp_access_token_path) = tempfile.mkstemp(dir = user_cred_dir)
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(token, f)

    (tmp_fd, tmp_refresh_token_path) = tempfile.mkstemp(dir = user_cred_dir)
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(refresh_token, f)
        
    (tmp_fd, tmp_metadata_path) = tempfile.mkstemp(dir = user_cred_dir)
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(metadata, f)
        
    # (over)write token files
    try:
        atomic_rename(tmp_access_token_path, access_token_path)
        atomic_rename(tmp_refresh_token_path, refresh_token_path)
        atomic_rename(tmp_metadata_path, metadata_path)
    except OSError as e:
        sys.stderr.write(e)

    # mark provider as logged in
    session['providers'][provider]['logged_in'] = True

    # check if other providers are logged in
    session['logged_in'] = True
    for provider in session['providers']:
        if session['providers'][provider]['logged_in'] == False:
            session['logged_in'] = False
    
    return redirect("/")

