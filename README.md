# HTCondor Scitokens CredMon

The HTCondor Scitokens CredMon monitors and refreshes credentials
that are being managed by the HTCondor CredD. This package also
includes a Flask application that users can be directed to in order to
obtain OAuth2 tokens from services for which an HTCondor pool
administrator has configured clients. The CredMon will then monitor
and refresh these OAuth2 tokens, and HTCondor can use and/or send the
tokens with users' jobs as requested by the user.

### Prerequisites

* HTCondor 8.8.1+
* Python 2.7+
* HTTPS-enabled web server (Apache, nginx, etc.)
* WSGI server (mod_wsgi, uWSGI, gunicorn, etc.)

## Installation

To install the latest version of the Scitokens CredMon:
```sh
pip install git+https://github.com/htcondor/scitokens-credmon
```

The installation writes (or overwrites) a number of configuration
files that set the stage for enabling the CredMon, including the
OAuth2 tokens Flask app. You may want to back up these files before
installing or upgrading if you have made changes to them. You may also
want to inspect them following an install to understand any changes
these files make to your system's services:

```
/etc/condor/config.d/50-scitokens-credmon.conf  HTCondor configuration file
/etc/httpd/conf.d/scitokens_credmon.conf        Apache configuration file for the Flask app
```

## Deployment

After installing the Scitokens CredMon, some configuration is required
to enable the CredMon and, if desired, the OAuth2 Token Flask app.

1. Create or modify HTCondor's credential directory
(`condor_config_val SEC_CREDENTIAL_DIRECTORY`) such that it is owned
by the group condor, not readable by others, with the SetGID bit set:
    ```sh
     [jcpatton@localhost ~]$ CREDDIR=$(condor_config_val SEC_CREDENTIAL_DIRECTORY)
     [jcpatton@localhost ~]$ sudo mkdir $CREDDIR # may already exist
     [jcpatton@localhost ~]$ sudo chgrp condor $CREDDIR
     [jcpatton@localhost ~]$ sudo chmod 2770 $CREDDIR
    ```

2. On HTCondor submit hosts, uncomment the `DAEMON_LIST` line in
`/etc/condor/config.d/50-scitokens-credmon.conf` so that it reads:
    ```
	DAEMON_LIST = $(DAEMON_LIST), CREDD, SEC_CREDENTIAL_MONITOR
    ```
	This tells HTCondor to start the CredD and CredMon when HTCondor
	starts.

3. On HTCondor execute hosts, you may choose to install the HTCondor
Scitokens CredMon Python package and follow the same steps above, or
you may manually add the following to the HTCondor configuration:
	```
	DAEMON_LIST = $(DAEMON_LIST), CREDD
    CREDD_OAUTH_MODE = TRUE
	SEC_CREDENTIAL_DIRECTORY = /var/lib/condor/credentials
    ```
	The `SEC_CREDENTIAL_DIRECTORY` must exist and be owned by root.

OAuth CredMon Mode
------------------
`/etc/httpd/conf.d/scitokens_credmon.conf` adds the OAuth2 tokens
Flask app at the root of your Apache webserver. With this
configuration, the app will run as long as Apache is running.

OAuth2 client information should be added to the submit host HTCondor
configuration for any OAuth2 providers that you would like your users
to be able to obtain access tokens from. For each provider:
  * The client id and client secret are generated when you
  register your submit machine as an application with the
  OAuth2 provider's API. The client secret must be kept in a file
  that is only readable by root.
  * You should configure the return URL in your application's settings
  as `https://<submit_hostname>/return/<provider>`.
  * Consult the OAuth2 provider's API documentation to obtain the
  authorization, token, and user URLs.

The HTCondor configuration parameters are:
```
<PROVIDER>_CLIENT_ID           The client id string
<PROVIDER>_CLIENT_SECRET_FILE  Path to the file with the client secret string
<PROVIDER>_RETURN_URL_SUFFIX   The return URL endpoint for your Flask app ("/return/<provider>")
<PROVIDER>_AUTHORIZATION_URL   The authorization URL for the OAuth2 provider
<PROVIDER>_TOKEN_URL           The token URL for the OAuth2 provider
<PROVIDER>_USER_URL            The user API endpoint URL for the OAuth2 provider
```
For example, for Box.com, you could configure HTCondor as follows:
```
BOX_CLIENT_ID = your_box_client_id
BOX_CLIENT_SECRET_FILE = /etc/condor/.secrets/box
BOX_RETURN_URL_SUFFIX = /return/box
BOX_AUTHORIZATION_URL = https://account.box.com/api/oauth2/authorize
BOX_TOKEN_URL = https://api.box.com/oauth2/token
BOX_USER_URL = https://api.box.com/2.0/users/me
```
Multiple OAuth2 clients can be configured as long as unique names are
used for `<PROVIDER>`.

Users that request tokens will be directed to a URL on the submit host
containing a unique key. The Flask app will use this key to generate
and present a list of token providers and links to log in to each
provider. Tokens returned from the providers will be stored in the
`SEC_CREDENTIAL_DIRECTORY` under the users' local usernames, and all
tokens will be monitored and refreshed as necessary by the OAuth
CredMon.

Local Credmon Mode
------------------

In the "local mode", the credmon will use a provided private key to sign a SciToken
directly, bypassing any OAuth callout.  This is useful in the case where the admin
wants a less-complex setup than a full OAuth deployment.

The following condor configuration directives set up the local credmon mode:
```
# The credential producer invoked by `condor_submit`; causes the credd to be invoked
# prior to the job being submitted.
SEC_CREDENTIAL_PRODUCER = /usr/bin/scitokens_credential_producer

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
