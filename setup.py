from setuptools import setup, find_packages

setup(name='scitokens-credmon',
      version = '0.1',
      description = 'Scitokens credential monitor for use with HTCondor',
      url = 'https://github.com/htcondor/scitokens-credmon',
      author = 'Jason Patton',
      author_email = 'jpatton@cs.wisc.edu',
      license = 'MIT',
      packages = find_packages(),
      scripts = ['bin/condor_credmon'],
      install_requires = [
          'htcondor',
          'requests_oauthlib==1.0.0',
          'six',
          'flask'
          ],
      include_package_data = True
    )
