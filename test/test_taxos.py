import unittest

from lib import *


class TestTaxoData(unittest.TestCase):

    # helper function
    def verify_taxos(self, taxos):
        self.assertTrue(type(taxos) == list)
        self.assertTrue(len(taxos) > 0)
        for taxo in taxos:
            self.assertTrue(type(taxo) == Taxonomy)

    def test_get_taxos(self):
        # remove taxos file to first test get_taxos -> download taxos
        os.remove(taxos_file)
        taxos = get_taxos()
        self.verify_taxos(taxos)
        # second use: now we have the file
        taxos = get_taxos()
        self.verify_taxos(taxos)


    def test_download_taxos(self):
        taxos = download_taxos()
        self.verify_taxos(taxos)


    def test_term_and_taxo_methods(self):
        taxos = download_taxos()
        taxo = next(t for t in taxos if t.name == 'TESTS')
        # Taxonomy::getRootTerms
        taxo.getRootTerms()
        for t in taxo.terms:
            # ensure "parent" term (and its children) aren't present before we
            # test, must run this _after_ getRootTerms() or that is called twice
            if t.term == "Parent":
                taxo.remove(t)
                break
        starting_length = len(taxo.terms)
        self.assertTrue(starting_length > 0)
        # create a parent and a child term
        taxo.add("Parent")
        parent = taxo.getTerm("Parent")
        self.assertTrue(parent in taxo.terms)
        # test adding an already-existing term (should return the UUID)
        self.assertEqual(parent.uuid, taxo.add(parent))
        print(taxo.terms); print(starting_length)
        self.assertTrue(starting_length + 1 == len(taxo.terms))
        child = Term({
            "term": "Child",
            "parentUuid": parent.uuid,
            "parents": [parent],
            "data": {
                "dataNode": "hi I am a child term's data node"
            }
        })
        child.uuid = taxo.add(child)
        self.assertTrue(child in taxo.terms)
        # test adding an already-existing child term
        self.assertEqual(child.uuid, taxo.add(child))
        # @TODO this is clunky, could we possibly detect when a child node
        # is added & automatically add it to its parents list of children?
        parent.children = [child]

        # addData throws an error if you pass it a Term without a UUID
        with self.assertRaises(Exception):
            taxo.addData(Term({"term": "a", "data": {"b": "c"}}))

        # Term::fullTerm
        self.assertEqual(child.fullTerm, 'Parent\\Child')
        self.assertEqual(child.asPOSTData(), {
            "term": child.term,
            "data": child.data,
            "parentUuid": parent.uuid,
            "index": child.index,
            "readonly": child.readonly
        })

        # Taxonomy::getTerm
        self.assertEqual(child, taxo.getTerm(child))
        self.assertEqual(child, taxo.getTerm("Child"))
        self.assertEqual(parent, taxo.getTerm(parent))

        # Taxonomy::search
        no_results = taxo.search('thistermdoesnotexistheeeeyoooo')
        self.assertTrue(len(no_results) == 0)
        one_result = taxo.search('Parent')
        self.assertTrue(len(one_result) == 1)

        # Taxonomy::remove (which returns a boolean)
        self.assertFalse(taxo.remove("term that does not exist"))
        self.assertTrue(taxo.remove(parent))
        self.assertFalse(parent in taxo.terms)
        # removing a parent removes its children
        self.assertFalse(child in taxo.terms)
        self.assertTrue(starting_length == len(taxo.getRootTerms()))
        string = "test text-only remove usage"
        taxo.add(Term({"term": string}))
        self.assertTrue(taxo.remove(string))
        self.assertTrue(starting_length == len(taxo.getRootTerms()))
        self.assertFalse(taxo.remove(Term({"term": "term without UUID"})))
        self.assertTrue(starting_length == len(taxo.getRootTerms()))


if __name__ == '__main__':
    unittest.main(verbosity=2)
