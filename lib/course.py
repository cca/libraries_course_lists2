from html import unescape

# https://docs.python.org/3/library/types.html#types.SimpleNamespace
# let's us construct an object from a dict
from types import SimpleNamespace

from .utilities import strip_prefix, PORTAL_STATUSES


class Course(SimpleNamespace):

    def __repr__(self) -> str:
        return f"{self.semester} {self.section_code} {self.section_title}"

    # some Workday fields have encoded entities (e.g. "&amp;") so we want to
    # unescape _all_ string attributes before returning them
    def __getattribute__(self, key):
        value = SimpleNamespace.__getattribute__(self, key)
        if type(value) == str:
            return unescape(value)
        return value

    # quote "Course" because it is not defined yet, causes a NameError
    def find_colocated_sections(self, courses: list["Course"]) -> list["Course"]:
        """Return colocated/cross-listed sections

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
    def instructor_names(self) -> str:
        """list of instructors as a comma-separated string of names"""
        if len(self.instructors) == 0:
            return "[instructors to be determined]"
        names = []
        for person in self.instructors:
            names.append("{} {}".format(person["first_name"], person["last_name"]))
        return ", ".join(names)

    @property
    def instructor_usernames(self) -> str:
        """list of instructor usernames as comma-separated string"""
        return ", ".join([i["username"] for i in self.instructors])

    @property
    def on_portal(self) -> bool:
        """boolean for whether a course is included in Portal course catalog"""
        if (
            self.hidden != "1"
            and self.status in PORTAL_STATUSES
            and self.owner != "EXTED"
        ):
            return True
        return False

    @property
    def owner(self) -> str:
        """Five-letter department code for course's primary department"""
        for au in self.academic_units:
            if au["course_owner"]:
                # 2 exceptions: HAAVC use "AU_VISST" & ETHST/ETHSM use "AU_DIVST"
                # both of these dept codes changed in 2020 but their corresponding
                # Workday Academic Unit codes remained the same
                if au["refid"] == "AU_VISST":
                    return "HAAVC"
                if au["refid"] == "AU_DIVST":
                    return "ETHST"
                return strip_prefix(au["refid"])

    @property
    def placeholder(self) -> bool:
        """Boolean property for whether a course is a placeholder or not.
        A placeholder course has no instructors and "placeholder" in its name."""
        if not len(self.instructors) and "placeholder" in self.section_title.lower():
            return True
        return False

    @property
    def semester(self) -> str:
        """Human-readable term like "Fall 22025"."""
        return strip_prefix(self.term).replace("_", " ")
