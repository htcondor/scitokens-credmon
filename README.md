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

To install the Scitokens CredMon, you can either use `pip` to install
the latest version in PyPI:
```sh
pip install scitokens-credmon
```
Or you can grab and install an RPM from our
[releases](../../releases).

The RPM includes example configuration and submit files under
`/usr/share/doc/python2-scitokens-credmon-%{version}/`.

### Note about the credential directory

If you are not installing using the RPM, the credential directory
(`SEC_CREDENTIAL_DIRECTORY = /var/lib/condor/credentials` in the
example config file) should be owned by the group condor with the
SetGID bit set and group write permissions:
```
mkdir -p /var/lib/condor/credentials
chgrp condor /var/lib/condor/credentials
chmod 2770 /var/lib/condor/credentials
```
```
# ls -ld /var/lib/condor/credentials
drwxrws--- 3 root condor 4096 May  8 10:05 /var/lib/condor/credentials
```

### Note about daemon-to-daemon encryption

For *both submit and execute hosts*, HTCondor must be configured to
use encryption for daemon-to-daemon communication. You can check this
by running `condor_config_val SEC_DEFAULT_ENCRYPTION` on each host,
which will return `REQUIRED` or `PREFERRED` if encryption is enabled.
If encryption is not enabled, you should add the following to your HTCondor
configuration:
    ```
    SEC_DEFAULT_ENCRYPTION = REQUIRED
    ```

## OAuth2 CredMon Mode

### Submit Host Admin Configuration

1. See the
[example Apache scitokens_credmon.conf config file](examples/config/apache/scitokens_credmon.conf)
for configuring the OAuth2 Token Flask app. The config must point to a WSGI
script that imports and runs the Flask app. If you installed via the
RPM, this will be created for you, otherwise we recommend using the 
[example scitokens-credmon.wsgi script](examples/wsgi/scitokens-credmon.wsgi).

2. See the
[example HTCondor 50-scitokens-credmon.conf config file](examples/config/condor/50-scitokens-credmon.conf)
for configuring HTCondor with the CredD and CredMon.

3. OAuth2 client information should be added to the submit host HTCondor
configuration for any OAuth2 providers that you would like your users
to be able to obtain access tokens from. See the
[example HTCondor 55-oauth-tokens.conf config file](examples/config/condor/55-oauth-tokens.conf).
For each provider:
    * The client id and client secret are generated when you
    register your submit machine as an application with the
    OAuth2 provider's API. The client secret must be kept in a file
    that is only readable by root.
    * You should configure the return URL in your application's settings
    as `https://<submit_hostname>/return/<provider>`.
    * Consult the OAuth2 provider's API documentation to obtain the
    authorization, token, and user URLs.

The HTCondor OAuth2 token configuration parameters are:
```
<PROVIDER>_CLIENT_ID           The client id string
<PROVIDER>_CLIENT_SECRET_FILE  Path to the file with the client secret string
<PROVIDER>_RETURN_URL_SUFFIX   The return URL endpoint for your Flask app ("/return/<provider>")
<PROVIDER>_AUTHORIZATION_URL   The authorization URL for the OAuth2 provider
<PROVIDER>_TOKEN_URL           The token URL for the OAuth2 provider
<PROVIDER>_USER_URL            The user API endpoint URL for the OAuth2 provider
```
Multiple OAuth2 clients can be configured as long as unique names are
used for each `<PROVIDER>`.

Users that request tokens will be directed to a URL on the submit host
containing a unique key. The Flask app will use this key to generate
and present a list of token providers and links to log in to each
provider. Tokens returned from the providers will be stored in the
`SEC_CREDENTIAL_DIRECTORY` under the users' local usernames, and all
tokens will be monitored and refreshed as necessary by the OAuth
CredMon.

### Submit File Commands for Requesting OAuth Tokens

`use_oauth_services = <service1, service2, service3, ...>`

A comma-delimited list of requested OAuth service providers, which
must match (case-insensitive) the <PROVIDER> names in the submit host
config.

`<PROVIDER>_oauth_permissions(_<HANDLE>) = <scope1, scope2, scope3,
...>`

A comma-delimited list of requested scopes for the token provided by
<PROVIDER>. This command is optional if the OAuth provider does not
require a scope to be defined. A <HANDLE> can optionally be provided
to give a unique name to the token (useful if requesting differently
scoped tokens from the same provider).

`<PROVIDER>_oauth_resource(_<HANDLE>) = <resource>`

The resource that the token should request permissions
for. Currently only required when requesting tokens from a Scitokens
provider.

When the job executes, tokens are placed in a subdirectory of the job
sandbox, and can be accessed at
`$_CONDOR_CREDS/<PROVIDER>(_<HANDLE>).use`.

See [examples/submit](examples/submit) for examples of submit files.

## Local Credmon Mode

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
