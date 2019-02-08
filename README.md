# HTCondor Scitokens CredMon

The HTCondor Scitokens CredMon monitors and refreshes credentials
that are being managed by the HTCondor CredD. This package also
includes a Flask application that users can be directed to in order to
obtain OAuth tokens from services for which an HTCondor pool
administrator has configured clients. The CredMon will then monitor
and refresh these OAuth tokens, and HTCondor can use and/or send the
tokens with users' jobs as requested by the user.

## Installation

Install the latest version of the CredMon in an environment accessible
by the same user as the user running the HTCondor daemons:
```sh
pip install git+https://github.com/htcondor/scitokens-credmon
```

`condor_credmon` should now be in your `PATH`. (By default, on Linux,
this is `/usr/bin/condor_credmon`.)

See **Deployment** for configuring and launching the `condor_credmon`
and associated Flask application.

### Prerequisites

* HTCondor 8.8.1+
* Python 2.7+
* HTTPS-enabled web server (Apache, nginx, etc.)
* WSGI server (mod_wsgi, uWSGI, gunicorn, etc.)

## Deployment

After installation of the credmon binaries, the admin needs to inform HTCondor of
the location of the credmon and that it should be run by default.

1. Decide on a directory where credentials (and related CredMon files)
will be stored. Create the directory owned by the group condor, not
readable by others, with the SetGID bit set. For example, to create
the directory under `/var/lib/condor/credentials`:
    ```sh
     [jcpatton@localhost ~]$ SEC_CREDENTIAL_DIR=/var/lib/condor/credentials
     [jcpatton@localhost ~]$ sudo mkdir $SEC_CREDENTIAL_DIR
     [jcpatton@localhost ~]$ sudo chgrp condor $SEC_CREDENTIAL_DIR
     [jcpatton@localhost ~]$ sudo chmod 2770 $SEC_CREDENTIAL_DIR
    ```
    After creating the directory:
    ```sh
    [jcpatton@localhost ~]$ sudo ls -dl $SEC_CREDENTIAL_DIR
    drwxrws--- 2 root condor 4096 Jan 23 15:00
    /var/lib/condor/credentials
    ```
2. On the `condor_schedd` host, add the following
to a configuration file in `/etc/condor/config.d` or wherever the `$CONDOR_CONFIG` variable
references:
	```
	SEC_CREDENTIAL_DIRECTORY = /var/lib/condor/credentials
    # PYTHONPATH only needs to be set if the credmon is not installed to system Python
    SEC_CREDENTIAL_MONITOR_ENVIRONMENT = "PYTHONPATH=/var/lib/scitokens-credmon"
    SEC_CREDENTIAL_MONITOR = /usr/bin/condor_credmon
    SEC_CREDENTIAL_MONITOR_LOG = /var/log/condor/CredMon
    ```
3. Modify the `condor_config` to enable the HTCondor CredD and to have
the CredD transfer credentials to job sandboxes:
    ```
    DAEMON_LIST = $(DAEMON_LIST), CREDD
    CREDD_OAUTH_MODE = True
    ```
4. Add OAuth client information to the `condor_config` for any OAuth
providers that you would like your users to be able to obtain
access tokens from.
  * The client id and client secret are usually generated when you
  register your submit machine as an application with the
  OAuth provider's API. The client secret should be kept in a file
  that is only readable by root.
  * Consult the OAuth provider API documentation to obtain the
  authorization endpoint URL and the token endpoint URL.
5. Configure the Flask application using WSGI in your web server
config.
6. On the HTCondor execute hosts, add the following to the configuration file:
    ```
    CREDD_OAUTH_MODE = TRUE
    # NOTE: credd will refuse to transfer tokens on a non-encrypted link.
    SEC_DEFAULT_ENCRYPTION=REQUIRED
    ```

Local Credmon Mode
------------------

In the "local mode", the credmon will use a provided private key to sign a SciToken
directly, bypassing any OAuth callout.  This is useful in the case where the admin
wants a less-complex setup than a full OAuth deployment.

The following configuration directives setup the local credmon mode:
```
# The credential producer invoked by `condor_submit`; causes the credd to be invoked
# prior to the job being submitted.
SEC_CREDENTIAL_PRODUCER = /var/lib/scitokens-credmon/bin/scitokens_credential_producer

# Path to the private keyfile
# LOCAL_CREDMON_PRIVATE_KEY = /etc/condor/scitokens-private.pem

# The issuer location; relying parties will need to be able to access this issuer to
# download the corresponding public key.
# LOCAL_CREDMON_ISSUER = https://$(FULL_HOSTNAME)

# The authorizations given to the token.  Should be of the form `authz:path` and
# space-separated for multiple authorizations.  The token `{username}` will be
# expanded with the user's Unix username.
# LOCAL_CREDMON_AUTHZ_TEMPLATE = read:/user/{username} write:/user/{username}

# The lifetime, in seconds, for a new token.  The credmon will continuously renew
# credentials on the submit-side.
# LOCAL_CREDMON_TOKEN_LIFETIME = 1200

# Each key must have a name that relying parties can look up; defaults to "local"
# LOCAL_CREDMON_KEY_ID = key-es356
```
