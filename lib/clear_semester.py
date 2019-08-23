"""
Given a course list taxonomy and a semester term (e.g. "Fall 2019"), delete that
term. Automatically deletes all child terms as well.
"""
import config
from .utilities import request_wrapper

def clear_semester(taxo, semester):
    s = request_wrapper()
    # https://vault.cca.edu/apidocs.do#!/taxonomy/getTaxonomyTerms_get_10
    # requesting /tax/uuid/term gets the root of the taxonomy which is where
    # all semester terms will be
    r = s.get(config.api_root + '/taxonomy/{}/term'.format(taxo.uuid))
    for term in r.json():
        if term["term"] == semester:
            print('deleting {} from {}'.format(semester, taxo))
            s.delete(config.api_root + '/taxonomy/{}/term/{}'.format(taxo.uuid, term["uuid"]))
            break
