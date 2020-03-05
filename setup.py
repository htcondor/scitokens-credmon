from setuptools import setup, find_packages

setup(
    name='scitokens-credmon',
    version = '0.5',
    description = 'SciTokens credential monitor for use with HTCondor',
    long_description = open('README.md').read(),
    long_description_content_type = "text/markdown",
    url = 'https://github.com/htcondor/scitokens-credmon',
    author = 'Jason Patton',
    author_email = 'jpatton@cs.wisc.edu',
    license = 'MIT',
    packages = find_packages(),
    scripts = ['bin/scitokens_credmon', 'bin/scitokens_credential_producer'],
    install_requires = [
        'htcondor >= 8.8.0',
        'requests_oauthlib==1.0.0',
        'six',
        'flask',
        'cryptography',
        'scitokens'
        ],
    include_package_data = True
    )
