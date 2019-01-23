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
2. Point `condor_config` to the credential directory, the location of
`condor_credmon`, and to where the CredMon's log file should be written:
	```
	SEC_CREDENTIAL_DIR = /var/lib/condor/credentials
    SEC_CREDENTIAL_MONITOR = /usr/bin/condor_credmon
    SEC_CREDENTIAL_MONITOR_LOG = /var/log/condor/CredMon
    ```
3. Modify the `condor_config` to enable the HTCondor CredD to work
with the CredMon:
    ```
    TOKENS = True
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
