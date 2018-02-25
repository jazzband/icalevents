import unittest
import icalevents.icalparser
from datetime import datetime, date
from pytz import utc


class ICalParserTests(unittest.TestCase):

    def setUp(self):
        self.eventA = icalevents.icalparser.Event()
        self.eventA.uid = 1234
        self.eventA.start = datetime(year=2017, month=2, day=3, hour=12, minute=5, tzinfo=utc)
        self.eventA.end = datetime(year=2017, month=2, day=3, hour=15, minute=5, tzinfo=utc)
        self.eventA.all_day = False
        self.eventA.summary = "Event A"

        self.eventB = icalevents.icalparser.Event()
        self.eventB.uid = 1234
        self.eventB.start = datetime(year=2017, month=2, day=1, hour=15, minute=5, tzinfo=utc)
        self.eventB.end = datetime(year=2017, month=2, day=1, hour=16, minute=5, tzinfo=utc)
        self.eventB.all_day = False
        self.eventB.summary = "Event B"

    def test_now(self):
        n = icalevents.icalparser.now()

        self.assertTrue(type(n) == datetime, "result of now has type datetime")
        self.assertTrue(n.tzinfo, "result of now has a timezone info")

    def test_event_copy_to(self):
        new_start = utc.normalize(datetime(year=2017, month=2, day=5, hour=12, minute=5, tzinfo=utc))
        eventC = self.eventA.copy_to(new_start)

        self.assertNotEqual(eventC.uid, self.eventA.uid, "new event has new UID")
        self.assertEqual(eventC.start, new_start, "new event has new start")
        self.assertEqual(eventC.end - eventC.start, self.eventA.end - self.eventA.start, "new event has same duration")
        self.assertEqual(eventC.all_day , False, "new event is no all day event")
        self.assertEqual(eventC.summary, self.eventA.summary, "copy to: summary")

    def test_event_order(self):
        self.assertTrue(self.eventA > self.eventB, "order of events")

    def test_next_year(self):
        date = utc.normalize(datetime(year=2016, month=1, day=1, hour=0, minute=0, tzinfo=utc))

        other = icalevents.icalparser.next_year_at(date, count=2)

        self.assertEqual(date.year + 2, other.year, "year is changed")
        self.assertEqual(date.month, other.month, "month is same")
        self.assertEqual(date.day, other.day, "day is same")
        self.assertEqual(date.hour, other.hour, "hour is same")
        self.assertEqual(date.minute, other.minute, "minute is same")
        self.assertEqual(date.tzinfo, other.tzinfo, "timezone is same")

    def test_next_month(self):
        dt = utc.normalize(datetime(year=2016, month=10, day=1, hour=0, minute=0, tzinfo=utc))

        other = icalevents.icalparser.next_month_at(dt, count=5)

        self.assertEqual(2017, other.year, "year is same")
        self.assertEqual(3, other.month, "month is changed")
        self.assertEqual(dt.day, other.day, "day is same")
        self.assertEqual(dt.hour, other.hour, "hour is same")
        self.assertEqual(dt.minute, other.minute, "minute is same")
        self.assertEqual(dt.tzinfo, other.tzinfo, "timezone is same")

    def test_normalize(self):
        dt = date(year=2016, month=11, day=13)
        norm = icalevents.icalparser.normalize(dt)

        self.assertTrue(type(norm) is datetime, "type is datetime")
        self.assertEqual(2016, norm.year, "year")
        self.assertEqual(11, norm.month, "month")
        self.assertEqual(13, norm.day, "day")
        self.assertEqual(0, norm.hour, "hour")
        self.assertEqual(0, norm.minute, "minute")
        self.assertEqual(0, norm.second, "second")
        self.assertEqual(0, norm.microsecond, "microsecond")
        self.assertEqual(utc, norm.tzinfo, "timezone")

    def test_in_range(self):
        range_start = datetime(year=2017, month=2, day=2, hour=12, minute=0, tzinfo=utc)
        range_end = datetime(year=2017, month=2, day=4, hour=12, minute=0, tzinfo=utc)

        events = [self.eventA, self.eventB]

        filtered = icalevents.icalparser.in_range(events, range_start, range_end)

        self.assertEqual(len(filtered), 1, "one event is left")
        self.assertEqual(filtered[0], self.eventA, "event A is left")

    def test_generate_day_deltas_by_weekday(self):
        by_day = {'MO', 'WE', 'SU'}
        result = icalevents.icalparser.generate_day_deltas_by_weekday(by_day)

        self.assertEqual(2, result[0], 'Mon to Wed')
        self.assertEqual(4, result[2], 'Wed to Sun')
        self.assertEqual(1, result[6], 'Sun to Mon')

        by_day = {'MO'}
        result = icalevents.icalparser.generate_day_deltas_by_weekday(by_day)

        self.assertEqual(7, result[0], 'Mon to Mon')
