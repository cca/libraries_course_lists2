import unittest

from lib import *


class TestAddTaxos(unittest.TestCase):
    courses = []
    taxos = []

    def setUp(self):
        # get course data
        with open("test/courses-fixture.json", "r") as file:
            data = json.load(file)
            self.courses = [Course(**c) for c in data]
        self.taxos = get_taxos()

    def tearDown(self):
        # delete everything from testing taxonomies in VAULT
        for t in [t for t in self.taxos if t.name.startswith("TESTS -")]:
            t.clear()

    def testGetDepts(self):
        # architecture division
        inter = next(c for c in self.courses if c.owner == "INTER")
        self.assertEqual(get_depts(inter), set(["ARCH DIV", "SYLLABUS"]))
        # CCA e.g. extension courses, other exceptions
        cca = next(c for c in self.courses if c.owner == "CCA")
        self.assertEqual(get_depts(cca), set())
        # Fine Arts e.g. critique, FNART courses
        criti = next(
            c for c in self.courses if c.owner == "FA" and c.subject == "CRITI"
        )
        fnart = next(
            c for c in self.courses if c.owner == "FA" and c.subject == "FNART"
        )
        self.assertEqual(get_depts(criti), set(["UDIST", "SYLLABUS"]))
        self.assertEqual(get_depts(fnart), set())

    def testCreateTerms(self):
        tests = next(t for t in self.taxos if t.name == "TESTS")
        courselist = next(t for t in self.taxos if t.name == "TESTS - COURSE LIST")

        unsuccessful = create_term("term", "taxo that doesn't exist", self.taxos)
        self.assertEqual(unsuccessful, None)
        # empty string means there's no taxo term to create
        self.assertEqual(create_term("", "TESTS", self.taxos), None)

        test_string = "term string"
        create_term(test_string, "TESTS", self.taxos)
        self.assertTrue(tests.getTerm(test_string))
        tests.remove(test_string)

        course = self.courses[0]
        create_term(course, "TESTS - COURSE LIST", self.taxos)
        # test the top-level (semester) and leaf (section code)  terms
        self.assertTrue(courselist.getTerm(course.semester))
        self.assertTrue(courselist.getTerm(course.section_code))
        # add a term (with department layer) while semester already exists
        course_list_term(course, courselist, True)
        self.assertTrue(courselist.getTerm(course.owner))

    def testAddToTaxos(self):
        courselist = next(t for t in self.taxos if t.name == "TESTS - COURSE LIST")
        courselist.getRootTerms()
        # set course owners to TESTS so we don't create terms in live taxonomies
        for c in self.courses:
            for i in range(0, len(c.academic_units)):
                c.academic_units[i]["refid"] = "AU_TESTS"

        # test the main add_to_taxos() method that adds to all taxos
        for c in sorted(self.courses, key=course_sort):
            add_to_taxos(c, self.taxos)

        # check that the top-level and leaf terms exist
        semester = self.courses[0].semester
        self.assertTrue(courselist.getTerm(semester))
        self.assertTrue(courselist.getTerm(self.courses[0].section_code))
        courselist.clear()

        for c in sorted(self.courses, key=course_sort):
            # now we test adding to only the course list taxonomy
            add_to_taxos(c, self.taxos, True)

        # test two terms from each taxonomy, the set of taoxnomies is:
        # section code, course code, course title, and instructor name
        sections = next(t for t in self.taxos if t.name == "TESTS - course sections")
        cnames = next(t for t in self.taxos if t.name == "TESTS - course names")
        ctitle = next(t for t in self.taxos if t.name == "TESTS - course titles")
        faculty = next(t for t in self.taxos if t.name == "TESTS - faculty")
        self.assertTrue(sections.getTerm(self.courses[4].section_code))
        self.assertTrue(sections.getTerm(self.courses[5].section_code))
        self.assertTrue(cnames.getTerm(self.courses[6].course_refid))
        self.assertTrue(cnames.getTerm(self.courses[7].course_refid))
        self.assertTrue(ctitle.getTerm(self.courses[8].section_title))
        self.assertTrue(ctitle.getTerm(self.courses[9].section_title))
        self.assertTrue(faculty.getTerm(self.courses[10].instructor_names))
        # courses[11] has no instructors, just pick another one
        self.assertTrue(faculty.getTerm(self.courses[7].instructor_names))


if __name__ == "__main__":
    unittest.main(verbosity=2)
