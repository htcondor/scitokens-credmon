#
# Configure Logging
#

from credmon.utils import setup_logging, get_cred_dir
import os
import logging

cred_dir = get_cred_dir()
logger = setup_logging(log_path = os.path.join(cred_dir, 'oauth_credmon_webserver.log'),
                       log_level = logging.DEBUG)

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
