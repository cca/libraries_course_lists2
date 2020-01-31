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


class TestGroupClass(unittest.TestCase):
    groups = []


    def setUp(self):
        self.groups = get_groups()


    def testGroupProperties(self):
        # Group.au, Group.ldap
        # Manually test that a couple of these work out
        ANIMA = next(g for g in self.groups if g.name == 'Animation Faculty')
        PRINT = next(g for g in self.groups if g.name == 'Printmedia Faculty')
        self.assertEqual(ANIMA.au, 'ANIMA')
        self.assertEqual(ANIMA.ldap, 'fac_an')
        self.assertEqual(PRINT.au, 'PRINT')
        self.assertEqual(PRINT.ldap, 'fac_pm')


    def testGroupMethods(self):
        # get_users
        testgroup = next(g for g in self.groups if g.name == 'API TEST GROUP')
        self.assertFalse(testgroup.have_gotten_users)
        self.assertTrue(len(testgroup.users) == 0)
        testgroup.get_users()
        self.assertTrue(testgroup.have_gotten_users)
        self.assertTrue(len(testgroup.users) > 0)

        # add_users
        libusers = len(testgroup.users)
        teststaff = 'd792560a-4155-35f7-515b-a7f662cdcddb'
        testgroup.add_users(teststaff)
        self.assertTrue(len(testgroup.users) == libusers + 1)
        self.assertTrue(teststaff in testgroup.users)
        # remove_users
        testgroup.remove_users(teststaff)
        self.assertTrue(len(testgroup.users) == libusers)
        self.assertTrue(teststaff not in testgroup.users)

        # write_ldap_file (use a fixture)


if __name__ == '__main__':
    unittest.main(verbosity=2)
