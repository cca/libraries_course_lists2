from html import unescape
# https://docs.python.org/3/library/types.html#types.SimpleNamespace
# let's us construct an object from a dict
from types import SimpleNamespace

from .utilities import strip_prefix, PORTAL_STATUSES


class Course(SimpleNamespace):


    def __repr__(self):
        return "{} {} {}".format(self.semester, self.section_code, self.section_title)

    # some Workday fields have encoded entities (e.g. "&amp;") so we want to
    # unescape _all_ string attributes before returning them
    def __getattribute__(self, key):
        value = SimpleNamespace.__getattribute__(self, key)
        if type(value) == str:
            return unescape(value)
        return value


    def find_colocated_sections(self, courses):
        """ Return colocated/cross-listed sections

        Parameters
        ----------
        courses : list of courses
            Set of courses to check for colocated ones

        Returns
        -------
        list of courses
            All colocated sections.

        """
        sections = []
        if self.colocated_sections:
            for colo in self.colocated_sections:
                for course in courses:
                    if colo == course.section_def_refid:
                        sections.append(course)
                        break

        return sections

    @property
    def instructor_names(self):
        # print list of instructors as a comma-separated string of names
        if len(self.instructors) == 0:
            return '[instructors to be determined]'
        names = []
        for person in self.instructors:
            names.append('{} {}'.format(person["first_name"], person["last_name"]))
        return ', '.join(names)

    @property
    def instructor_usernames(self):
        # print list of instructor usernames as comma-separated string
        return ', '.join([i['username'] for i in self.instructors])

    @property
    def on_portal(self):
        """ boolean for whether a course is included in Portal course catalog """
        if self.hidden != "1" and self.status in PORTAL_STATUSES and self.owner != 'EXTED':
            return True
        return False

    @property
    def owner(self):
        for au in self.academic_units:
            if au["course_owner"]:
                return strip_prefix(au["refid"])

    @property
    def semester(self):
        return strip_prefix(self.term).replace('_', ' ')
