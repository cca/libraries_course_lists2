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
    response = s.get(config.api_root + '/taxonomy')
    response.raise_for_status()
    data = response.json()
    # create file
    with open(taxos_file, 'w') as fh:
        json.dump(data, fh)

    taxos = [Taxonomy(t) for t in data["results"]]
    return taxos


def get_taxos():
    if os.path.exists(taxos_file):
        data = json.load(open(taxos_file, 'r'))
        taxos = [Taxonomy(t) for t in data["results"]]
    else:
        # get data from API, this fn also writes to file
        taxos = download_taxos()

    return taxos
