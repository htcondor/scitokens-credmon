# HTCondor Scitokens CredMon

The HTCondor Scitokens CredMon monitors and refreshes credentials
that are being managed by the HTCondor CredD. This package also
includes a Flask application that users can be directed to in order to
obtain OAuth2 tokens from services for which an HTCondor pool
administrator has configured clients. The CredMon will then monitor
and refresh these OAuth2 tokens, and HTCondor can use and/or send the
tokens with users' jobs as requested by the user.

## *** NOTICES ***
* **Development:** Development of the HTCondor Scitokens CredMon has
been moved to the [HTCondor source repository](https://github.com/htcondor/htcondor)
under `src/condor_credd/condor_credmon_oauth`.
* **Installation:** Starting with [HTCondor version 8.9.9](https://htcondor.readthedocs.io/en/latest/version-history/development-release-series-89.html#version-8-9-9),
the `condor_credmon_oauth` package should be installed from the
[HTCondor Enterprise Linux repository](https://research.cs.wisc.edu/htcondor/instructions/).
Older versions should be uninstalled first.
* **Documentation:** Set up and administration of the credmon is now
covered in the [HTCondor Administrator's Manual](https://htcondor.readthedocs.io/en/latest/admin-manual/setting-up-special-environments.html#enabling-the-fetching-and-use-of-oauth2-credentials),
and usage of OAuth2 credentials is now covered in the [HTCondor User's Manual](https://htcondor.readthedocs.io/en/latest/users-manual/submitting-a-job.html#jobs-that-require-credentials).
The remaining documentation here covers the local issuer mode of the
credmon and the Docker image, which are currently undocumented in the
HTCondor manual.

### Prerequisites

* HTCondor 8.8.2+
* Python 2.7+
* HTTPS-enabled web server (Apache, nginx, etc.)
* WSGI server (mod_wsgi, uWSGI, gunicorn, etc.)

### Docker Container

This repository provides a Docker image for users who want to experiment
with a personal HTCondor install with the Scitokens CredMon installed.
For details, see the [instructions for using the Docker
container](#docker-container-setup) below.

## Local Credmon Mode

In the "local mode", the credmon will use a provided private key to sign a Scitoken
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

## Docker Container Setup

We assume that this container is running with the hostname `schedd.client.address`
Register the client with a Scitokens server. When registering this client, the callback URL should be
```
https://schedd.client.address:443/return/scitokens
```
You will need to enter one of more audiences and one or more scope request templates for each audience when you register the client. These values will be used to set `scitokens_oauth_resource` and `scitokens_oauth_permissions` in the condor submit file when you run a job.

Record the values of client ID and client secret provided by the server and use them to set the build arguments below.

### Build the Docker image

Obtain an X509 host certificate and key pair and put them in the directory
`docker` in this repository. Then build the image with:
```
docker build \
  --build-arg SCITOKENS_CLIENT_ID='myproxy:oa4mp,2012:/client_id/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
  --build-arg SCITOKENS_CLIENT_SECRET='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
  --build-arg SCITOKENS_AUTHORIZATION_URL=https://scitokens.server.address:443/scitokens-server/authorize \
  --build-arg SCITOKENS_TOKEN_URL=https://scitokens.server.address:443/scitokens-server/token \
  --build-arg SCITOKENS_USER_URL=https://scitokens.server.address:443/scitokens-server/userinfo \
  --rm -t scitokens/htcondor-submit .
```

### Run the Docker image

Edit `docker-compose.yml` to set the `hostname` and `domainname` to be the name of the machine on which this container will run so that it is visible from the outside world.

```
docker-compose up -d
```

### Testing the CredMon with the Docker image

The docker container has an unpriveleged user named `submitter` who can submit jobs to the schedd. To log into the container as this user, run the following command from the host:
```sh
docker exec -it scitokens-credmon_scitokens-htcondor_1 /bin/su -l submitter
```
Once logged in, you will find a submit file names `test.sub`. Edit this file and set the arguments `scitokens_oauth_resource` to one of the audiences that the Schedd is configured to access, and set `scitokens_oauth_permissions` to a valid scope for that audience. For example, of you registered `my.host.org` as an audience with a scope template of `read:/public/**` in the SciTokens server, then
```
scitokens_oauth_resource = my.host.org
scitokens_oauth_permissions = read:/public
```
would be valid configurations to get a SciToken for `read:/public` access on `my.host.org`.

Once you have edited the submit file, you can submit it in the usual way with
```sh
condor_submit test.sub
```
You will provided with a URL to visit the CredMon to authorize the HTCondor to obtain the required SciToken. Once you have done this, you can re-submit the job by running
```sh
condor_submit test.sub
```
Monitor the statis of the job in the usual way by looking at the job userlog or `condor_q`. Once the job completes, the output file will contain a dump of:
 * The job environment as printed by `env`. Look for the value of `_CONDOR_CREDS` which is set to the path to the directory where the tokens reside.
 * A listing of the directory specified by `_CONDOR_CREDS`. Look for a `scitokens.use` file that contains the token.
 * A dump of all the files in the directory `_CONDOR_CREDS`, including `scitokens.use`. This should contain JSON that contains an `access_token` containing the SciToken itself.
