import re

DOMAINS = {
    'box':               re.compile(r'https://.*\.box\.com'),
    'gdrive':            re.compile(r'https://.*\.googleapis\.com'),
    'onedrive':          re.compile(r'https://.*\.microsoftonline\.com'),
    'dropbox':           re.compile(r'https://.*\.dropboxapi?\.com'),
}

def get_token_name(token_url):
    '''Returns the token name by matching it to the list of token domains'''
    for token_name, domain in DOMAINS.items():
        if domain.match(token_url):
            return token_name
    return None

def user(token_url):
    '''Returns the URL and fields to query for user info'''
    token = get_token_name(token_url)
    if token is None:
        return (None, None)

    url = {
        'box':          'https://api.box.com/2.0/users/me',
        'gdrive':       'https://www.googleapis.com/drive/v3/about',
        'onedrive':     'https://graph.microsoft.com/v1.0/me',
        'dropbox':      'https://api.dropboxapi.com/2/users/get_account',
    }

    field = {
        'box':          ['login'],
        'gdrive':       ['user', 'emailAddress'],
        'onedrive':     ['userPrincipalName'],
        'dropbox':      ['email'],
    }

    return (url[token], field[token])
