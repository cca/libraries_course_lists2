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
        "name": "CERM - COURSE LIST",
        "terms": [ { "term": "Summer 2019", "uuid": "1" },
        { "term": "Intro to Ceramics", "uuid": "5" },
        ... ]
    },
    {
        "uuid": "0dc4bdac-1215-44f1-945d-3e67ed4c36ff",
        "name": "CERM - course sections",
        "terms": [ { "term": 'CERAM-101-01', "uuid": "2" },
        { "term": 'CERAM-301-07', "uuid": "7" } ]
    },
    {
        "uuid": "0dc4bdac-1215-44f1-945d-3e67ed4c36ff",
        "name": "CERM - course names",
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


def get_depts(course):
    arch_div = ['BARCH', 'INTER', 'MARCH' ]
    # find out what departmental taxos a course needs to be added to
    # everything will at least be added to Syllabus Collection taxos
    # depts = set(['SYLLABUS'])
    depts = set()
    if course.owner in arch_div:
        depts.add('ARCH DIV')
    elif course.owner  == 'CCA':
        # international exchange, skip this course
        return None
    elif course.owner  == 'FA':
        # file Interdisciplinary Critique under UDIST
        if course.subject == 'CRITI':
            depts.add('UDIST')
        # ignore Fine Arts internship courses
        elif course.subject == 'FNART':
            return None
    else:
        depts.add(course.owner)
    return depts


def course_list_term(term, taxo, dept_layer=False):
    if type(term) == Course:
        # term is actually a course object
        course = term
        # we need to create the root (semester-level) taxonomy term
        term = Term({ "term": course.semester })
        parents = [term]

        if dept_layer:
            dept = Term({
                "term": course.owner,
                "parents": [p.term for p in parents],
            })
            term.children.append(dept)
            parents.append(dept)

        title = Term({
            "term": course.section_title,
            "parents": [p.term for p in parents],
        })
        term.children.append(title)
        parents.append(title)

        instructors = Term({
            "term": course.instructor_names,
            "parents": [p.term for p in parents],
        })
        term.children.append(instructors)
        parents.append(instructors)

        # final child contains additional data nodes
        # @TODO is there other data we want to store here? also this doesn't work
        section = Term({
            "data": {
                "CrsName": course.course_code,
                "facultyID": course.instructor_usernames,
            },
            "parents": [p.term for p in parents],
            "term": course.section_code,
        })
        term.children.append(section)

    uuid = taxo.add(term)

    # if we have child terms to add, recursively call this function
    if len(term.children) > 0:
        next_term = term.children.pop(0)
        next_term.children = term.children
        next_term.parentUuid = uuid
        course_list_term(next_term, taxo)

# term can be either a Course object or a string
def create_term(term, taxo_name, taxos):
    # find the appropriate named taxonomy, do a check in case we don't find one
    taxo = next((t for t in taxos if t.name.lower() == taxo_name.lower()), None)
    if not taxo:
        print('Unable to find {} taxonomy.'.format(taxo_name))
        return

    if type(term) == str:
        return taxo.add(Term({ "term": term }))

    # term is an object so it's a course list term
    # 2 course lists have an additional layer in hierarchy for department
    has_dept_layer = 'SYLLABUS' in taxo_name or 'ARCH DIV' in taxo_name
    return course_list_term(term, taxo, dept_layer=has_dept_layer)


def add_to_taxos(course, taxos, only_course_lists=False):
    for dept in get_depts(course):
        create_term(course, dept + ' - COURSE LIST', taxos)
        if not only_course_lists:
            create_term(course.section_code, dept + ' - course sections', taxos)
            create_term(course.course_refid, dept + ' - course names', taxos)
            create_term(course.section_title, dept + ' - course titles', taxos)
            create_term(course.instructor_names, dept + ' - faculty', taxos)
