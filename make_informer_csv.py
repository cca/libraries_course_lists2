""" Given the new (Workday Student) JSON data source, convert it into the old
(Informer report) CSV format that the original libraries_course_lists project
utilizes.

usage: python make_informer_csv.py

automatically names the output file "_informer.csv" per convention used in the
original libraries_course_lists project
"""
import csv
from datetime import datetime
import json
import unicodedata

from google.cloud import storage

from lib import Course

today = datetime.now().date()


def what_term_is_it(date=today):
    """ determine current term (e.g. "Fall 2023", "Spring 2023") from the date
    """
    season = None
    year = date.year

    if date.month >= 8:
        season = 'Fall'
    elif date.month >= 5:
        season = 'Summer'
    else:
        season = 'Spring'

    return f"{season}_{year}"


def download_courses_file(term):
    client = storage.Client()
    file_name = f'course_section_data_AP_{term}.json'
    print(f'Downloading {file_name} course data from Google Storage.')
    bucket = client.get_bucket('int_files_source')
    blob = bucket.blob(file_name)
    local_file = f'data/{today.isoformat()}-{term}.json'
    blob.download_to_filename(local_file)
    return local_file


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

# dealing with three different forms of semester strings
# 1. "Fall 2023" (Workday JSON)
# 2. "2023FA" (EQUELLA taxonomy)
# 3. "FA_2023" (Google Storage file name)
file = download_courses_file(what_term_is_it())
with open(file, 'r') as fh:
    data = json.load(fh)
    courses = [Course(**d) for d in data]

SEMESTER = to_term_code(courses[0].semester)

print('Writing Informer CSV file to _informaer.csv')
with open('_informer.csv', 'w') as file:
    writer = csv.writer(file)
    header = ['semester', 'department', 'title', 'faculty', 'section', 'course', 'colocated courses', 'faculty usernames']
    writer.writerow(header)
    for course in courses:
        row = make_course_row(course)
        if row:
            writer.writerow(row)
