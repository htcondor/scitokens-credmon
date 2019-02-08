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

`condor_credmon` should now be in your `PATH`.

See *Deployment* for configuring and launching the `condor_credmon`
and associated Flask application.

### Prerequisites

* HTCondor 8.8.0+
* Python 2.7+

