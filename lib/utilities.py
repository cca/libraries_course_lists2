import re

import requests

import config


def request_wrapper():
    if not config.token:
        raise Exception('I need an OAuth token in config.py to work.')

    s = requests.Session()
    headers = {
        'Accept': 'application/json',
        'X-Authorization': 'access_token=' + config.token,
    }
    s.headers.update(headers)
    return s


def strip_prefix(string):
    """
    A lot of Workday names, which we are unfortunately forced to use as identifiers,
    being with a "AX_..." prefix as in "AU_CERAM" (for the Ceramics academic unit)
    or "AP_Fall_2019" for the Fall academic period. We need these names for
    matching but don't use this prefix.
    """
    return re.sub(r'^A[A-Z]_', '', string)
