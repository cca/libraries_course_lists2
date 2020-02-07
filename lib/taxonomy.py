import json
from urllib.parse import urlencode

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
        self.index = term.get('index', 0)
        self.readonly = term.get('readonly', False)


    def __repr__(self):
        return self.fullTerm

    @property
    def fullTerm(self):
        # string form of term's path e.g. Fall 2019\ANIMA\Jane Doe...
        return '\\'.join([p.term for p in self.parents] + [self.term])


    def asJSON(self):
        # used to serialize Terms for POSTing to EQUELLA API
        # Basically, include everything EXCEPT UUID because we use this method
        # when creating a term in openEQUELLA
        return json.dumps({
            "term": self.term,
            "data": self.data,
            "parentUuid": self.parentUuid,
            "index": self.index,
            "readonly": self.readonly,
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
        """
            add a Term to a Taxonomy, also adds the Terms data nodes to itself
            args:
                term (Term)
            returns:
                uuid (str): identifier of the created taxonomy term
        """
        # don't add a term we already have
        existing_term = self.getTerm(term)
        if existing_term is not None:
            return existing_term.uuid

        s = request_wrapper()
        r = s.post(config.api_root + '/taxonomy/{}/term'.format(self.uuid), data=term.asJSON())

        config.logger.info('added {} term to {} taxonomy'.format(term, self))
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
        """
        add a taxonomy term's data nodes to itself
        args:
            term (Term): a term object with a term.data dict
        returns:
            nothing
        """
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
        config.logger.info('added data to {} term in {} taxonomy'.format(term, self))


    def getTerm(self, search_term, attr="fullTerm"):
        """
            args:
                search_term: Term object
                attr: attribute of Term object to match with
            returns:
                matched Term object or None if term isn't in the Taxonomy
        """
        for term in self.terms:
            if getattr(term, attr) == getattr(search_term, attr):
                return term
        return None


    def getRootTerms(self):
        """
            return list of terms in taxonomy root, you can then add them to the
            taxonomy object like `for te in taxo.getRootTerms(): taxo.add(te)`
            args: (none)
            returns:
                root terms (list): list of Term objects
        """
        config.logger.debug('Getting root-level taxonomy terms for {}'.format(self))
        s = request_wrapper()
        r = s.get(config.api_root + '/taxonomy/{}/term'.format(self.uuid))
        r.raise_for_status()
        return [Term(t) for t in r.json()]


    def remove(self, term):
        """
            Remove a term from a taxonomy (primarily used to remove semester
            terms from course lists). ONLY REMOVES ROOT-LEVEL TERMS RIGHT NOW.
            args:
                term (Term): either a string ("Fall 2019") or Term object
            returns:
                status (bool): True for successful & False for not
        """
        s = request_wrapper()
        if type(term) == str:
            # NOTE: you can get a term with /tax/{uuid}/term?path={string}
            # but it always seems to return the children of `string` e.g. for
            # SEMESTER\COURSE it'll return the instructor names beneath `COURSE`
            # But requesting /tax/uuid/term gets the root of the taxonomy which
            # is where all semester terms will be
            r = s.get(config.api_root + '/taxonomy/{}/term'.format(self.uuid))
            r.raise_for_status()
            # convert to a term object
            term = Term([t for t in r.json() if t["term"] == term][0])

        # Term objects don't necessarily have UUIDs
        if not term.uuid:
            config.logger.error('Cannot delete {} from {}: need to know the UUID of the term.'
            .format(term, self))
            return False

        config.logger.info('deleting {} term from {} taxonomy'.format(term, self))
        r = s.delete(config.api_root + '/taxonomy/{}/term/{}'.format(self.uuid, term.uuid))
        # will throw a 500 error if the taxonomy is locked by another user
        # r.json() = {'code': 500, 'error': 'Internal Server Error',
        # 'error_description': 'Taxonomy is locked by another user: {username}'}
        r.raise_for_status()
        return True


    def search(self, query, options={}):
        """
            find a term anywhere within the taxonomy

            args:
                query (str): search term text for this
                options (dict):
                    restriction (str): "TOP_LEVEL_ONLY"|"LEAF_ONLY"
                    (defaults to unrestricted)
                    limit (int): limit search results to this number
                    searchfullterm (bool): search across the full term path (e.g.
                    text of the term and all its parents), is False by default
            returns:
                list of Term-like dicts {"term": "entry", "fullTerm":
                "parent\\entry"} note that they lack the Term UUID :( and thus
                are kinda useless
        """
        config.logger.debug('Searching taxonomy {} for query {} with options {}'.format(self, query, options))
        s = request_wrapper()
        r = s.get(config.api_root + '/taxonomy/{}/search?q={}&{}'.format(
            self.uuid,
            query,
            urlencode(options),
        ))
        r.raise_for_status()
        return r.json()["results"]
