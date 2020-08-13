""" given the new (Workday Student) JSON data source, convert it into the old
(Informer report) CSV format. This is (hopefully) a one-time work-around until
this project is complete and we can cease relying on the old libraries_course_lists
project entirely.

usage: python make_informer_csv.py -c data.json -s 2020FA

where "2020FA" is the current semester

automatically names the output file "_informer.csv" per convention used in the
original libraries_course_lists project
"""
import argparse
import csv
import json
import sys
import unicodedata

from lib import Course

parser = argparse.ArgumentParser(description='Create VAULT taxonomies from JSON course data.')
parser.add_argument('-s', '--semester', required=True, help='semester code like "2020FA"')
parser.add_argument('file', help='course list JSON file')

args = parser.parse_args()


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
        args.semester,
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

with open('_informer.csv', 'w') as file:
    writer = csv.writer(file)
    header = ['semester','department','title','faculty','section','course','colocated courses','faculty usernames']
    writer.writerow(header)
    for course in courses:
        row = make_course_row(course)
        if row: writer.writerow(row)
