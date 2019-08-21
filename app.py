# iterate over courses
# each needs to be filed into
# 1) overall syllabus list
# 2) departmental list
# then we compile special cases (Arch Division, interdisciplinary, critical studies?, engage?)
# into larger departmental lists
# create the necessary sub-lists for each list
# (course list, course names, course sections, course titles, faculty names)
# add to VAULT taxonomies using REST API
import argparse
import json
import logging # @TODO
import sys

from lib import *

parser = argparse.ArgumentParser(description='Create VAULT taxonomies from JSON course data.')
parser.add_argument('-c', '--clear', action='store_true', default=False, help='only clear the given semester taxonomy term, do not create new terms')
parser.add_argument('-d', '--downloadtaxos', action='store_true', default=False, help='download taxonomies from VAULT (do not use JSON list in /data dir)')
parser.add_argument('file', nargs=1, help='course list JSON file')
# @TODO --make-lists only make taxo lists

args = parser.parse_args()

with open(args.file[0], 'r') as file:
    courses = json.load(file)

# get current term from the first course we have on hand
semester = strip_prefix(courses[0]['term'])

if args.clear:
    for taxo in get_taxos():
        # we only need to clear semesters from course lists, should filter somehow
        clear_semester(taxo, semester)
    exit(0)

if args.downloadtaxos:
    taxos = download_taxos()
else:
    taxos = get_taxos()

for course in courses:
    taxos = add_to_taxos(course, taxos)

for taxo in taxos:
    # we only need to clear semesters from course lists, should filter somehow
    clear_semester(taxo, semester)
    update_taxo(taxo)
