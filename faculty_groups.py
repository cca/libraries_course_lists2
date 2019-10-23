""" given Workday Student JSON data, update EQUELLA groups to reflect who is
teaching in what programs. Right now the script only writes out a series of .txt
files named after LDAP groups; these are lists of users to be sent to the Help
Desk so they can update all the LDAP groups. I want to add functionality such
that it also updates the VAULT faculty groups for each department.

usage: python faculty_groups.py data/data.json
"""
import json
import sys

from lib import Course, map

with open(sys.argv[1], 'r') as file:
    data = json.load(file)
    courses = [Course(**d) for d in data]

# dict of dept code to list of faculty usernames e.g. "LIBRA": ["ephetteplace"]
teaching = {}
for course in courses:
    # initialize department set if it doesn't exist yet
    if teaching.get(course.owner) == None:
        teaching[course.owner] = set([i["username"] for i in course.instructors])
    else:
        teaching[course.owner].update([i["username"] for i in course.instructors])

# write LDAP text files
for dept, instructors in teaching.items():
    ldap = map[dept]["ldap"]
    if ldap is not None:
        with open('data/{}.txt'.format(ldap), 'a') as file:
            file.write('\n'.join(list(instructors)))
