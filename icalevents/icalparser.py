"""
Parse iCal data to Events.
"""
# for UID generation
from random import randint
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from dateutil.rrule import rrule, rruleset, rrulestr

from icalendar import Calendar
from icalendar.prop import vDDDLists
from pytz import utc


# default query length (one week)
default_span = timedelta(days=7)


def now():
    """
    Get current time.

    :return: now as datetime with timezone
    """
    return utc.localize(datetime.utcnow())


class Event:
    """
    Represents one event (occurrence in case of reoccurring events).
    """

    def __init__(self):
        """
        Create a new event occurrence.
        """
        self.uid = -1
        self.summary = None
        self.description = None
        self.start = None
        self.end = None
        self.all_day = True

    def time_left(self, time=now()):
        """
        timedelta form now to event.

        :return: timedelta from now
        """
        return self.start - time

    def __lt__(self, other):
        """
        Events are sorted by start time by default.

        :param other: other event
        :return: True if start of this event is smaller than other
        """
        if not other or not isinstance(other, Event):
            raise ValueError('Only events can be compared with each other! Other is %s' % type(other))
        else:
            return self.start < other.start

    def __str__(self):
        n = now()

        # compute time delta description
        if not self.all_day:
            if self.end > n > self.start:
                # event is now
                delta = "now"
            elif self.start > n:
                # event is a future event
                if self.time_left().days > 0:
                    delta = "%s days left" % self.time_left().days
                else:
                    hours = self.time_left().seconds / (60 * 60)
                    delta = "%.1f hours left" % hours
            else:
                # event is over
                delta = "ended"
        else:
            if self.end > n > self.start:
                delta = "today"
            elif self.start > n:
                delta = "%s days left" % self.time_left().days
            else:
                delta = "ended"

        return "%s: %s (%s)" % (self.start, self.summary, delta)

    def copy_to(self, new_start=None, uid=None):
        """
        Create a new event equal to this with new start date.

        :param new_start: new start date
        :param uid: UID of new event
        :return: new event
        """
        duration = self.end - self.start

        if not new_start:
            new_start = self.start

        if not uid:
            uid = "%s_%d" % (self.uid, randint(0, 1000000))

        ne = Event()
        ne.summary = self.summary
        ne.description = self.description
        ne.start = new_start
        ne.end = (new_start + duration)
        ne.all_day = (self.all_day and (new_start - self.start).seconds == 0)
        ne.uid = uid

        return ne


def next_year_at(dt, count=1):
    """
    Move date <count> years to the future.

    :param dt: date as datetime
    :param count: number of years
    :return: date datetime
    """
    dt += relativedelta.relativedelta(years=+count)
    return normalize(datetime(year=dt.year, month=dt.month, day=dt.day,
                              hour=dt.hour, minute=dt.minute,
                              second=dt.second, microsecond=dt.microsecond))


def next_month_at(dt, count=1):
    """
    Move date <count> months to the future.

    :param dt: date as datetime
    :param count: number of months
    :return: date datetime
    """
    dt += relativedelta.relativedelta(months=+count)

    return normalize(datetime(year=dt.year, month=dt.month, day=dt.day,
                              hour=dt.hour, minute=dt.minute, second=dt.second,
                              microsecond=dt.microsecond))


def create_event(component):
    """
    Create an event from its iCal representation.

    :param component: iCal component
    :return: event
    """

    event = Event()

    event.start = normalize(component.get('dtstart').dt)
    
    if component.get('dtend'):
        event.end = normalize(component.get('dtend').dt)
    elif component.get('duration'):
        event.end = event.start + component.get('duration').dt
    else:
        raise ValueError("Event has neither end, nor duration property.")
    
    event.summary = str(component.get('summary'))
    event.description = str(component.get('description'))
    event.all_day = type(component.get('dtstart').dt) is date

    return event


def normalize(dt):
    """
    Convert date or datetime to datetime with timezone.

    :param dt: date to normalize
    :return: date as datetime with timezone
    """
    if type(dt) is date:
        dt = datetime(dt.year, dt.month, dt.day, 0, 0)
    elif type(dt) is datetime:
        pass
    else:
        raise ValueError("unknown type %s" % type(dt))

    if not dt.tzinfo:
        dt = utc.localize(dt)

    return dt


def find_last(rule, freq, end, first):
    last = end

    if rule.get('UNTIL'):
        last = rule.get('UNTIL')[0]
    elif rule.get('COUNT'):
        count = rule.get('COUNT')[0]
        if freq == 'YEARLY':
            last = next_year_at(first.start, count=count)
        elif freq == 'MONTHLY':
            last = next_month_at(first.start, count=count)
        elif freq == 'WEEKLY':
            last = normalize(first.start + timedelta(days=7*count))
        elif freq == 'DAILY':
            last = normalize(first.start + timedelta(days=count))

    return normalize(last)


def in_range(event_list, start, end):
    """
    Find elements in the given time range.

    :param event_list: list of events
    :param start: start datetime
    :param end: end datetime
    :return: events in range
    """
    filtered = []
    for e in event_list:
        if e.end > start and e.start < end:
            filtered.append(e)

    return filtered


def parse_events(content, start=None, end=None):
    """
    Query the events occurring in a given time range.

    :param content: iCal URL/file content as String
    :param start: start date for search, default today
    :param end: end date for search
    :return: events as list
    """
    if not start:
        start = now()

    if not end:
        end = start + default_span

    if not content:
        raise ValueError('Content is invalid!')

    calendar = Calendar.from_ical(content)

    start = normalize(start)
    end = normalize(end)

    found = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            e = create_event(component)
            if component.get('rrule'):
                rule = parse_rrule(component)
                dur = e.end - e.start
                found.extend(e.copy_to(adjust_dst(dt)) for dt in rule.between(start - dur, end, inc=True))
            elif e.end >= start and e.start <= end:
                found.append(e)
    return found


# Awful hack to adjust timezone throughout DST transitions.
def adjust_dst (dt):
    """
    Recomputes a datetime's UTC offset without changing the displayed value.
    This is useful when shifting dates beyond DST transitions using dateutil's
    relativedelta and rrule tools.
    
    :param dt: a datetime object
    :return: adjusted datetime object
    """
    if dt.tzinfo:
        return dt.tzinfo.localize(dt.replace(tzinfo=None))
    else:
        return dt


def parse_rrule(component):
    if component.get('rrule'):
        # Parse the rrule, might return a rruleset instance, instead of rrule
        rule = rrulestr(component['rrule'].to_ical().decode(), dtstart=normalize(component['dtstart'].dt))
        
        if component.get('exdate'):
            # Make sure, to work with a rruleset
            if isinstance(rule, rrule):
                rules = rruleset()
                rules.rrule(rule)
                rule = rules
            
            for exd in extract_exdates(component):
                rule.exdate(exd)
        
        #TODO: What about rdates and exrules?
        
    # You really want an rrule for a component without rrule? Here you are.
    else:
        rule = rruleset()
        rule.rdate(normalize(component['dtstart'].dt))
    
    return rule


def create_recurring_events(start, end, component):
    """
    Unfold a reoccurring event to its occurrances into the given time frame.

    :param start: start of the time frame
    :param end: end of the time frame
    :param component: iCal component
    :return: occurrances of the event
    """
    start = normalize(start)
    end = normalize(end)

    rule = component.get('rrule')

    unfolded = []

    first = create_event(component)
    unfolded.append(first)

    freq = str(rule.get('FREQ')[0])
    last = find_last(rule, freq, end, first)

    if last < start:
        return
    elif end < last:
        limit = end
    else:
        limit = last

    current = first

    if freq == 'YEARLY':
        while True:
            current = current.copy_to(next_year_at(current.start))
            if current.start < limit:
                unfolded.append(current)
            else:
                break
    elif freq == 'MONTHLY':
        by_day = rule.get('BYDAY')

        while True:
            if by_day:
                next_date = next_month_byday_delta(current.start, by_day[0])
                current = current.copy_to(next_date)
            else:
                current = current.copy_to(next_month_at(current.start))
            if current.start < limit:
                unfolded.append(current)
            else:
                break
    elif freq == 'DAILY':
        delta = timedelta(days=1)
        while True:
            current = current.copy_to(current.start + delta)
            if current.start < limit:
                unfolded.append(current)
            else:
                break
    elif freq == 'WEEKLY':
        delta = timedelta(days=7)

        by_day = rule.get('BYDAY')
        if by_day:
            day_deltas = generate_day_deltas_by_weekday(set(by_day))
        else:
            day_deltas = None

        while True:
            if day_deltas:
                delta = timedelta(days=day_deltas.get(current.start.weekday()))
            current = current.copy_to(current.start + delta)
            if current.start < limit:
                unfolded.append(current)
            else:
                break
    else:
        return

    reduced_range = in_range(unfolded, start, end)

    exceptions = extract_exdates(component)
    reduced_exceptions = [ev for ev in reduced_range if ev.start not in exceptions]

    return reduced_exceptions


def extract_exdates(component):
    """
    Compile a list of all exception dates stored with a component.
    
    :param component: icalendar iCal component
    :return: exception dates
    """
    dates = []

    exd_prop = component.get('exdate')
    if exd_prop:
        if isinstance(exd_prop, list):
            for exd_list in exd_prop:
                dates.extend(normalize(exd.dt) for exd in exd_list.dts)
        elif isinstance(exd_prop, vDDDLists):
            dates.extend(normalize(exd.dt) for exd in exd_prop.dts)

    return dates


def generate_day_deltas_by_weekday(by_day):
    """
    Create a dict to determine how many days to add to the current
    event to get the next event when a WEEKLY rule contains a
    BYDAY clause.

    The resulting dictionary has the weekday number as keys and the
    number of days to add to get the next event as values. Weekday
    numbers are the same as those assigned by the date.weekday()
    function.

    :param by_day: list or set of two-letter weekday abbreviations
    :return: dict mapping weekday numbers to day deltas
    """
    weekdays = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

    selected_weekday_numbers = []
    day_deltas = []
    hop_count = 0
    for weekday_number, weekday_name in enumerate(weekdays):
        if weekday_name in by_day:
            selected_weekday_numbers.append(weekday_number)
            day_deltas.append(hop_count)
            hop_count = 0
        hop_count += 1

    # readjust the first deltas to include the remaining deltas
    first_hop_count = day_deltas[0] + hop_count
    adjusted_deltas = day_deltas[1:] + [first_hop_count]

    return dict(zip(selected_weekday_numbers, adjusted_deltas))


def next_month_byday_delta(start_date, by_day):
    """
    Get the next event date when a MONTHLY rule contains a BYDAY clause,
    e.g. 3SA = "Next third Saturday"
    """

    weekdays = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

    number = int(by_day[0])
    weekday = by_day[1:]

    if weekday not in weekdays:
        raise ValueError('Invalid weekday: {}'.format(weekday))

    weekday = weekdays.index(weekday)
    weekday_func = relativedelta.weekday(weekday)

    delta = relativedelta.relativedelta(day=1, months=+1,
                                        weekday=weekday_func(number))

    return start_date + delta
