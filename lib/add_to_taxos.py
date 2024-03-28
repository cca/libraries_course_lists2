"""
Given a course and a list of taxonomies, create the taxonomy terms in VAULT and
for the hierarchical course list terms store the term/its UUID under the "terms"
list of the taxonomy in memory (to aid with adding further terms later). Each
course creates both program-level and syllabus collection terms for:

- overall hierarchical course list taxonomy
- course title
- course "name" e.g. course code without section digits
- course section
- faculty names

For instance, CERAM-101-01 might look like:
taxos = [
    {
        "uuid": "0dc4bdac-1215-44f1-945d-3e67ed4c36ff",
        "name": "CERAM - COURSE LIST",
        "terms": [ { "term": "Summer 2019", "uuid": "1" },
        { "term": "Intro to Ceramics", "uuid": "5" },
        ... ]
    },
    {
        "uuid": "0dc4bdac-1215-44f1-945d-3e67ed4c36ff",
        "name": "CERAM - course sections",
        "terms": [ { "term": 'CERAM-101-01', "uuid": "2" },
        { "term": 'CERAM-301-07', "uuid": "7" } ]
    },
    {
        "uuid": "0dc4bdac-1215-44f1-945d-3e67ed4c36ff",
        "name": "CERAM - course names",
        "terms": [ { "term": 'CERAM-101', "uuid": "3" } ]
    },
    (a few more of these)...
    {
        "uuid": "0dc4bdac-1215-44f1-945d-3e67ed4c36ff",
        "name": "SYLLABUS - COURSE LIST",
        "terms": [ { "term": "Summer 2019", "uuid": "1" },
        { "term": "Intro to Ceramics", "uuid": "5" },
        ... ]
    }
]

Note that we only record the "terms" list for course list taxonomies in memory,
there's not as much value in storing the terms from flat taxonomies.

We have some special logic in here for non-standard taxonomies, such as Archt
(which has one division-level set of lists for 3 programs) and Syllabus course
lists.
"""

from .course import Course
from .taxonomy import Term
from config import logger


def get_depts(course) -> set:
    """
    Determine what departments a course should be filed under in VAULT
    taxonomies.

    args:
        course (Course)
    returns:
        departments (set|None): set of department code strings e.g.
        {"SYLLABUS", "ANIMA"} or None if there are no departments
    """
    arch_div = ["ARCHT", "BARCH", "INTER", "MARCH"]
    # find out what departmental taxos a course needs to be added to
    # everything will at least be added to Syllabus Collection taxos
    depts = set(["SYLLABUS"])
    if course.owner in arch_div:
        depts.add("ARCH DIV")
    elif course.owner == "TESTS":
        # don't add test courses to syllabus collection
        return set(["TESTS"])
    elif course.owner == "CCA":
        # international exchange & other exceptions, skip them
        return set()
    elif course.owner == "FA":
        # file Interdisciplinary Critique under UDIST
        if course.subject == "CRITI":
            depts.add("UDIST")
        # ignore Fine Arts internship courses
        elif course.subject == "FNART":
            return set()
    else:
        depts.add(course.owner)
    return depts


def course_list_term(term, taxo, dept_layer=False) -> None:
    """
    Add all the terms from a course to a taxonomy. This function is recursive,
    passing a nested Term object which knows its parent/child Terms to itself
    over and over until it finishes.

    args:
        term (Term|Course): the term to be added to the taxonomy, if it's a
        Course object then it will be split into nested Term objects

        taxo (Taxonomy): course list taxonomy to add the course terms to

        dept_layer (bool): whether or not to include a term for the academic
        department e.g.
        with dept_layer: Spring 2020\\ANIMA\\Animation 1\\John Doe\\ANIMA-1000-1
        without dept_layer: Spring 2020\\Animation 1\\John Doe\\ANIMA-1000-1

    returns:
        nothing
    """
    if type(term) == Course:
        logger.debug(
            "Course {} passed as taxonomy term, breaking it into nested terms.".format(
                term
            )
        )
        # term is actually a course object
        course = term
        # we need to create the root (semester-level) taxonomy term
        term = Term({"term": course.semester})
        # We build a tree of nested Terms inside the current Term's list of
        # children. Each term outlined in the sections below (nothing has been
        # added to the Taxo yet) has a parents list equal to the course itself
        # & its children that we are creating along the way, not to be completed
        # until we reach the final one (section code). We use makeParentsList to
        # pass _values_ not a reference or every Term.parents => the whole tree.
        makeParentsList = lambda t: [t] + [c for c in t.children]

        if dept_layer:
            dept = Term(
                {
                    "term": course.owner,
                    "parents": makeParentsList(term),
                }
            )
            term.children.append(dept)

        title = Term(
            {
                "term": course.section_title,
                "parents": makeParentsList(term),
            }
        )
        term.children.append(title)

        instructors = Term(
            {
                "term": course.instructor_names,
                "parents": makeParentsList(term),
            }
        )
        term.children.append(instructors)

        # final child contains additional data nodes
        section = Term(
            {
                "data": {
                    "CrsName": course.course_code,
                    "facultyID": course.instructor_usernames,
                    # additional Workday data we may be interested in
                    "acad_level": course.acad_level,
                    "delivery_mode": course.delivery_mode,
                    "instructional_format": course.instructional_format,
                    "section_def_refid": course.section_def_refid,  # true identifier
                    "subject_name": course.subject_name,
                },
                "parents": makeParentsList(term),
                "term": course.section_code,
            }
        )
        term.children.append(section)

    term.uuid = taxo.add(term)

    # if we have child terms to add, recursively call this function
    if len(term.children) > 0:
        next_term = term.children.pop(0)
        next_term.children = term.children
        next_term.parentUuid = term.uuid
        course_list_term(next_term, taxo)


# term can be either a Course object or a string
def create_term(term, taxo_name, taxos):
    """
    Adds a Term to a Taxonomy while handling Course terms—which require
    multiple operations due to the way they are represented by a hierarchical
    chain of terms.

    args:
        term (str|Course): text of the term to be added at the root of the
        taxonomy or a Course object to be converted into a nested set of
        terms

        taxo_name (str): name of the Taxonomy to add the Term to

        taxos (list): the set of all taxonomies which we will find `taxo_name`
        in

    returns:
        essentially nothing, do not use the output of this function

        result (str|None): for a string term, returns the (also string) UUID
        of the created taxonomy term, while for a Course returns nothing due
        to the way nested terms are created (it wouldn't make much sense to
        return the final term's UUID)
    """
    # find the appropriate named taxonomy, do a check in case we don't find one
    taxo = next((t for t in taxos if t.name.lower() == taxo_name.lower()), None)
    if not taxo:
        logger.error("Unable to find {} in list of taxonomies.".format(taxo_name))
        return None

    if type(term) == str:
        if len(term) == 0 or term.isspace():
            logger.debug("No term to be added to {} taxonomy".format(taxo))
            return None
        return taxo.add(Term({"term": term}))

    # term is an object so it's a course list term
    # 2 course lists have an additional layer in hierarchy for department
    has_dept_layer = "SYLLABUS" in taxo_name or "ARCH DIV" in taxo_name
    return course_list_term(term, taxo, dept_layer=has_dept_layer)


def add_to_taxos(course, taxos, only_course_lists=False) -> None:
    """
    Create all the related taxonomy terms for a given course.

    args:
        course (Course)

        taxos (list): list of _all_ VAULT taxonomies

        only_course_lists (bool): whether to only add terms to course lists
        as opposed to all taxonomies (e.g. course sections, faculty names).
        The initial data population should be all taxonomies but repeat runs
        use `only_course_lists=True`

    returns:
        nothing
    """
    logger.debug("Processing taxonomies for course {}".format(course))
    for dept in get_depts(course):
        create_term(course, dept + " - COURSE LIST", taxos)
        if not only_course_lists:
            create_term(course.section_code, dept + " - course sections", taxos)
            create_term(course.course_refid, dept + " - course names", taxos)
            create_term(course.section_title, dept + " - course titles", taxos)
            create_term(course.instructor_names, dept + " - faculty", taxos)
