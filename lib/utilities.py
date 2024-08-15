import re

import config


PORTAL_STATUSES = ("Closed", "Open", "Waitlist")


def get_headers() -> dict[str, str]:
    if not config.token:
        raise Exception("I need an OAuth token in config.py to work.")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Authorization": "access_token=" + config.token,
    }
    return headers


def strip_prefix(string) -> str:
    """
    A lot of Workday names, which we are unfortunately forced to use as identifiers,
    begin with an "AX_..." prefix as in "AU_CERAM" (for the Ceramics academic unit)
    or "AP_Fall_2019" for the Fall academic period. We need these names for
    matching but don't use this prefix.
    """
    return re.sub(r"^A[A-Z]_", "", string)


def course_sort(course):
    # we sort a course object by sorting its properties in this order
    s = (
        course.owner,
        course.section_title,
        course.instructor_names,
        course.section_code,
    )
    return s
