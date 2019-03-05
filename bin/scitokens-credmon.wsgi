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
