"""
Given JSON data file _without_ the "academic_units" list property on each course
add a fake AU list using the five five letters of the section code. This helps
me test with data that looks real. Usage:

> python add_au_list.py input.json > output.json

NOTE: it's fake! 1st 5 letters != department code.
"""
import json
import sys

with open(sys.argv[1], 'r') as file:
    data = json.load(file)
    for course in data:
        # it's a list of dicts
        course["academic_units"] = [{
            "refid": "AU_" + course["section_code"][:5],
            "name": "...", # too much work to figure out/create names
            "offering_percent": 100,
        }]

print(json.dumps(data))
