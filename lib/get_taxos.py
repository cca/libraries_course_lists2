"""
If we have a JSON list of taxonomies from VAULT, return it.
IF we don't, create such a list using the REST API.
"""
import json
import os

from .utilities import request_wrapper
from .taxonomy import Taxonomy
import config

taxos_file = os.path.join('data', 'taxonomies.json')


def download_taxos():
    s = request_wrapper()
    # with 2019.2 API defaults to length=10 if you don't specify it, we want
    # _all_ the taxonomies so just make this a very high number
    r = s.get(config.api_root + '/taxonomy?length=5000')
    r.raise_for_status()
    data = r.json()
    # create file
    with open(taxos_file, 'w') as fh:
        json.dump(data, fh)

    return [Taxonomy(t) for t in data["results"]]


def get_taxos():
    if os.path.exists(taxos_file):
        with open(taxos_file, 'r') as fh:
            data = json.load(fh)
            return [Taxonomy(t) for t in data["results"]]
    else:
        # get data from API, this fn also writes to file
        return download_taxos()
