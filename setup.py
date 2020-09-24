from setuptools import setup, find_packages

setup(
    name='scitokens-credmon',
    version = '0.7',
    description = 'SciTokens credential monitor for use with HTCondor',
    long_description = open('README.md').read(),
    long_description_content_type = "text/markdown",
    url = 'https://github.com/htcondor/scitokens-credmon',
    author = 'Jason Patton',
    author_email = 'jpatton@cs.wisc.edu',
    license = 'MIT',
    packages = find_packages(),
    scripts = ['bin/condor_credmon_oauth', 'bin/scitokens_credential_producer'],
    install_requires = [
        'htcondor >= 8.8.2',
        'requests_oauthlib',
        'six',
        'flask',
        'cryptography',
        'scitokens'
        ],
    include_package_data = True
    )
