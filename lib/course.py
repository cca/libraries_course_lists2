# https://docs.python.org/3/library/types.html#types.SimpleNamespace
# let's us construct an object from a dict
from types import SimpleNamespace

from .utilities import strip_prefix


class Course(SimpleNamespace):


    def find_colocated_sections(self, courses):
        # courses is a list of Course objects
        sections = []
        if self.colocated_sections:
            for colo in self.colocated_sections:
                for course in courses:
                    if colo == course.section_def_refid:
                        sections.append(course.section_code)
                        break

        return sections

    @property
    def instructor_names(self):
        # print list of instructors as a comma-separated string of names
        names = []
        for person in self.instructors:
            names.append('{} {}'.format(person["first_name"], person["last_name"]))
        return ', '.join(names)

    @property
    def instructor_usernames(self):
        # print list of instructor usernames as comma-separated string
        return ', '.join([i['username'] for i in self.instructors])

    @property
    def owner(self):
        for au in self.academic_units:
            if au["course_owner"]:
                return strip_prefix(au["refid"])

    @property
    def semester(self):
        return strip_prefix(self.term).replace('_', ' ')
