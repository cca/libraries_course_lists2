from urllib.parse import urlencode, quote

import requests

from config import api_root, logger
from .utilities import get_headers


class Term:
    def __init__(self, term):
        self.children: list[Term] = term.get("children", [])
        self.data = term.get("data", {})
        self.parents: list[Term] = term.get("parents", [])
        self.parentUuid = term.get("parentUuid", None)
        self.term = term.get("term", None)
        self.uuid = term.get("uuid", None)
        self.index = term.get("index", 0)
        self.readonly = term.get("readonly", False)

    def __repr__(self):
        return self.fullTerm

    def __eq__(self, other):
        if type(other) != Term:
            return False
        if self.uuid == other.uuid:
            return True
        if not self.uuid or not other.uuid:
            return self.fullTerm == other.fullTerm
        return False

    def __hash__(self):
        return hash((self.uuid, self.fullTerm))

    @property
    def fullTerm(self):
        # string form of term's path e.g. Fall 2019\ANIMA\Jane Doe...
        return "\\".join([p.term for p in self.parents] + [self.term])

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
        # initialize as empty set, populated by getRootTerms() & add() methods
        self.terms = set()
        # unlike with terms we always know the taxonomy UUID upfront
        self.uuid = taxo["uuid"]

    def __repr__(self):
        return self.name

    def add(self, term):
        """
        add a Term to a Taxonomy, also adds the Terms data nodes to itself
        args:
            term (Term|str): term to be added, if a string is passed it will
            be added as a root-level term
        returns:
            uuid (str): the UUID of the created taxonomy term or, if the term
            already existed, the UUID of the existing term
        """
        if type(term) == str:
            term = Term({"term": term})

        # don't add a term we already have
        existing_term = self.getTerm(term, "fullTerm")
        if existing_term:
            logger.debug('Term "{}" is already in taxonomy "{}".'.format(self, term))
            return existing_term.uuid

        r = requests.post(
            api_root + "/taxonomy/{}/term".format(self.uuid),
            json=term.asPOSTData(),
            headers=get_headers(),
        )
        # if we successfully created a term, store its UUID
        if r.status_code == 200 or r.status_code == 201:
            logger.info("added {} term to {} taxonomy".format(term, self))
            # EQUELLA puts the UUID in the response's Location header
            # "Location": "https://vault.cca.edu/api/taxonomy/7ef.../term/bc35..."
            term.uuid = r.headers["Location"].split("/term/")[1]
            self.terms.add(term)
            # if it's a child term, add it to the parent's list of children
            if term.parentUuid:
                self.getTerm(Term({"uuid": term.parentUuid}), "uuid").children.append(
                    term
                )
        # term already exists 406 "duplicate sibling" error, cannot rely on the
        # error message though because it varies if the term being added is a
        # parent or child term...sigh
        elif r.status_code == 406:
            return self.getTermFromDupe(term).uuid
        else:
            # actual error where we don't know what happened...we end up here if
            # taxonomy is locked by another user
            logger.error(
                'HTTP error adding term "{}" to taxonomy "{}". Error response JSON: {}'.format(
                    term, self, r.json()
                )
            )
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
            raise Exception(
                """
                Cannot add data to taxonomy term without the term's UUID.
                Term: {}
                Taxo: {}
                """.format(
                    term, self
                )
            )

        for key, value in term.data.items():
            if value:
                r = requests.put(
                    api_root
                    + "/taxonomy/{uuid}/term/{termUuid}/data/{key}/{value}".format(
                        uuid=self.uuid,
                        termUuid=term.uuid,
                        key=quote(key),
                        value=quote(value),
                    ),
                    headers=get_headers(),
                )
                r.raise_for_status()
        logger.info("added data to {} term in {} taxonomy".format(term, self))

    def clear(self):
        """
        Delete all terms in the taxonomy. We only need to delete the root
        terms, orphaned children are automatically erased.
        """
        terms = self.getRootTerms()
        for term in terms:
            self.remove(term)
        self.terms.clear()

    def getTerm(self, search_term, attr="term"):
        """
        TODO I want to get tests passing first but turns out I _hate_ this
        API. `search_term` should always be a string that gets wrapped in a
        Term object—the fact that taxo.getTerm("term string", "term")
        behaves differently from taxo.getTerm("uuid string", "uuid") is a
        disaster that made me overlook a bug for weeks.

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

    def getTermFromDupe(self, term):
        """
        If we try to add a pre-existing term we get a "duplicate sibling"
        error but still don't know the sibling's UUID. This method finds a
        term whose path we _know_ already exists but we don't know its UUID.

        args:
            term: Term object which will lack UUID (there's no point in
            using this method if you have UUID already)
        returns:
            Term object with UUID
        """
        # case 1: not a child term, so it must be top-level
        if not term.parentUuid:
            if len(self.terms) == 0:
                self.getRootTerms()
            sibling = self.getTerm(term.term, "term")
        else:
            # case 2: child term, we have to get its parents' children to find it
            # NOTE: /tax/uuid/term?path=FULL\\TERM\\PATH returns children of PATH
            parent = self.getTerm(Term({"uuid": term.parentUuid}), "uuid")
            if not parent:
                logger.error(
                    'Trying to find the parent to duplicate child "{}" in taxonomy "{}" but unable to, will not be able to add this term.'.format(
                        term, self
                    )
                )
                raise Exception("cannot find parent of duplicate child term")
            r = requests.get(
                api_root
                + "/taxonomy/{}/term?{}".format(
                    self.uuid, urlencode({"path": parent.fullTerm})
                ),
                headers=get_headers(),
            )
            r.raise_for_status()
            # r.json is a list of sibling term dicts, find the duplicate one
            sibling = next((Term(t) for t in r.json() if t["term"] == term.term), None)
            if not sibling:
                logger.error(
                    'Unable to find duplicate of "{}" among parent\'s children'.format(
                        term.term
                    )
                )
                raise Exception("cannot find identical sibling for child duplicate")

        logger.info(
            'Found duplicate sibling term "{}" with UUID "{}" in taxonomy "{}"'.format(
                sibling.term, sibling.uuid, self
            )
        )
        return sibling

    def getRootTerms(self):
        """
        Obtains a list of terms at the root of the taxonomy from openEQUELLA
        and adds them to the taxo.terms set.
        args: (none)
        returns:
            root terms (list): list of Term objects
        """
        logger.debug("Getting root-level taxonomy terms for {}".format(self))
        r = requests.get(
            api_root + "/taxonomy/{}/term".format(self.uuid), headers=get_headers()
        )
        r.raise_for_status()
        terms = [Term(t) for t in r.json()]
        for term in terms:
            self.terms.add(term)
        return terms

    def remove(self, term) -> bool:
        """
        Remove a term from a taxonomy (primarily used to remove semester
        terms from course lists).

        ! clear calls remove on all root terms and both call getRootTerms
        ! which may be causing a memory leak

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
                    logger.error(
                        'Cannot find term "{}" in taxonomy "{}" while deleting.'.format(
                            term, self
                        )
                    )
                    return False

        # Term objects don't necessarily have UUIDs
        if not term.uuid:
            logger.error(
                'Cannot delete "{}" from "{}": need to know the UUID of the term.'.format(
                    term, self
                )
            )
            return False

        logger.info('deleting "{}" term from "{}" taxonomy'.format(term, self))
        r = requests.delete(
            api_root + "/taxonomy/{}/term/{}".format(self.uuid, term.uuid),
            headers=get_headers(),
        )
        self.terms.discard(term)
        # will throw a 500 error if the taxonomy is locked by another user
        # r.json() = {'code': 500, 'error': 'Internal Server Error',
        # 'error_description': 'Taxonomy is locked by another user: {username}'}
        r.raise_for_status()
        # remove term's children (openEQUELLA API does this automatically)
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
        logger.debug(
            'Searching taxonomy "{}" for query "{}" with options "{}"'.format(
                self, query, options
            )
        )
        r = requests.get(
            api_root
            + "/taxonomy/{}/search?q={}&{}".format(
                self.uuid,
                query,
                urlencode(options),
            ),
            headers=get_headers(),
        )
        r.raise_for_status()
        results = r.json()["results"]
        return results
