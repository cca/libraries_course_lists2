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
parser.add_argument('-d', '--downloadtaxos', action='store_true', default=False, help='download fresh taxonomies from VAULT (do not use JSON list in /data dir)')
parser.add_argument('file', nargs=1, help='course list JSON file')
# @TODO --make-lists only make taxo lists

args = parser.parse_args()

with open(args.file[0], 'r') as file:
    courses = json.load(file)

# get current term from the first course we have on hand
semester = strip_prefix(courses[0]['term']).replace('_', ' ')

if args.downloadtaxos:
    taxos = download_taxos()
else:
    taxos = get_taxos()

course_lists = [t for t in taxos if 'course list' in t["name"].lower()]

for taxo in course_lists:
    clear_semester(taxo, semester)

# we're done if we were only clearing semester terms
if args.clear:
    exit(0)

for course in sorted(courses, key=course_sort):
    add_to_taxos(course, taxos)
