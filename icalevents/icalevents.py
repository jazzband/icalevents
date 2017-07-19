from .icalparser import parse_events
from .icaldownload import ICalDownload


def events(url=None, file=None, start=None, end=None, fix_apple=False):
    """
    Get all events form the given iCal URL occurring in the given time range.

    :param url: iCal URL
    :param start: start date (see dateutils.date)
    :param end: end date (see dateutils.date)
    :param fix_apple: fix known Apple iCal issues
    :return: events as list of dictionaries
    """
    found_events = []

    content = None

    if url:
        content = ICalDownload().data_from_url(url, apple_fix=fix_apple)

    if not content and file:
        content = ICalDownload().data_from_file(file, apple_fix=fix_apple)

    if start and end:
        found_events += parse_events(content, start=start, end=end)
    elif start:
        found_events += parse_events(content, start=start)
    else:
        found_events += parse_events(content)

    return found_events
