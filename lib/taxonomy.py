import json
from urllib.parse import urlencode

from config import api_root, logger
from .utilities import request_wrapper


class Term:
    def __init__(self, term):
        # children is a list of other Term objects
        self.children = term.get('children', [])
        self.data = term.get('data', {})
        # parents is a list of Term objects
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


    def asPOSTData(self):
        # used to serialize Terms for POSTing to EQUELLA API
        # Basically, include everything EXCEPT UUID because we use this method
        # when creating a term in openEQUELLA
        return {
            "term": self.term,
            "data": self.data,
            "parentUuid": self.parentUuid,
            "index": self.index,
            "readonly": self.readonly,
        }


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
                uuid (str): the UUID of the created taxonomy term or, if the term
                already existed, the UUID of the existing term
        """
        # don't add a term we already have
        existing_term = self.getTerm(term, "fullTerm")
        if existing_term:
            if not existing_term.uuid:
                logger.error("Added a pre-existing term {} to taxonomy {} but we don't know its name, something strange is going on.".format(term, self))
                return None
            return existing_term.uuid

        if type(term) == str:
            term = Term({"term": term})

        s = request_wrapper()
        r = s.post(api_root + '/taxonomy/{}/term'.format(self.uuid), json=term.asPOSTData())

        # if we successfully created a term, store its UUID
        if r.status_code == 200 or r.status_code == 201:
            logger.info('added {} term to {} taxonomy'.format(term, self))
            # EQUELLA puts the UUID in the response's Location header
            # "Location": "https://vault.cca.edu/api/taxonomy/7ef.../term/bc35..."
            term.uuid = r.headers['Location'].split('/term/')[1]
            self.terms.add(term)
        else:
            logger.error(r.json())
            r.raise_for_status()

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
            if value:
                r = s.put(api_root + '/taxonomy/{uuid}/term/{termUuid}/data/{key}/{value}'.format(
                    uuid=self.uuid,
                    termUuid=term.uuid,
                    key=key,
                    value=value
                ))
                r.raise_for_status()
        logger.info('added data to {} term in {} taxonomy'.format(term, self))


    def clear(self):
        """
            delete all terms in the taxonomy
        """
        for term in self.getRootTerms():
            self.remove(term)


    def getTerm(self, search_term, attr="term"):
        """
            args:
                search_term: str|Term item to search for, strings will be cast
                to Terms like Term({"term": "string"})
                attr: attribute of Term object to match with, e.g. term, fullTerm,
                UUID
            returns:
                matched Term object or None if term isn't in the Taxonomy
        """
        if type(search_term) == str:
            search_term = Term({"term": search_term})

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
        logger.debug('Getting root-level taxonomy terms for {}'.format(self))
        s = request_wrapper()
        r = s.get(api_root + '/taxonomy/{}/term'.format(self.uuid))
        r.raise_for_status()
        terms = [Term(t) for t in r.json()]
        for term in terms:
            self.terms.add(term)
        return terms


    def remove(self, term):
        """
            Remove a term from a taxonomy (primarily used to remove semester
            terms from course lists).
            args:
                term (str|Term): either a string ("Fall 2019") or Term object
            returns:
                status (bool): True for successful & False for not
        """
        if type(term) == str:
            found_term = self.getTerm(term, "fullTerm")
            if found_term:
                term = found_term
            else:
                # We hope the term is in the taxonomy root because otherwise we
                # have no way of finding it
                terms = self.getRootTerms()
                # this does _not_ fail gracefully...
                term = next((t for t in terms if t.term == term), None)
                if not term:
                    logger.error('Cannot find term "{}" in taxonomy {}.'.format(term, self))
                    return False

        # Term objects don't necessarily have UUIDs
        if not term.uuid:
            logger.error('Cannot delete {} from {}: need to know the UUID of the term.'
            .format(term, self))
            return False

        s = request_wrapper()
        logger.info('deleting {} term from {} taxonomy'.format(term, self))
        r = s.delete(api_root + '/taxonomy/{}/term/{}'.format(self.uuid, term.uuid))
        self.terms.discard(term)
        # will throw a 500 error if the taxonomy is locked by another user
        # r.json() = {'code': 500, 'error': 'Internal Server Error',
        # 'error_description': 'Taxonomy is locked by another user: {username}'}
        r.raise_for_status()
        # remove term's children (openEQUELLA API does this automatically)
        if len(term.children) > 0:
            for child in term.children:
                self.terms.discard(child)
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
        logger.debug('Searching taxonomy {} for query {} with options {}'.format(self, query, options))
        s = request_wrapper()
        r = s.get(api_root + '/taxonomy/{}/search?q={}&{}'.format(
            self.uuid,
            query,
            urlencode(options),
        ))
        r.raise_for_status()
        return r.json()["results"]
