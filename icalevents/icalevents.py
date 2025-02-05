from __future__ import annotations

from datetime import datetime, tzinfo as _tzinfo
from pathlib import Path
from threading import Lock, Thread

import urllib3

from .icalparser import Event, parse_events
from .icaldownload import ICalDownload


# Lock for event data
event_lock = Lock()
# Event data
event_store: dict[str, list[Event]] = {}
# Threads
threads: dict[str, list[Thread]] = {}


def events(
    url: str | None = None,
    file: str | Path | None = None,
    string_content: bytes | str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    fix_apple: bool = False,
    http: urllib3.PoolManager | None = None,
    tzinfo: _tzinfo | None = None,
    sort: bool = False,
    strict: bool = False,
) -> list[Event]:
    """
    Get all events form the given iCal URL occurring in the given time range.

    :param url: iCal URL
    :param file: iCal file path
    :param string_content: iCal content as string
    :param start: start date (see datetime.date)
    :param end: end date (see datetime.date)
    :param fix_apple: fix known Apple iCal issues
    :param tzinfo: return values in specified tz
    :param sort: sort return values
    :param strict: return dates, datetimes and datetime with timezones as specified in ical
    :sort sorts events by start time

    :return events
    """
    found_events = []

    content = ""
    ical_download = ICalDownload(http=http)

    if url:
        content = ical_download.data_from_url(url, apple_fix=fix_apple)

    if not content and file:
        content = ical_download.data_from_file(file, apple_fix=fix_apple)

    if not content and string_content:
        content = ical_download.data_from_string(string_content, apple_fix=fix_apple)

    found_events += parse_events(
        content, start=start, end=end, tzinfo=tzinfo, sort=sort, strict=strict
    )

    if sort:
        found_events.sort()

    return found_events


def request_data(
    key: str,
    url: str | None,
    file: str | Path | None,
    string_content: bytes | str | None,
    start: datetime | None,
    end: datetime | None,
    fix_apple: bool,
) -> None:
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
    key: str,
    url: str | None = None,
    file: str | Path | None = None,
    start: datetime | None = None,
    string_content: bytes | str | None = None,
    end: datetime | None = None,
    fix_apple: bool = False,
) -> None:
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


def request_finished(key: str) -> None:
    """
    Remove finished Thread from queue.

    :param key: data source key
    """
    with event_lock:
        threads[key] = threads[key][1:]

        if threads[key]:
            threads[key][0].run()


def update_events(key: str, data: list[Event]) -> None:
    """
    Set the latest events for a key.

    :param key: key to set
    :param data: events for key
    """
    with event_lock:
        event_store[key] = data


def latest_events(key: str) -> list[Event]:
    """
    Get the latest downloaded events for the given key.

    :return: events for key
    """
    with event_lock:
        # copy data
        res = event_store[key][:]

    return res


def all_done(key: str) -> bool:
    """
    Check if requests for the given key are active.

    :param key: key for requests
    :return: True if requests are pending or active
    """
    with event_lock:
        if threads[key]:
            return False
        return True
