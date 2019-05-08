import os
import sys
import socket
import shutil
import errno
import htcondor
from credmon.utils import get_cred_dir

credmon_config_template = '''
#####################################################################################
# MANDATORY: To setup the credmon, you must uncomment these lines:
#
DAEMON_LIST = $(DAEMON_LIST), CREDD, SEC_CREDENTIAL_MONITOR

# MANDATORY for OAuth credmon: Uncomment this lines to have the CredD
# use the OAuth2 mode of managing credentials
#
CREDD_OAUTH_MODE = True

# MANDATORY for local credmon: Uncomment this line to have submitters
# always create a credential
#
# SEC_CREDENTIAL_PRODUCER = /usr/bin/scitokens_credential_producer

# MANDATORY for enabling the transfer of credentials from submit host
# to execute hosts, if encryption is not already enabled.
# SEC_DEFAULT_ENCRYPTION = REQUIRED

#####################################################################################
#
# OPTIONAL: These are customized in many use cases.
#
#

# The issuer location; relying parties will need to be able to access this issuer to
# download the corresponding public key.
# LOCAL_CREDMON_ISSUER = https://$(FULL_HOSTNAME)

# The authorizations given to the token.  Should be of the form `authz:path` and
# space-separated for multiple authorizations.  The token `{{username}}` will be
# expanded with the user's Unix username.
# LOCAL_CREDMON_AUTHZ_TEMPLATE = read:/user/{{username}} write:/user/{{username}}


#####################################################################################
#
#
# OPTIONAL: These are rarely customized
#
#

# Path to the private keyfile
# LOCAL_CREDMON_PRIVATE_KEY = /etc/condor/scitokens-private.pem

# The lifetime, in seconds, for a new token.  The credmon will continuously renew
# credentials on the submit-side.
# LOCAL_CREDMON_TOKEN_LIFETIME = 1200

# Each key must have a name that relying parties can look up; defaults to "local"
# LOCAL_CREDMON_KEY_ID = local

# Common directories and definition of the various credmon-related daemons
SEC_CREDENTIAL_DIRECTORY = {0}
TRUST_CREDENTIAL_DIRECTORY = True
SEC_CREDENTIAL_MONITOR = /usr/bin/scitokens_credmon
SEC_CREDENTIAL_MONITOR_LOG = $(LOG)/CredMonLog
'''

tokens_config_example = '''
## Example for Box.com:
# BOX_CLIENT_ID = changeme
# BOX_CLIENT_SECRET_FILE = /etc/condor/.secrets/box
# BOX_RETURN_URL_SUFFIX = /return/box
# BOX_AUTHORIZATION_URL = https://account.box.com/api/oauth2/authorize
# BOX_TOKEN_URL = https://api.box.com/oauth2/token
# BOX_USER_URL = https://api.box.com/2.0/users/me
'''

apache_config_template = '''
# Set SSL ciphers if not already part of your SSL config!  Here's a reasonable recommendation.
# Instead of blindly accepting this, go to https://mozilla.github.io/server-side-tls/ssl-config-generator/?server=apache-2.4.0&openssl=1.0.1e&hsts=yes&profile=modern
# and create your own.
#SSLProtocol             all -SSLv3 -TLSv1 -TLSv1.1
#SSLCipherSuite          ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256
#SSLHonorCipherOrder     on

# A modest number of processes and threads; production applications may want to increase this.
WSGIDaemonProcess     ScitokensCredmon user=condor group=condor processes=2 threads=25 display-name=ScitokensCredmon
WSGIProcessGroup      ScitokensCredmon

# Place the app under {0}
WSGIScriptAlias       {0} {1}

# Recommendation from upstream mod_wsgi developers.
LogLevel info

# Required for wsgi-scripts directory to allow executing WSGI.
<Directory {2}>
  Require all granted
</Directory>
'''

wsgi_code = '''
#
# Configure Logging
#

from credmon.utils import setup_logging
import os
import logging

import htcondor

logger = setup_logging(log_path = htcondor.param.get("SEC_CREDENTIAL_MONITOR_LOG", "/var/log/condor/CredMonLog"),
                       log_level = logging.INFO)

#
# Load the session key
#
from credmon.utils import generate_secret_key
mykey = generate_secret_key()

#
# Start Service
#
from credmon.CredentialMonitors.OAuthCredmonWebserver import app
app.secret_key = mykey

application = app
'''

def install_to_condor(
        condor_credmon_config_path = os.path.join(htcondor.param['LOCAL_CONFIG_DIR'], '50-scitokens-credmon.conf'),
        condor_tokens_config_path = os.path.join(htcondor.param['LOCAL_CONFIG_DIR'], '60-oauth-token-providers.conf'),
        credential_directory = os.path.join('/', 'var', 'lib', 'condor', 'credentials'),
        credmon_web_port = 443,
        credmon_web_directory = '/',
        ):

    if not os.path.exists(os.path.dirname(condor_credmon_config_path)):
        raise OSError(errno.ENOENT, 'Cannot find HTCondor config directory', os.path.dirname(condor_credmon_config_path))

    if not os.path.exists(os.path.dirname(condor_tokens_config_path)):
        raise OSError(errno.ENOENT, 'Cannot find HTCondor config directory', os.path.dirname(condor_tokens_config_path))

    if not os.path.exists(credential_directory):
        sys.stderr.write('Warning: credential directory {0} does not exist, will attempt to create it\n'.format(credential_directory))

    if os.path.exists(condor_credmon_config_path):
        (basedir, basename) = os.path.split(condor_credmon_config_path)
        if basedir == htcondor.param['LOCAL_CONFIG_DIR']:
            try:
                os.makedirs(os.path.join(basedir, 'bak'))
            except OSError as oserror:
                if oserror.errno != errno.EEXIST:
                    raise oserror
            condor_credmon_config_backup = os.path.join(basedir, 'bak', basename + '.bak')
        else:
            condor_credmon_config_backup = condor_credmon_config_path + '.bak'

        shutil.copy2(condor_credmon_config_path, condor_credmon_config_backup)
        sys.stdout.write('Copied existing {0} to {1}\n'.format(condor_credmon_config_path, condor_credmon_config_backup))

    credmon_config = credmon_config_template.format(credential_directory)
    if (credmon_web_port != 443) or (credmon_web_directory != '/'):
        credmon_web_prefix = 'https://' + socket.getfqdn()
        if credmon_web_port != 443:
            credmon_web_prefix += ':' + str(credmon_web_port)
        if credmon_web_directory.lstrip('/') != '':
            credmon_web_prefix += '/' + credmon_web_directory.lstrip('/').rstrip('/')
        credmon_config += 'CREDMON_WEB_PREFIX = {0}\n'.format(credmon_web_prefix)

    with open(condor_credmon_config_path, 'w') as f:
        f.write(credmon_config)
    sys.stdout.write('Wrote credmon configuration to {0}\n'.format(condor_credmon_config_path))

    if os.path.exists(condor_tokens_config_path):
        sys.stdout.write('Existing token config {0} will not be overwritten\n'.format(condor_tokens_config_path))
    else:
        with open(condor_tokens_config_path, 'w') as f:
            f.write(tokens_config_example)
        sys.stdout.write('Wrote example tokens config to {0}\n'.format(condor_tokens_config_path))

    # to see what's set now, reload the config after adding to it
    htcondor.reload_config()

    # get_cred_dir will create the credential directory if it doesn't already exist
    get_cred_dir()

    if ('SEC_DEFAULT_ENCRYPTION' not in htcondor.param):
        sys.stderr.write(
            'Warning: SEC_DEFAULT_ENCRYPTION not defined in current HTCondor configuration.\n' +
            'Encryption must be enabled for token transfer to job sandboxes!\n')
    elif htcondor.param['SEC_DEFAULT_ENCRYPTION'].upper() == 'NEVER':
        sys.stderr.write(
            'Warning: SEC_DEFAULT_ENCRYPTION = {0} in current HTCondor configuration.\n'.format(htcondor.param['SEC_DEFAULT_ENCRYPTION']) +
            'Encryption must be enabled for token transfer to job sandboxes!\n')
    elif htcondor.param['SEC_DEFAULT_ENCRYPTION'].upper() in ['OPTIONAL', 'PREFERRED']:
        sys.stderr.write(
            'Warning: SEC_DEFAULT_ENCRYPTION = {0} in current HTCondor configuration.\n'.format(htcondor.param['SEC_DEFAULT_ENCRYPTION']) +
            'If communication between a starter and shadow is not encrypted, tokens will not be transferred!\n')

def install_to_apache(
        apache_config_path = os.path.join('/', 'etc', 'httpd', 'conf.d', 'scitokens_credmon.conf'),
        wsgi_path = os.path.join('/', 'var', 'www', 'wsgi-scripts', 'scitokens-credmon', 'scitokens-credmon.wsgi'),
        credmon_web_directory = '/'
        ):

    if not os.path.exists(os.path.dirname(apache_config_path)):
        raise OSError(errno.ENOENT, 'Cannot find Apache config directory', os.path.dirname(apache_config_path))

    # Apache must allow the correct path in the config.
    # This should be the name of the parent directory under /var/www.
    allow_path = wsgi_path
    if wsgi_path[0:8] == '/var/www':
        (parent, child) = os.path.split(wsgi_path)
        i = 0
        while parent != '/var/www':
            (parent, child) = os.path.split(parent)
            i += 1
            if (i > 100) or (parent == ''):
                raise RuntimeError('Infinite loop detected while looking for WSGI allow path')
        allow_path = os.path.join(parent, child)

    if os.path.exists(apache_config_path):
        apache_config_backup = apache_config_path + '.bak'
        shutil.copy2(apache_config_path, apache_config_backup)
        sys.stdout.write('Copied existing {0} to {1}\n'.format(apache_config_path, apache_config_backup))

    apache_config = apache_config_template.format(credmon_web_directory, wsgi_path, allow_path)

    with open(apache_config_path, 'w') as f:
        f.write(apache_config)
        sys.stdout.write('Wrote WSGI config to {0}\n'.format(apache_config_path))

    if not os.path.exists(os.path.dirname(wsgi_path)):
        os.makedirs(os.path.dirname(wsgi_path))
        sys.stdout.write('Created WSGI script directory {0}\n'.format(os.path.dirname(wsgi_path)))

    if os.path.exists(wsgi_path):
        wsgi_backup = wsgi_path + '.bak'
        shutil.copy2(wsgi_path, wsgi_backup)
        sys.stdout.write('Copied existing {0} to {1}\n'.format(wsgi_path, wsgi_backup))

    with open(wsgi_path, 'w') as f:
        f.write(wsgi_code)
        sys.stdout.write('Wrote WSGI script to {0}\n'.format(wsgi_path))

    sys.stderr.write('Remember to check your SSL ciphers in your Apache configuration.\n' +
                         'An example is available in the WSGI config.\n')

def install_dummy():
    return

def install_credmon(server):
    if server is None:
        server = 'none'

    flask_installers = {
        'apache': install_to_apache,
        'none': install_dummy,
    }

    install_to_condor()

    install_to_server = flask_installers[server]
    install_to_server()
