import unittest

from lib import *


class TestStripPrefix(unittest.TestCase):

    # strip_prefix is used in two contexts right now: for department codes but
    # also for academic periods (semesters)
    def test_department(self):
        self.assertEqual(strip_prefix('AU_CERAM'), 'CERAM')


    def test_semester(self):
        self.assertEqual(strip_prefix('AP_Spring_2020'), 'Spring_2020')


class TestCourseSort(unittest.TestCase):
    courses = []

    def setUp(self):
        with open('test/courses-fixture.json', 'r') as file:
            data = json.load(file)
            self.courses = [Course(**c) for c in data]

    # strip_prefix is used in two contexts right now: for department codes but
    # also for academic periods (semesters)
    def test_course_sort(self):
        c = self.courses # just to save typing below
        sorted_courses = sorted(c, key=course_sort)
        correct_sort = [c[1], c[12], c[9], c[11], c[3], c[2], c[10], c[0], c[7], c[8], c[5], c[6], c[4],]
        self.assertEqual(correct_sort, sorted_courses)


class TestRequestWrapper(unittest.TestCase):


    def test_request_wrapper(self):
        global config
        s = request_wrapper()
        r = s.get(config.api_root + '/taxonomy')
        r.raise_for_status()
        taxos = r.json()
        self.assertTrue(taxos["length"] > 1)
        self.assertTrue(len(taxos["results"]))
        # cannot perform requests without OAuth token
        with self.assertRaises(Exception):
            del config.token
            s = request_wrapper()


if __name__ == '__main__':
    unittest.main(verbosity=2)
