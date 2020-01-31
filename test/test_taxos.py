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


if __name__ == '__main__':
    unittest.main(verbosity=2)
