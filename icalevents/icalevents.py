from threading import Lock, Thread

from .icalparser import parse_events, Event
from .icaldownload import ICalDownload


# Lock for event data
event_lock = Lock()
# Event data
event_store = {}
# Threads
threads = {}


def events(
    url=None,
    file=None,
    string_content=None,
    start=None,
    end=None,
    fix_apple=False,
    http=None,
    sort=True,
) -> list[Event]:
    """
    Get all events form the given iCal URL occurring in the given time range.

    :param url: iCal URL
    :param file: iCal file path
    :param string_content: iCal content as string
    :param start: start date (see dateutils.date)
    :param end: end date (see dateutils.date)
    :param fix_apple: fix known Apple iCal issues
    :sort: sorts events by start time

    :return: events
    """
    found_events = []

    content = None
    ical_download = ICalDownload(http=http)

    if url:
        content = ical_download.data_from_url(url, apple_fix=fix_apple)

    if not content and file:
        content = ical_download.data_from_file(file, apple_fix=fix_apple)

    if not content and string_content:
        content = ical_download.data_from_string(string_content, apple_fix=fix_apple)

    found_events += parse_events(content, start=start, end=end)

    if found_events is not None and sort is True:
        found_events.sort()

    return found_events


def request_data(key, url, file, string_content, start, end, fix_apple):
    """
    Request data, update local data cache and remove this Thread from queue.

    :param key: key for data source to get result later
    :param url: iCal URL
    :param file: iCal file path
    :param string_content: iCal content as string
    :param start: start date
    :param end: end date
    :param fix_apple: fix known Apple iCal issues
    """
    data = []

    try:
        data += events(
            url=url,
            file=file,
            string_content=string_content,
            start=start,
            end=end,
            fix_apple=fix_apple,
        )
    finally:
        update_events(key, data)
        request_finished(key)


def events_async(
    key, url=None, file=None, start=None, string_content=None, end=None, fix_apple=False
):
    """
    Trigger an asynchronous data request.

    :param key: key for data source to get result later
    :param url: iCal URL
    :param file: iCal file path
    :param string_content: iCal content as string
    :param start: start date
    :param end: end date
    :param fix_apple: fix known Apple iCal issues
    """
    t = Thread(
        target=request_data,
        args=(key, url, file, string_content, start, end, fix_apple),
    )

    with event_lock:
        if key not in threads:
            threads[key] = []

        threads[key].append(t)

        if not threads[key][0].is_alive():
            threads[key][0].start()


def request_finished(key):
    """
    Remove finished Thread from queue.

    :param key: data source key
    """
    with event_lock:
        threads[key] = threads[key][1:]

        if threads[key]:
            threads[key][0].run()


def update_events(key, data):
    """
    Set the latest events for a key.

    :param key: key to set
    :param data: events for key
    """
    with event_lock:
        event_store[key] = data


def latest_events(key):
    """
    Get the latest downloaded events for the given key.

    :return: events for key
    """
    with event_lock:
        # copy data
        res = event_store[key][:]

    return res


def all_done(key):
    """
    Check if requests for the given key are active.

    :param key: key for requests
    :return: True if requests are pending or active
    """
    with event_lock:
        if threads[key]:
            return False
        return True
