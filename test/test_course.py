import unittest

from lib import *


class TestCourseClass(unittest.TestCase):
    courses = []

    def setUp(self):
        with open('test/courses-fixture.json', 'r') as file:
            data = json.load(file)
            self.courses = [Course(**c) for c in data]


    def test_computed_properties(self):
        # test a course with one instructor and with two
        one_instructor = self.courses[0]
        two_instructors = self.courses[4]
        # instructor methods
        self.assertEqual(one_instructor.instructor_names, 'Donald Fortescue')
        self.assertEqual(one_instructor.instructor_usernames, 'dfortescue')
        self.assertEqual(two_instructors.instructor_names, 'Megan Werner, Elin Christopherson')
        self.assertEqual(two_instructors.instructor_usernames, 'mwerner, echristopherson')
        # test on_portal - one_instructor course is status: Preliminary
        self.assertFalse(one_instructor.on_portal)
        self.assertFalse(next(c for c in self.courses if c.hidden == '1').on_portal)
        self.assertFalse(self.courses[11].on_portal) # EXTED course
        # test a first year course rather than another UDIST one
        self.assertEqual(self.courses[-1].owner, 'CORES')
        self.assertEqual(two_instructors.owner, 'UDIST')
        self.assertEqual(one_instructor.semester, 'Spring 2020')
        self.assertEqual(two_instructors.semester, 'Spring 2020')
        # kinda dumb but this helps with coverage
        self.assertEqual(str(one_instructor), 'Spring 2020 UDIST-3000-3')


    def test_colocated_sections(self):
        one = next(c for c in self.courses if c.section_def_refid == "DEF_INDUS-2320-2_2020SP")
        two = next(c for c in self.courses if c.section_def_refid == "DEF_GLASS-2320-2_2020SP")
        self.assertEqual(type(one.find_colocated_sections(self.courses)), list)
        self.assertEqual(one.find_colocated_sections(self.courses), [two])
        self.assertEqual(two.find_colocated_sections(self.courses), [one])


if __name__ == '__main__':
    unittest.main(verbosity=2)
