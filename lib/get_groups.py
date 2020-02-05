"""
If we have a JSON list of groups from VAULT, return it.
IF we don't, create such a list using the REST API.
Direct copy of logic from get_taxos.py
"""
import json
import os

from .utilities import request_wrapper
from .group import Group
import config

groups_file = os.path.join('data', 'groups.json')


def download_groups():
    s = request_wrapper()
    response = s.get(config.api_root + '/usermanagement/local/group?allParents=true')
    response.raise_for_status()
    data = response.json()
    # create file
    with open(groups_file, 'w') as fh:
        json.dump(data, fh)

    config.logger.info('Downloaded group JSON data from API.')
    return [Group(g) for g in data["results"]]


def get_groups():
    config.logger.info('Getting group JSON data.')
    if os.path.exists(groups_file):
        with open(groups_file, 'r') as fh:
            data = json.load(fh)
            return [Group(g) for g in data["results"]]
    else:
        # get data from API, this fn also writes to file
        return download_groups()
