""" Given the new (Workday Student) JSON data source, convert it into the old
(Informer report) CSV format that the original libraries_course_lists project
utilizes.

usage: python make_informer_csv.py data.json

automatically names the output file "_informer.csv" per convention used in the
original libraries_course_lists project
"""
import argparse
import csv
import json
import unicodedata

from lib import Course

parser = argparse.ArgumentParser(description='Create VAULT taxonomies from JSON course data.')
parser.add_argument('file', help='course list JSON file')

args = parser.parse_args()


def to_term_code(semester):
    """ convert a semester phrase like "Fall 2023" to a "2023FA" term code

    Args:
        semester (str): semester string like "Fall 2023" e.g. "SEASON YEAR"

    Returns:
        str: term code like "2023FA" for use in EQUELLA taxonomy
    """
    [season, year] = semester.split(" ")

    if season == 'Fall':
        postfix = 'FA'
    elif season == 'Spring':
        postfix = 'SP'
    elif season == 'Summer':
        postfix = 'SU'

    return f"{year}{postfix}"


def asciize(s):
    # convert unicode string into ascii
    # we have to do this bc uptaxo script chokes on non-ascii chars
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()


def make_course_row(course):
    """ args: course object from Workday json
        returns: list of data properties we're interested in
    """
    # skip courses not in Portal course catalog
    if not course.on_portal:
        return None
    global courses
    dept = course.owner
    # skip the weird exceptions
    if dept in ['CCA', 'PRECO']:
        # intl exchg, skip
        return None
    elif dept == 'FA':
        if course.subject == 'CRITI':
            dept = 'CRITI'
        else:
            # FNARTs internship, skip
            return None
    row = [
        SEMESTER,
        dept,
        asciize(course.section_title),
        # cannot allow an empty instructor names field
        asciize(course.instructor_names if course.instructor_names else 'Staff'),
        course.section_code,
        course.course_code,
        ', '.join([c.section_code for c in course.find_colocated_sections(courses)]),
        asciize(course.instructor_usernames),
    ]
    return row


with open(args.file, 'r') as file:
    data = json.load(file)
    courses = [Course(**d) for d in data]

SEMESTER = to_term_code(courses[0].semester)

with open('_informer.csv', 'w') as file:
    writer = csv.writer(file)
    header = ['semester', 'department', 'title', 'faculty', 'section', 'course', 'colocated courses', 'faculty usernames']
    writer.writerow(header)
    for course in courses:
        row = make_course_row(course)
        if row:
            writer.writerow(row)
