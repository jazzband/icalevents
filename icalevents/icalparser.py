"""
Parse iCal data to Events.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, tzinfo as _tzinfo
from importlib.metadata import version
from random import randint
from typing import cast
from uuid import uuid4

from dateutil.rrule import rruleset, rrulestr
from dateutil.tz import UTC, gettz
from icalendar import Calendar, Timezone
from icalendar.prop import vDDDLists, vText
from icalendar.timezone.windows_to_olson import WINDOWS_TO_OLSON
from pytz import timezone

if version("icalendar") >= "6.0":
    from icalendar import Component, use_pytz
    from icalendar.timezone.windows_to_olson import WINDOWS_TO_OLSON

    use_pytz()
else:
    from icalendar.cal import Component
    from icalendar.windows_to_olson import WINDOWS_TO_OLSON


def now() -> datetime:
    """
    Get current time.

    :return: now as datetime with timezone
    """
    return datetime.now(UTC)


class Attendee(str):
    def __init__(self, address: str) -> None:
        self.address = address

    def __repr__(self) -> str:
        return self.address.encode("utf-8").decode("ascii")

    @property
    def params(self):
        return self.address.params


class Event:
    """
    Represents one event (occurrence in case of reoccurring events).
    """

    def __init__(self) -> None:
        """
        Create a new event occurrence.
        """
        self.uid: str = "-1"
        self.summary: str | None = None
        self.description: str | None = None
        self.start: datetime
        self.end: datetime
        self.all_day: bool = True
        self.transparent: bool = False
        self.recurring: bool = False
        self.location: str | None = None
        self.private: bool = False
        self.created: datetime | None = None
        self.last_modified: datetime | None = None
        self.sequence: str | None = None
        self.recurrence_id: datetime | date | None = None
        self.attendee: Attendee | list[Attendee] | str = ""
        self.organizer: str | None = None
        self.categories: list[str | None] = []
        self.floating: bool = False
        self.status: str | None = None
        self.url: str | None = None
        self.component: Component | None = None

    def time_left(self, time: datetime | None = None) -> timedelta:
        """
        timedelta form now to event.

        :return: timedelta from now
        """
        time = time or now()
        return self.start - time

    def __lt__(self, other: object) -> bool:
        """
        Events are sorted by start time by default.

        :param other: other event
        :return: True if start of this event is smaller than other
        """
        if not other or not isinstance(other, Event):
            raise ValueError(
                "Only events can be compared with each other! Other is %s" % type(other)
            )
        else:
            # start and end can be dates, datetimes and datetimes with timezoneinfo
            if type(self.start) is date and type(other.start) is date:
                return self.start < other.start
            elif type(self.start) is datetime and type(other.start) is datetime:
                if self.start.tzinfo == other.start.tzinfo:
                    return self.start < other.start
                else:
                    return self.start.astimezone(UTC) < other.start.astimezone(UTC)
            elif type(self.start) is date and type(other.start) is datetime:
                return self.start < other.start.date()
            elif type(self.start) is datetime and type(other.start) is date:
                return self.start.date() < other.start

    def __str__(self) -> str:
        return "%s: %s (%s)" % (self.start, self.summary, self.end - self.start)

    def astimezone(self, tzinfo: _tzinfo) -> Event:
        if type(self.start) is datetime:
            self.start = self.start.astimezone(tzinfo)

        if type(self.end) is datetime:
            self.end = self.end.astimezone(tzinfo)

        return self

    def copy_to(
        self, new_start: datetime | None = None, uid: str | None = None
    ) -> Event:
        """
        Create a new event equal to this with new start date.

        :param new_start: new start date
        :param uid: UID of new event
        :return: new event
        """
        if not new_start:
            new_start = self.start

        if not uid:
            uid = "%s_%d" % (self.uid, randint(0, 1000000))

        ne = Event()
        ne.component = self.component
        ne.summary = self.summary
        ne.description = self.description
        ne.start = new_start

        if self.end:
            duration = self.end - self.start
            ne.end = new_start + duration

        ne.all_day = self.all_day
        ne.recurring = self.recurring
        ne.location = self.location
        ne.attendee = self.attendee
        ne.organizer = self.organizer
        ne.private = self.private
        ne.transparent = self.transparent
        ne.uid = uid
        ne.created = self.created
        ne.last_modified = self.last_modified
        ne.categories = self.categories
        ne.floating = self.floating
        ne.status = self.status
        ne.url = self.url

        return ne


def encode(value: vText | None) -> str | None:
    if value is None:
        return None
    try:
        return str(value)
    except UnicodeEncodeError:
        return str(value.encode("utf-8"))


def create_event(component: Component, strict: bool) -> Event:
    """
    Create an event from its iCal representation.

    :param component: iCal component
    :param strict:
    :return: event
    """

    event = Event()

    event.component = component

    event.start = component.get("dtstart").dt
    # The RFC specifies that the TZID parameter must be specified for datetime or time
    # Otherwise we set a default timezone (if only one is set with VTIMEZONE) or utc
    if not strict:
        event.floating = (
            type(component.get("dtstart").dt) == date
            or component.get("dtstart").dt.tzinfo is None
        )
    else:
        event.floating = (
            type(component.get("dtstart").dt) == datetime
            and component.get("dtstart").dt.tzinfo is None
        )

    if component.get("dtend"):
        event.end = component.get("dtend").dt
    elif component.get("duration"):  # compute implicit end as start + duration
        event.end = event.start + component.get("duration").dt
    else:  # compute implicit end as start + 0
        event.end = event.start

    event.summary = encode(component.get("summary"))
    event.description = encode(component.get("description"))
    event.all_day = type(component.get("dtstart").dt) is date
    if component.get("rrule"):
        event.recurring = True
    event.location = encode(component.get("location"))

    if component.get("attendee"):
        attendees = component.get("attendee")
        if type(attendees) is list:
            event.attendee = [Attendee(attendee) for attendee in attendees]
        elif attendees:
            event.attendee = Attendee(attendees)

    try:
        event.uid = component.get("uid").encode("utf-8").decode("ascii")
    except (AttributeError, UnicodeDecodeError):
        event.uid = str(uuid4())  # Be nice - treat every event as unique

    if component.get("organizer"):
        event.organizer = component.get("organizer").encode("utf-8").decode("ascii")
    else:
        event.organizer = str(None)

    if component.get("class"):
        event_class = component.get("class")
        event.private = event_class == "PRIVATE" or event_class == "CONFIDENTIAL"

    if component.get("transp"):
        event.transparent = component.get("transp") == "TRANSPARENT"

    if component.get("created"):
        event.created = component.get("created").dt

    if component.get("RECURRENCE-ID"):
        rid = component.get("RECURRENCE-ID").dt

        # Spec defines that if DTSTART is a date RECURRENCE-ID also is to be interpreted as a date
        if type(component.get("dtstart").dt) is date:
            event.recurrence_id = date(year=rid.year, month=rid.month, day=rid.day)
        else:
            event.recurrence_id = rid

    if component.get("last-modified"):
        event.last_modified = component.get("last-modified").dt
    elif event.created:
        event.last_modified = event.created

    # sequence can be 0 - test for None instead
    if component.get("sequence") is not None:
        event.sequence = component.get("sequence")

    if component.get("categories"):
        categories = component.get("categories").cats
        encoded_categories = list()
        for category in categories:
            encoded_categories.append(encode(category))
        event.categories = encoded_categories

    if component.get("status"):
        event.status = encode(component.get("status"))

    if component.get("url"):
        event.url = encode(component.get("url"))

    return event


def parse_events(
    content: str,
    start: datetime | None = None,
    end: datetime | None = None,
    default_span: timedelta = timedelta(days=7),
    tzinfo: _tzinfo | None = None,
    sort: bool = False,
    strict: bool = False,
):
    """
    Query the events occurring in a given time range.

    :param content: iCal URL/file content as String
    :param start: start date for search, default today (in UTC format)
    :param end: end date for search (in UTC format)
    :param default_span: default query length (one week)
    :return: events as list
    """
    if not start:
        start = now()

    if not end:
        end = start + default_span

    if not content:
        raise ValueError("Content is invalid!")

    calendar = Calendar.from_ical(content)

    # > Will be deprecated ========================
    # Calendar.from_ical already parses timezones as specified in the ical.
    # We can specify a 'default' tz but this is not according to spec.
    # Kept this here to verify tests and backward compatibility

    # Keep track of the timezones defined in the calendar
    timezones = {}

    # Parse non standard timezone name
    if "X-WR-TIMEZONE" in calendar:
        x_wr_timezone = str(calendar["X-WR-TIMEZONE"])
        timezones[x_wr_timezone] = get_timezone(x_wr_timezone)

    for c in calendar.walk("VTIMEZONE"):
        # we search for VTIMEZONE so we only get Timezone back
        c = cast(Timezone, c)
        name = str(c["TZID"])
        try:
            timezones[name] = c.to_tz()
        except IndexError:
            # This happens if the VTIMEZONE doesn't
            # contain start/end times for daylight
            # saving time. Get the system pytz
            # value from the name as a fallback.
            timezones[name] = timezone(name)

    # If there's exactly one timezone in the file,
    # assume it applies globally, otherwise UTC
    if len(timezones) == 1:
        cal_tz = get_timezone(list(timezones)[0])
    else:
        cal_tz = UTC
    # < ==========================================

    found: list[Event] = []

    def is_not_exception(date: datetime) -> bool:
        exdate = "%04d%02d%02d" % (
            date.year,
            date.month,
            date.day,
        )

        return exdate not in exceptions

    for component in calendar.walk():
        exceptions = {}

        if "EXDATE" in component:
            # Deal with the fact that sometimes it's a list and
            # sometimes it's a singleton
            exlist = []
            if isinstance(component["EXDATE"], vDDDLists):
                exlist = component["EXDATE"].dts
            else:
                exlist = component["EXDATE"]
            for ex in exlist:
                exdate = ex.to_ical().decode("UTF-8")
                exceptions[exdate[0:8]] = exdate

        if component.name == "VEVENT":
            e = create_event(component, strict)

            # make rule.between happy and provide from, to points in time that have the same format as dtstart
            if type(e.start) is date and not e.recurring:
                f, t = date(start.year, start.month, start.day), date(
                    end.year, end.month, end.day
                )
            elif type(e.start) is datetime and e.start.tzinfo:
                f = (
                    datetime(
                        start.year,
                        start.month,
                        start.day,
                        start.hour,
                        start.minute,
                        tzinfo=e.start.tzinfo,
                    )
                    if type(start) == datetime
                    else datetime(
                        start.year, start.month, start.day, tzinfo=e.start.tzinfo
                    )
                )
                t = (
                    datetime(
                        end.year,
                        end.month,
                        end.day,
                        end.hour,
                        end.minute,
                        tzinfo=e.start.tzinfo,
                    )
                    if type(end) == datetime
                    else datetime(end.year, end.month, end.day, tzinfo=e.start.tzinfo)
                )
            else:
                f = (
                    datetime(
                        start.year, start.month, start.day, start.hour, start.minute
                    )
                    if type(start) == datetime
                    else datetime(start.year, start.month, start.day)
                )
                t = (
                    datetime(end.year, end.month, end.day, end.hour, end.minute)
                    if type(end) == datetime
                    else datetime(end.year, end.month, end.day)
                )

            if e.recurring:
                rule = parse_rrule(component)
                # We can not use rule.between because the event has to fit in between https://github.com/jazzband/icalevents/issues/101
                for dt in [
                    dt
                    for dt in list(rule.between(f - (end - start), t + (end - start)))
                    if dt >= f and dt <= t
                ]:
                    # Recompute the start time in the current timezone *on* the
                    # date of *this* occurrence. This handles the case where the
                    # recurrence has crossed over the daylight savings time boundary.
                    if is_not_exception(dt):
                        if type(dt) is datetime and dt.tzinfo:
                            ecopy = e.copy_to(
                                dt.replace(tzinfo=get_timezone(str(dt.tzinfo))),
                                e.uid,
                            )
                        else:
                            ecopy = e.copy_to(
                                dt.date() if type(e.start) is date else dt, e.uid
                            )
                        found.append(ecopy)

            elif e.end >= f and e.start <= t and is_not_exception(e.start):
                found.append(e)

    result = found.copy()

    # Remove events that are replaced in ical
    for event in found:
        if not event.recurrence_id and (
            event.uid,
            event.start,
        ) in [(f.uid, f.recurrence_id) for f in found]:
            result.remove(event)

    # > Will be deprecated ========================
    # We will apply default cal_tz as required by some tests.
    # This is just here for backward-compatibility
    if not strict:
        for event in result:
            if type(event.start) is date:
                event.start = datetime(
                    year=event.start.year,
                    month=event.start.month,
                    day=event.start.day,
                    hour=0,
                    minute=0,
                    tzinfo=cal_tz,
                )
                event.end = datetime(
                    year=event.end.year,
                    month=event.end.month,
                    day=event.end.day,
                    hour=0,
                    minute=0,
                    tzinfo=cal_tz,
                )
            elif type(event.start) is datetime:
                if event.start.tzinfo:
                    event.start = event.start.astimezone(cal_tz)
                    event.end = event.end.astimezone(cal_tz)
                else:
                    event.start = event.start.replace(tzinfo=cal_tz)
                    event.end = event.end.replace(tzinfo=cal_tz)

            if event.created:
                if type(event.created) is date:
                    event.created = datetime(
                        year=event.created.year,
                        month=event.created.month,
                        day=event.created.day,
                        hour=0,
                        minute=0,
                        tzinfo=cal_tz,
                    )
                if type(event.created) is datetime:
                    if event.created.tzinfo:
                        event.created = event.created.astimezone(cal_tz)
                    else:
                        event.created = event.created.replace(tzinfo=cal_tz)

            if event.last_modified:
                if type(event.last_modified) is date:
                    event.last_modified = datetime(
                        year=event.last_modified.year,
                        month=event.last_modified.month,
                        day=event.last_modified.day,
                        hour=0,
                        minute=0,
                        tzinfo=cal_tz,
                    )
                if type(event.last_modified) is datetime:
                    if event.last_modified.tzinfo:
                        event.last_modified = event.last_modified.astimezone(cal_tz)
                    else:
                        event.last_modified = event.last_modified.replace(tzinfo=cal_tz)
    # < ==========================================

    if sort:
        result.sort()

    if tzinfo:
        result = [event.astimezone(tzinfo) for event in result]

    return result


def parse_rrule(component: Component):
    """
    Extract a dateutil.rrule object from an icalendar component. Also includes
    the component's dtstart and exdate properties. The rdate and exrule
    properties are not yet supported.

    :param component: icalendar component
    :return: extracted rrule or rruleset or None
    """

    dtstart = component.get("dtstart").dt

    # component['rrule'] can be both a scalar and a list
    rrules = component.get("rrule")
    if not isinstance(rrules, list):
        rrules = [rrules]

    def conform_until(until, dtstart):
        if type(dtstart) is datetime:
            # If we have timezone defined adjust for daylight saving time
            if type(until) is datetime:
                return until + abs(
                    (
                        until.astimezone(dtstart.tzinfo).utcoffset()
                        if until.tzinfo is not None and dtstart.tzinfo is not None
                        else None
                    )
                    or timedelta()
                )

            return (
                until.astimezone(UTC)
                if type(until) is datetime
                else datetime(
                    year=until.year, month=until.month, day=until.day, tzinfo=UTC
                )
            ) + (
                dtstart.tzinfo.utcoffset(dtstart) if dtstart.tzinfo else None
            ) or timedelta()

        return until.date() + timedelta(days=1) if type(until) is datetime else until

    for index, rru in enumerate(rrules):
        if "UNTIL" in rru:
            rrules[index]["UNTIL"] = [
                conform_until(until, dtstart) for until in rrules[index]["UNTIL"]
            ]

    rule: rruleset = rrulestr(  # type: ignore[assignment]
        "\n".join(x.to_ical().decode() for x in rrules),
        dtstart=dtstart,
        forceset=True,
        unfold=True,
    )

    if component.get("exdate"):
        # Add exdates to the rruleset
        for exd in extract_exdates(component):
            if type(dtstart) is date:
                if type(exd) is date:
                    # Always convert exdates to datetimes because rrule.between does not like dates
                    # https://github.com/dateutil/dateutil/issues/938
                    rule.exdate(datetime.combine(exd, datetime.min.time()))
                else:
                    rule.exdate(exd.replace(tzinfo=None))
            else:
                rule.exdate(exd)

    # TODO: What about rdates and exrules?
    if component.get("exrule"):
        pass

    if component.get("rdate"):
        pass

    return rule


def extract_exdates(component: Component) -> list[datetime]:
    """
    Compile a list of all exception dates stored with a component.

    :param component: icalendar iCal component
    :return: list of exception dates
    """
    dates: list[datetime] = []
    exd_prop = component.get("exdate")
    if isinstance(exd_prop, list):
        for exd_list in exd_prop:
            dates.extend(exd.dt for exd in exd_list.dts)
    else:  # it must be a vDDDLists
        dates.extend(exd.dt for exd in exd_prop.dts)

    return dates


def get_timezone(tz_name: str) -> _tzinfo | None:
    if tz_name in WINDOWS_TO_OLSON:
        return gettz(WINDOWS_TO_OLSON[tz_name])
    else:
        return gettz(tz_name)
