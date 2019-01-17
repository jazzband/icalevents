"""
Parse iCal data to Events.
"""
# for UID generation
from random import randint
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, rruleset, rrulestr
from dateutil.tz import UTC, gettz

from icalendar import Calendar
from icalendar.prop import vDDDLists

from text_unidecode import unidecode

# default query length (one week)
default_span = timedelta(days=7)


def now():
    """
    Get current time.

    :return: now as datetime with timezone
    """
    return datetime.now(UTC)


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
        self.recurring = False

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
        if not new_start:
            new_start = self.start

        if not uid:
            uid = "%s_%d" % (self.uid, randint(0, 1000000))

        ne = Event()
        ne.summary = self.summary
        ne.description = self.description
        ne.start = new_start
        
        if self.end:
            duration = self.end - self.start
            ne.end = (new_start + duration)

        ne.all_day = self.all_day
        ne.recurring = self.recurring
        ne.uid = uid

        return ne


def create_event(component, tz=UTC):
    """
    Create an event from its iCal representation.

    :param component: iCal component
    :param tz: timezone for start and end times
    :return: event
    """

    event = Event()

    event.start = normalize(component.get('dtstart').dt, tz=tz)
    
    if component.get('dtend'):
        event.end = normalize(component.get('dtend').dt, tz=tz)
    elif component.get('duration'): # compute implicit end as start + duration
        event.end = event.start + component.get('duration').dt
    else: # compute implicit end as start + 0
        event.end = event.start
    
    event.summary = str(unidecode(component.get('summary')))
    event.description = str(unidecode(component.get('description')))
    event.all_day = type(component.get('dtstart').dt) is date
    if component.get('rrule'):
        event.recurring = True
    return event


def normalize(dt, tz=UTC):
    """
    Convert date or datetime to datetime with timezone.

    :param dt: date to normalize
    :param tz: the normalized date's timezone
    :return: date as datetime with timezone
    """
    if type(dt) is date:
        dt = dt + relativedelta(hour=0)
    elif type(dt) is datetime:
        pass
    else:
        raise ValueError("unknown type %s" % type(dt))

    if dt.tzinfo:
        dt = dt.astimezone(tz)
    else:
        dt = dt.replace(tzinfo=tz)

    return dt


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
    
    # Find the calendar's timezone info, or use UTC
    for c in calendar.walk():
        if c.name == 'VTIMEZONE':
            cal_tz = gettz(str(c['TZID']))
            break;
    else:
        cal_tz = UTC

    start = normalize(start, cal_tz)
    end = normalize(end, cal_tz)

    found = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            e = create_event(component)
            if e.recurring:
                # Unfold recurring events according to their rrule
                rule = parse_rrule(component, cal_tz)
                dur = e.end - e.start
                found.extend(e.copy_to(dt) for dt in rule.between(start - dur, end, inc=True))
            elif e.end >= start and e.start <= end:
                found.append(e)
    return found


def parse_rrule(component, tz=UTC):
    """
    Extract a dateutil.rrule object from an icalendar component. Also includes
    the component's dtstart and exdate properties. The rdate and exrule
    properties are not yet supported.
    
    :param component: icalendar component
    :param tz: timezone for DST handling
    :return: extracted rrule or rruleset
    """
    if component.get('rrule'):
        # component['rrule'] can be both a scalar and a list
        rrules = component['rrule']
        if not isinstance(rrules, list):
            rrules = [rrules]
        # Parse the rrules, might return a rruleset instance, instead of rrule
        rule = rrulestr('\n'.join(x.to_ical().decode() for x in rrules), dtstart=normalize(component['dtstart'].dt, tz=tz))
        
        if component.get('exdate'):
            # Make sure, to work with a rruleset
            if isinstance(rule, rrule):
                rules = rruleset()
                rules.rrule(rule)
                rule = rules
            
            # Add exdates to the rruleset
            for exd in extract_exdates(component):
                rule.exdate(exd)
        
        #TODO: What about rdates and exrules?
        
    # You really want an rrule for a component without rrule? Here you are.
    else:
        rule = rruleset()
        rule.rdate(normalize(component['dtstart'].dt, tz=tz))
    
    return rule


def extract_exdates(component):
    """
    Compile a list of all exception dates stored with a component.
    
    :param component: icalendar iCal component
    :return: list of exception dates
    """
    dates = []

    exd_prop = component.get('exdate')
    if exd_prop:
        if isinstance(exd_prop, list): # In case there is more than one exdate property
            for exd_list in exd_prop:
                dates.extend(normalize(exd.dt) for exd in exd_list.dts)
        elif isinstance(exd_prop, vDDDLists):
            dates.extend(normalize(exd.dt) for exd in exd_prop.dts)

    return dates

