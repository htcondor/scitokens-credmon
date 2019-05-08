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

## Deployment

After installing the Scitokens CredMon for the first time, some
configuration is required to enable the CredMon and, if desired, the
OAuth2 Token Flask app.

To install a generic configuration to your submit host, run:
```
scitokens_credmon --deploy --apache
```

This creates the credential directory if it does not exist (see note below),
enables the CredD and CredMon in the HTCondor configuration,
places the WSGI script for the OAuth2 Token Flask app in `/var/www`,
and puts the OAuth2 Token Flask app at the root of your Apache webserver.
To change the HTCondor or Apache configurations, edit either
`/etc/condor/config.d/50-scitokens-credmon.conf` or
`/etc/httpd/conf.d/scitokens_credmon.conf`. See the following notes
for some important manual configurations details.

After installing the configuration, you must (re)start Apache and HTCondor.

### Note about the credential directory

`scitokens_credmon --deploy` may create the credential directory with
inappropriate permissions. The credential directory
(`condor_config_val SEC_CREDENTIAL_DIRECTORY`) should be owned by the
group condor with the SetGID bit set and group write permissions:
```
chgrp condor $(condor_config_val SEC_CREDENTIAL_DIRECTORY)
chmod 2770 $(condor_config_val SEC_CREDENTIAL_DIRECTORY)
```
```
# ls -ld $(condor_config_val SEC_CREDENTIAL_DIRECTORY)
drwxrws--- 3 root condor 4096 May  8 10:05 /var/lib/condor/credentials
```

### Note about execute nodes
The "new" OAuth2 token mode must also be enabled in the HTCondor config of
all execute nodes that you wish to be able to send tokens to by adding:
```
CREDD_OAUTH_MODE = TRUE
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

If you used `scitokens_credmon --deploy --apache`, you can skip to step 3.

1. See the
[example scitokens_credmon.conf](examples/config/apache/scitokens_credmon.conf)
for configuring the OAuth2 Token Flask app. The config must point to a WSGI
script that imports and runs the Flask app, see the 
[example scitokens-credmon.wsgi](examples/wsgi/scitokens-credmon.wsgi).

2. See the
[example 50-scitokens-credmon.conf](examples/config/condor/50-scitokens-credmon.conf)
for configuring HTCondor with the CredD and CredMon.

3. OAuth2 client information should be added to the submit host HTCondor
configuration for any OAuth2 providers that you would like your users
to be able to obtain access tokens from. If you installed your
configuration using `scitokens_credmon --deploy`, an example is given
in `60-oauth-token-providers.conf` in your `config.d` directory, otherwise
see the
[example 60-oauth-token-providers.conf](examples/config/condor/50-scitokens-credmon.conf).
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
For example, for Box.com, you could configure HTCondor as follows:
```
BOX_CLIENT_ID = changeme
BOX_CLIENT_SECRET_FILE = /etc/condor/.secrets/box
BOX_RETURN_URL_SUFFIX = /return/box
BOX_AUTHORIZATION_URL = https://account.box.com/api/oauth2/authorize
BOX_TOKEN_URL = https://api.box.com/oauth2/token
BOX_USER_URL = https://api.box.com/2.0/users/me
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

#### Example - Requesting a single Box token

Suppose the admin has configured your submit host following the
`BOX_...` example above. Box.com does not require tokens to be scoped,
so the only command required in your submit file is:

```
use_oauth_services = box
```

When this job runs, the token will be placed at
`$_CONDOR_CREDS/box.use`.

#### Example - Requesting multiple Box tokens

Even though Box.com does not required scoped tokens, to generate
multiple Box tokens, you must provide a custom handle for each Box
token using an empty `box_oauth_permissions_<HANDLE>` command. For
example:

```
use_oauth_services = box

box_oauth_permissions_foo =
box_oauth_permissions_bar =
```

When this job runs, the tokens will be placed at
`$_CONDOR_CREDS/box_foo.use` and `$_CONDOR_CREDS/box_bar.use`.

#### Example - Requesting Scitokens tokens

Suppose the admin has configured your submit host with a Scitokens
provider named "UXYZ_SCITOKENS". And suppose you have read and write
access to the `/public` directory on a resource named
`https://data.uxyz.edu`. You can request a Scitoken for this resource
using the following commands:

```
use_oauth_services = uxyz_scitokens
uxyz_scitokens_oauth_permissions = read:/public, write:/public
uxyz_scitokens_oauth_resource = https://data.uxyz.edu
```

When this job runs, the token will be placed at
`$_CONDOR_CREDS/uxyz_scitokens.use`.

#### Example - Requesting Box and Scitokens tokens

Putting together the above examples, you can request tokens from
multiple providers:

```
use_oauth_services = box, uxyz_scitokens

box_oauth_permissions_personal =
box_oauth_permissions_uxyz =

uxyz_scitokens_oauth_permissions_read = read:/public/input
uxyz_scitokens_oauth_resource_read = https://input_data.uxyz.edu

uxyz_scitokens_oauth_permissions_write = write:/public/output
uxyz_scitokens_oauth_resource_write = https://output_data.uxyz.edu
```

From this example, you would get four tokens under the
`$_CONDOR_CREDS` directory:
`box_personal.use`, `box_uxyz.use`, `uxyz_scitokens_read.use`, and
`uxyz_scitokens_write.use`.

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
