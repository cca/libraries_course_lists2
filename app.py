# get full list of taxonomies from file or VAULT
# sort courses from JSON file into all the taxos they'll need to be in
# clear our current semester terms from course list taxonomies
# add new terms to the taxonomies
import argparse
import json
import logging # @TODO
import sys

from lib import *

parser = argparse.ArgumentParser(description='Create VAULT taxonomies from JSON course data.')
parser.add_argument('-c', '--clear', action='store_true', default=False, help='only clear the given semester taxonomy term, do not create new terms')
parser.add_argument('--course-lists', action='store_true', default=False, help='only create terms in course list taxonomies, ignore others')
parser.add_argument('-d', '--downloadtaxos', action='store_true', default=False, help='download fresh taxonomies from VAULT (do not use JSON list in /data dir)')
parser.add_argument('file', nargs=1, help='course list JSON file')

args = parser.parse_args()

with open(args.file[0], 'r') as file:
    data = json.load(file)
    courses = [Course(**c) for c in data]

if args.downloadtaxos:
    taxos = download_taxos()
else:
    taxos = get_taxos()

course_lists = [t for t in taxos if 'course list' in t.name.lower()]
# semester is the same for all courses so we just grab it from first one
current_semester = courses[0].semester

for taxo in course_lists:
    taxo.remove(current_semester)

# we're done if we were only clearing semester terms from course lists
if args.clear:
    exit(0)

# filter out preliminary and hidden courses
courses = [c for c in courses if c.hidden == '0' and c.status != 'Preliminary']
for course in sorted(courses, key=course_sort):
    add_to_taxos(course, taxos, args.course_lists)
