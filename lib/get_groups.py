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
    response = s.get(config.api_root + '/usermanagement/local/group')
    response.raise_for_status()
    data = response.json()
    # create file
    with open(groups_file, 'w') as fh:
        json.dump(data, fh)

    groups = [Group(g) for g in data["results"]]
    return groups


def get_groups():
    if os.path.exists(groups_file):
        data = json.load(open(groups_file, 'r'))
        groups = [Group(g) for g in data["results"]]
    else:
        # get data from API, this fn also writes to file
        groups = download_groups()

    return groups
