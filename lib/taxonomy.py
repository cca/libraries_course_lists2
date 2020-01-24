import json

import config
from .utilities import request_wrapper


class Term:
    def __init__(self, term):
        # children is a list of other Term objects
        self.children = term.get('children', [])
        self.data = term.get('data', {})
        # parents is a list of _strings_ not Term objects
        self.parents = term.get('parents', [])
        self.parentUuid = term.get('parentUuid', None)
        self.term = term['term']
        self.uuid = term.get('uuid', None)


    def __repr__(self):
        return self.fullTerm

    @property
    def fullTerm(self):
        # string form of term's path e.g. Fall 2019\ANIMA\Jane Doe...
        return '\\'.join(self.parents + [self.term])


    def asJSON(self):
        # used to serialize Terms for POSTing to EQUELLA API
        # I don't _think_ we need to include fullTerm
        return json.dumps({
            "parentUuid": self.parentUuid,
            "term": self.term,
        })


class Taxonomy:
    def __init__(self, taxo):
        self.name = taxo["name"]
        # initialize as empty set, populated by add() method
        self.terms = set()
        # unlike with terms we will always know the taxonomy UUID upfront
        self.uuid = taxo["uuid"]


    def __repr__(self):
        return self.name


    def add(self, term):
        """ args: term is a Term object
            returns: uuid (str) of created taxonomy term
            throws: HTTP errors from requests
        """
        # don't add a term we already have
        existing_term = self.get(term)
        if existing_term is not None:
            return existing_term.uuid

        s = request_wrapper()
        r = s.post(config.api_root + '/taxonomy/{}/term'.format(self.uuid), data=term.asJSON())

        print('added {} to {}'.format(term, self))
        # if we successfully created a term, store its UUID
        if r.status_code == 200 or r.status_code == 201:
            # EQUELLA puts the UUID in the response's Location header
            # "Location": "https://vault.cca.edu/api/taxonomy/7ef.../term/bc35..."
            term.uuid = r.headers['Location'].split('/term/')[1]
        self.terms.add(term)
        if term.data:
            self.addData(term)
        return term.uuid


    def addData(self, term):
        """ add a taxonomy term's data nodes to itself
        NOTE: this API route seems broken & this doesn't work yet """
        print(term, term.data, term.uuid)
        if not term.uuid:
            raise Exception("""
                Cannot add data to taxonomy term without the term's UUID.
                Term: {}
                Taxo: {}
                """.format(term, self))

        s = request_wrapper()
        for key, value in term.data.items():
            r = s.put(config.api_root + '/taxonomy/{uuid}/term/{termUuid}/data/{key}/{value}'.format(
                uuid=self.uuid,
                termUuid=term.uuid,
                key=key,
                value=value
            ))
            r.raise_for_status()
        print('added data to {} term in {} taxo'.format(term, self))


    def get(self, term, attr="fullTerm"):
        """
            args:
                term: Term object
                attr: attribute of Term object to match with
            returns:
                matched Term object or None if term isn't in the Taxonomy
        """
        for t in self.terms:
            if getattr(t, attr) == getattr(term, attr):
                return term
        return None


    def remove(self, term):
        """
            Remove a term from a taxonomy (primarily used to remove semester
            terms from course lists). ONLY REMOVES ROOT-LEVEL TERMS RIGHT NOW.
            args:
                term: either a string ("Fall 2019") or Term object
            returns:
                nothing
        """
        s = request_wrapper()
        if type(term) == str:
            # NOTE: you can get a term with /tax/{uuid}/term?path={string}
            # but it always seems to return the children of string e.g. for
            # Fall 2019\Course Name it'll return all the instructor names
            # But requesting /tax/uuid/term gets the root of the taxonomy which
            # is where all semester terms will be
            r = s.get(config.api_root + '/taxonomy/{}/term'.format(self.uuid))
            r.raise_for_status()
            # convert to a term object
            term = Term([t for t in r.json() if t["term"] == term][0])

        print('deleting {} from {}'.format(term, self))
        r = s.delete(config.api_root + '/taxonomy/{}/term/{}'.format(self.uuid, term.uuid))
        # will through a 500 error if the taxonomy is locked by another user
        # r.json() = {'code': 500, 'error': 'Internal Server Error',
        # 'error_description': 'Taxonomy is locked by another user: {username}'}
        r.raise_for_status()
