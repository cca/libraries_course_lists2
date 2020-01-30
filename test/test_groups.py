import unittest

from lib import *


class TestGroupData(unittest.TestCase):


    def test_get_groups(self):
        groups = get_groups()
        self.assertTrue(type(groups) == list)
        self.assertTrue(len(groups) > 0)
        for group in groups:
            self.assertTrue(type(group) == Group)


    def test_download_groups(self):
        groups = download_groups()
        self.assertTrue(type(groups) == list)
        self.assertTrue(len(groups) > 0)
        for group in groups:
            self.assertTrue(type(group) == Group)


if __name__ == '__main__':
    unittest.main(verbosity=2)
