import unittest
import warnings

from lib import *


class TestTaxoData(unittest.TestCase):

    def setUp(self):
        # make "unclosed socket" warnings stop, see this for instance
        # https://github.com/boto/boto3/issues/454
        warnings.filterwarnings(
            "ignore", category=ResourceWarning, message="unclosed.*<socket.socket.*>"
        )

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
        taxos = get_taxos()
        taxo = next(t for t in taxos if t.name == "TESTS")
        # Taxonomy::getRootTerms
        taxo.getRootTerms()
        # Ensure "Parent" term does not already exist
        try:
            print(
                'NOTE; we are removing a term that _should not_ exist so it is OK if you see a "Cannot find term...while deleting" error'
            )
            taxo.remove("Parent")
        except:
            pass

        starting_length = len(taxo.terms)
        self.assertTrue(starting_length > 0)
        # running getRootTerms multiple times doesn't double the terms set
        taxo.getRootTerms()
        self.assertEqual(starting_length, len(taxo.terms))

        # create a parent and a child term
        taxo.add("Parent")
        self.assertTrue(starting_length + 1 == len(taxo.terms))
        parent = taxo.getTerm("Parent")
        self.assertTrue(parent in taxo.terms)
        # test adding an already-existing term we know about
        self.assertEqual(parent.uuid, taxo.add(parent))
        child = Term(
            {
                "term": "Child",
                "parentUuid": parent.uuid,
                "parents": [parent],
                "data": {"dataNode": "hi I am a child term's data node"},
            }
        )
        child.uuid = taxo.add(child)
        self.assertTrue(child in taxo.terms)
        # test adding an already-existing child term
        self.assertEqual(child.uuid, taxo.add(child))

        # Term::__eq__
        # non-Term objects are always false, these fail cuz they're strings
        self.assertTrue(parent != "Parent")
        self.assertTrue(parent != parent.uuid)
        self.assertEqual(parent, Term({"uuid": parent.uuid, "term": "Parent"}))
        self.assertEqual(parent, Term({"uuid": None, "term": "Parent"}))
        self.assertTrue(parent != child)
        self.assertTrue(parent != Term({"uuid": None, "term": "Not the same term"}))

        # addData throws an error if you pass it a Term without a UUID
        with self.assertRaises(Exception):
            taxo.addData(Term({"term": "a", "data": {"b": "c"}}))

        # Term::fullTerm
        self.assertEqual(child.fullTerm, "Parent\\Child")
        self.assertEqual(
            child.asPOSTData(),
            {
                "term": child.term,
                "data": child.data,
                "parentUuid": parent.uuid,
                "index": child.index,
                "readonly": child.readonly,
            },
        )

        # Taxonomy::getTerm
        self.assertEqual(child, taxo.getTerm(child))
        self.assertEqual(child, taxo.getTerm("Child"))
        self.assertEqual(parent, taxo.getTerm(parent))

        # Taxonomy::search
        no_results = taxo.search("thistermdoesnotexistheeeeyoooo")
        self.assertTrue(len(no_results) == 0)
        one_result = taxo.search("Parent")
        self.assertTrue(len(one_result) == 1)

        # Taxonomy::remove (which returns a boolean)
        self.assertFalse(taxo.remove("term that does not exist"))
        self.assertTrue(taxo.remove(parent))
        self.assertFalse(parent in taxo.terms)
        # removing a parent removes its children
        self.assertFalse(child in taxo.terms)
        self.assertEqual(starting_length, len(taxo.getRootTerms()))
        string = "test text-only remove usage"
        taxo.add(Term({"term": string}))
        self.assertTrue(taxo.remove(string))
        self.assertEqual(starting_length, len(taxo.getRootTerms()))
        print(
            'NOTE: we are expecting taxo.remove() to fail to remove a term without a UUID, so we _expect_ to see a "Cannot find term...while deleting" error'
        )
        self.assertFalse(taxo.remove(Term({"term": "term without UUID"})))
        self.assertEqual(starting_length, len(taxo.getRootTerms()))

        # Taxonomy::getTermFromDupe
        parentDupe = Term({"term": "parent dupe"})
        parentDupe.uuid = taxo.add(parentDupe)
        taxo.terms.clear()  # this helps test 1 line of getTermFromDupe()
        self.assertEqual(parentDupe, taxo.getTermFromDupe(parentDupe))
        childDupe = Term({"term": "child of dupe", "parentUuid": parentDupe.uuid})
        childDupe.uuid = taxo.add(childDupe)
        taxo.terms.clear()  # need to do this or child is obtained from taxo.terms
        taxo.getRootTerms()
        self.assertEqual(
            childDupe.uuid,
            taxo.add(Term({"term": "child of dupe", "parentUuid": parentDupe.uuid})),
        )
        taxo.remove(parentDupe)


if __name__ == "__main__":
    unittest.main(verbosity=2)
