import unittest

from lib import *


class TestAddTaxos(unittest.TestCase):
    courses = []
    taxos = []


    def setUp(self):
        # get course data & set all academic units to TESTS
        with open('test/courses-fixture.json', 'r') as file:
            data = json.load(file)
            self.courses = [Course(**c) for c in data]
        self.taxos = get_taxos()


    def testGetDepts(self):
        # architecture division
        inter = next(c for c in self.courses if c.owner == 'INTER')
        self.assertEqual(get_depts(inter), set(['ARCH DIV']))
        # CCA e.g. extension courses, other exceptions
        cca = next(c for c in self.courses if c.owner == 'CCA')
        self.assertEqual(get_depts(cca), None)
        # Fine Arts e.g. critique, FNART courses
        criti = next(c for c in self.courses if c.owner == 'FA' and c.subject == 'CRITI')
        fnart = next(c for c in self.courses if c.owner == 'FA' and c.subject == 'FNART')
        self.assertEqual(get_depts(criti), set(['UDIST']))
        self.assertEqual(get_depts(fnart), None)


    def testCreateTerm(self):
        tests = next(t for t in self.taxos if t.name == 'TESTS')
        courselist = next(t for t in self.taxos if t.name == 'TESTS - course list')
        unsuccessful = create_term("term", "taxo that doesn't exist", self.taxos)
        self.assertEqual(unsuccessful, None)
        create_term("term string", 'TESTS', self.taxos)
        self.assertTrue(tests.getTerm(Term({"term": "term string"})))

        # tests course_list_term which is called by create_term(course,...)
        semester = self.courses[0].semester
        create_term(self.courses[0], 'TESTS - course list', self.taxos)
        self.assertTrue(courselist.getTerm(Term({"term": semester})))
        # try to add a term (without dept layer) while semester already exists
        course_list_term(self.courses[0], courselist, False)
        # @TODO check that the child terms also exist

        # delete the terms we just created
        tests.remove("term string")
        courselist.remove(semester)


    def testAddToTaxos(self):
        pass
