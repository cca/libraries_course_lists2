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
import json

import config
from .utilities import *


def get_depts(course):
    arch_div = ['BARCH', 'INTER', 'MARCH' ]
    # find out what departmental taxos a course needs to be added to
    # everything will at least be added to Syllabus Collection taxos
    depts = set(['SYLLABUS'])
    for au in course['academic_units']:
        # multiple Academic Units can offer a course but only one is owner
        if au["course_owner"]:
            dept = strip_prefix(au["refid"])
            if dept in arch_div:
                depts.add('ARCH DIV')
            elif dept == 'CCA':
                # international exchange, skip this course
                return None
            elif dept == 'FA':
                # file Interdisciplinary Critique under UDIST
                # ignore Fine Arts internship courses
                if course['subject'] == 'CRITI':
                    depts.add('UDIST')
                elif course['subject'] == 'FNART':
                    return None
            else:
                depts.add(dept)
    return depts


def eq_flat_term(term, taxo):
    # https://vault.cca.edu/apidocs.do#!/taxonomy/createTaxonomyTerm_post_11
    s = request_wrapper()
    # this will 406 when we try to create terms that already exist but we don't
    # care, also no need to record flat terms in memory
    s.post(config.api_root + '/taxonomy/{}/term'.format(taxo["uuid"]),
        data=json.dumps({ "term": term })
    )
    print('added {} to {}'.format(term, taxo["name"]))

# note that "term" arg can be either: a course dict, a string, or a final child
# node dict with "term" and "data" properties
def eq_course_list_term(term, taxo, parentUuid=None, children=None, dept_layer=False):
    if not parentUuid and not children:
        # no parent & no child -> term must be the initial course object
        # & we need to create the root (semester-level) taxonomy term
        course = term
        # course list taxonomies start with semester
        term = strip_prefix(course['term']).replace('_', ' ')
        children = []
        if dept_layer:
            children.append(get_course_owner(course))
        children += [
            course["section_title"],
            format_instructors(course["instructors"]),
            # final child contains additional data nodes
            # @TODO what other data do we want to store here?
            {
                "term": course["section_code"],
                "data": {
                    "CrsName": course["course_code"],
                    "facultyID": ', '.join([i['username'] for i in course["instructors"]]),
                }
            }
        ]
    # do we already have the term in the taxonomy?
    for t in taxo["terms"]:
        if t["term"] == term:
            # we will have children to create
            # final child (section code) always is unique for a given semester
            term = children.pop(0)
            return eq_course_list_term(term, taxo, parentUuid=t["uuid"], children=children)

    # construct the body to be sent to VAULT
    body = {}
    if parentUuid:
        body["parentUuid"] = parentUuid
    # final child term which may have data components
    if parentUuid and len(children) == 0:
        body["data"] = term["data"]
        term = term["term"]

    body["term"] = term
    data = json.dumps(body)

    # https://vault.cca.edu/apidocs.do#!/taxonomy/createTaxonomyTerm_post_11
    s = request_wrapper()
    r = s.post(config.api_root + '/taxonomy/{}/term'.format(taxo["uuid"]), data=data)
    r.raise_for_status()
    print('added {} to {}'.format(term, taxo["name"]))

    # EQUELLA has the UUID of the created term in the response's Location header
    # "Location": "https://vault.cca.edu/api/taxonomy/7ef.../term/bc35..."
    uuid = r.headers['Location'].split('/term/')[1]
    # record the term we created in memory
    taxo["terms"].append({ "uuid": uuid, "term": term })

    # if we have child terms to add, recursively call this function
    if len(children) > 0:
        term = children.pop(0)
        eq_course_list_term(term, taxo, parentUuid=uuid, children=children)

# term can be a course dict or string
def create_term(term, taxo_name, taxos):
    # find the appropriate named taxonomy, do a check in case we don't find one
    taxo = next((t for t in taxos if t["name"].lower() == taxo_name.lower()), None)
    if not taxo:
        print('Unable to find {} taxonomy.'.format(taxo_name))
        return

    # initialize the (in memory) terms list if it doesn't exist yet
    if not taxo.get("terms"):
        taxo["terms"] = []

    if type(term) == str:
        return eq_flat_term(term, taxo)

    # object so it's course list term
    # 2 course lists have an additional layer in hierarchy for department
    has_dept_layer = 'SYLLABUS' in taxo_name or 'ARCH DIV' in taxo_name
    return eq_course_list_term(term, taxo, dept_layer=has_dept_layer)


def add_to_taxos(course, taxos):
    for dept in get_depts(course):
        create_term(course["section_code"], dept + ' - course sections', taxos)
        create_term(course["course_refid"], dept + ' - course names', taxos)
        create_term(course["section_title"], dept + ' - course titles', taxos)
        create_term(format_instructors(course["instructors"]), dept + ' - faculty', taxos)
        create_term(course, dept + ' - COURSE LIST', taxos)
