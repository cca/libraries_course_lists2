""" Given the new (Workday Student) JSON data source, convert it into the old
(Informer report) CSV format that the original libraries_course_lists project
utilizes.

usage: python make_informer_csv.py

automatically names the output file "_informer.csv" per convention used in the
original libraries_course_lists project
"""

import argparse
import csv
from datetime import date, datetime
import json
import re
import subprocess
import unicodedata

from lib import Course

today: date = datetime.now().date()


def what_term_is_it(date: date = today) -> str:
    """determine current term (e.g. "Fall 2023", "Spring 2023") from the date"""
    year: int = date.year

    if date.month >= 8:
        season = "Fall"
    elif date.month >= 5:
        season = "Summer"
    else:
        season = "Spring"

    return f"{season}_{year}"


def download_courses_file(term: str) -> str:
    # call out to `gsutil` to download the courses file from Google Storage
    # using the google-cloud-storage library stopped working, some kind of auth problem
    uri: str = f"gs://int_files_source/course_section_data_AP_{term}.json"
    path: str = f"data/{today}_{term}.json"
    cmd: str = f"gsutil cp {uri} {path}"
    subprocess.call(cmd, shell=True)
    return path


def to_term_code(semester: str) -> str:
    """convert a semester phrase like "Fall 2023" to a "2023FA" term code

    Args:
        semester (str): semester string like "Fall 2023" e.g. "SEASON YEAR"

    Returns:
        str: term code like "2023FA" for use in EQUELLA taxonomy
    """
    [season, year] = semester.split(" ")

    if season == "Summer":
        postfix = "SU"
    elif season == "Spring":
        postfix = "SP"
    else:  # default to Fall
        postfix = "FA"

    return f"{year}{postfix}"


def asciize(s: str) -> str:
    # convert unicode string into ascii
    # we have to do this bc uptaxo script chokes on non-ascii chars
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def make_course_row(course: Course, courses: list[Course]) -> list[str] | None:
    """args: course object from Workday json
    returns: list of data properties we're interested in
    """
    # skip ones not in Portal course catalog & placeholders
    if not course.on_portal or course.placeholder:
        return None

    dept: str | None = course.owner
    # skip the weird exceptions
    if not dept or dept in ["CCA", "PRECO"]:
        # intl exchg, skip
        return None
    elif dept == "FA":
        if course.subject == "CRITI":
            dept = "CRITI"
        else:
            # FNARTs internship, skip
            return None
    row: list[str] = [
        to_term_code(course.semester),
        dept,
        asciize(course.section_title),
        # cannot allow an empty instructor names field
        asciize(course.instructor_names if course.instructor_names else "Staff"),
        course.section_code,
        course.course_code,
        ", ".join([c.section_code for c in course.find_colocated_sections(courses)]),
        asciize(course.instructor_usernames),
    ]
    return row


# dealing with three different forms of semester strings
# 1. "Fall 2023" (Workday JSON)
# 2. "2023FA" (EQUELLA taxonomy)
# 3. "FA_2023" (Google Storage file name)
def main(file: str | None = None, term: str | None = None) -> None:
    if not file:
        file = download_courses_file(term or what_term_is_it())

    with open(file, "r") as fh:
        data = json.load(fh)
        courses: list[Course] = [Course(**d) for d in data]

    print("Writing Informer CSV file to _informer.csv")
    with open("_informer.csv", "w") as outfile:
        writer = csv.writer(outfile)
        header: list[str] = [
            "semester",
            "department",
            "title",
            "faculty",
            "section",
            "course",
            "colocated courses",
            "faculty usernames",
        ]
        writer.writerow(header)
        for course in courses:
            row: list[str] | None = make_course_row(course, courses)
            if row:
                writer.writerow(row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create Informer-like CSV from Workday JSON. This script automatically downloads the JSON courses file for the current semester from Google Storage or you can specify a term or file to create a CSV for a semester other than the current one."
    )
    parser.add_argument("-f", "--file", help="path to JSON courses file")
    parser.add_argument("-t", "--term", help="term code like 'Fall_2023'")
    args = parser.parse_args()
    if args.term and not re.match(r"(Spring|Summer|Fall)_\d{4}", args.term):
        raise ValueError(
            f"Cannot understand '{args.term}', the --term must be in the form of 'Fall_2023' e.g. a valid season, an underscore, and a 4-digit year"
        )
    main(args.file, args.term)
