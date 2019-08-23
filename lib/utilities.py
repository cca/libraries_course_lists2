import re

import requests

import config


def request_wrapper():
    if not config.token:
        raise Exception('I need an OAuth token in config.py to work.')

    s = requests.Session()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Authorization': 'access_token=' + config.token,
    }
    s.headers.update(headers)
    return s


def format_instructors(instructors):
    # take list of faculty objects & convert into comma-separated string of names
    names = []
    for person in instructors:
        names.append('{} {}'.format(person["first_name"], person["last_name"]))
    return ', '.join(names)


def strip_prefix(string):
    """
    A lot of Workday names, which we are unfortunately forced to use as identifiers,
    being with a "AX_..." prefix as in "AU_CERAM" (for the Ceramics academic unit)
    or "AP_Fall_2019" for the Fall academic period. We need these names for
    matching but don't use this prefix.
    """
    return re.sub(r'^A[A-Z]_', '', string)


def get_course_owner(course):
    for au in course["academic_units"]:
        if au["course_owner"]:
            return strip_prefix(au["refid"])


def course_sort(course):
    # we sort a course object by sorting its properties in this order:
    # department, title, instructors, section
    s = (
        get_course_owner(course),
        course["section_title"],
        format_instructors(course["instructors"]),
        course["section_code"],
    )
    return s
