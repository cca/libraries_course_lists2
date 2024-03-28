import filecmp
import os
import unittest

from lib import *


class TestGroupData(unittest.TestCase):
    # helper function
    def verify_groups(self, groups):
        self.assertTrue(type(groups) == list)
        self.assertTrue(len(groups) > 0)
        for group in groups:
            self.assertTrue(type(group) == Group)

    def test_get_groups(self):
        # delete groups file to test get_groups -> download
        os.remove(groups_file)
        groups = get_groups()
        self.verify_groups(groups)
        # second use case, we already have the file
        groups = get_groups()
        self.verify_groups(groups)

    def test_download_groups(self):
        groups = download_groups()
        self.verify_groups(groups)


class TestGroupClass(unittest.TestCase):
    groups = []

    def setUp(self):
        self.groups = get_groups()

    def testGroupProperties(self):
        # Group.au, Group.ldap
        # Manually test that a couple of these work out
        ANIMA = next(g for g in self.groups if g.name == "Animation Faculty")
        PRINT = next(g for g in self.groups if g.name == "Printmedia Faculty")
        self.assertEqual(ANIMA.au, "ANIMA")
        self.assertEqual(ANIMA.ldap, "fac_an")
        self.assertEqual(PRINT.au, "PRINT")
        self.assertEqual(PRINT.ldap, "fac_pm")

    def testGroupMethods(self):
        # TODO test add_users / remove_users before have_gotten_users = True
        # get_users
        testgroup = next(g for g in self.groups if g.name == "API TEST GROUP")
        self.assertFalse(testgroup._have_gotten_users)
        self.assertTrue(len(testgroup.users) == 0)
        testgroup.get_users()
        self.assertTrue(testgroup._have_gotten_users)
        self.assertTrue(len(testgroup.users) > 0)

        # add_users
        testgroup._have_gotten_users = False
        libusers = len(testgroup.users)
        teststaff = "d792560a-4155-35f7-515b-a7f662cdcddb"
        testgroup.add_users(teststaff)
        self.assertTrue(len(testgroup.users) == libusers + 1)
        self.assertTrue(teststaff in testgroup.users)
        # remove_users
        testgroup._have_gotten_users = False
        testgroup.remove_users(teststaff)
        self.assertTrue(len(testgroup.users) == libusers)
        self.assertTrue(teststaff not in testgroup.users)
        testgroup.remove_users(teststaff)  # should do nothing

        # write_ldap_file (uses a fixture)
        testgroup._have_gotten_users = False
        testfile = "test/test-group-ldap.txt"
        testgroup.write_ldap_file(testfile)
        testgroup.write_ldap_file()
        filecmp.cmp("test/api-test-group.txt", testfile)
        filecmp.cmp("test/api-test-group.txt", "data/None.txt")
        os.remove(testfile)
        os.remove("data/None.txt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
