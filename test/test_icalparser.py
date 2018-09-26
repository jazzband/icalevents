import unittest
import icalevents.icalparser
from datetime import datetime, date
from dateutil.tz import UTC, gettz


class ICalParserTests(unittest.TestCase):

    def setUp(self):
        self.eventA = icalevents.icalparser.Event()
        self.eventA.uid = 1234
        self.eventA.start = datetime(year=2017, month=2, day=3, hour=12, minute=5, tzinfo=UTC)
        self.eventA.end = datetime(year=2017, month=2, day=3, hour=15, minute=5, tzinfo=UTC)
        self.eventA.all_day = False
        self.eventA.summary = "Event A"

        self.eventB = icalevents.icalparser.Event()
        self.eventB.uid = 1234
        self.eventB.start = datetime(year=2017, month=2, day=1, hour=15, minute=5, tzinfo=UTC)
        self.eventB.end = datetime(year=2017, month=2, day=1, hour=16, minute=5, tzinfo=UTC)
        self.eventB.all_day = False
        self.eventB.summary = "Event B"
        
        self.dtA = datetime(2018, 6, 21, 12)
        self.dtB = datetime(2018, 6, 21, 12, tzinfo=gettz('Europe/Berlin'))

    def test_now(self):
        n = icalevents.icalparser.now()

        self.assertTrue(type(n) == datetime, "result of now has type datetime")
        self.assertTrue(n.tzinfo, "result of now has a timezone info")

    def test_time_left(self):
        dt = datetime(year=2017, month=2, day=2, hour=11, minute=2, tzinfo=UTC)
        time_left = self.eventA.time_left(time=dt)
        self.assertEqual(time_left.days, 1)
        self.assertEqual(time_left.seconds, 3780)

    def test_event_copy_to(self):
        new_start = datetime(year=2017, month=2, day=5, hour=12, minute=5, tzinfo=UTC)
        eventC = self.eventA.copy_to(new_start)

        self.assertNotEqual(eventC.uid, self.eventA.uid, "new event has new UID")
        self.assertEqual(eventC.start, new_start, "new event has new start")
        self.assertEqual(eventC.end - eventC.start, self.eventA.end - self.eventA.start, "new event has same duration")
        self.assertEqual(eventC.all_day, False, "new event is no all day event")
        self.assertEqual(eventC.summary, self.eventA.summary, "copy to: summary")
        self.assertEqual(eventC.description, self.eventA.description, "copy to: description")

        eventD = eventC.copy_to()
        self.assertNotEqual(eventD.uid, eventC.uid, "new event has new UID")
        self.assertEqual(eventD.start, eventC.start, "new event has same start")
        self.assertEqual(eventD.end, eventC.end, "new event has same end")
        self.assertEqual(eventD.all_day, eventC.all_day, "new event is no all day event")
        self.assertEqual(eventD.summary, eventC.summary, "copy to: summary")
        self.assertEqual(eventD.description, eventC.description, "copy to: description")

    def test_event_order(self):
        self.assertTrue(self.eventA > self.eventB, "order of events")

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
        self.assertEqual(UTC, norm.tzinfo, "timezone")

        dt = datetime(year=2016, month=11, day=13, hour=1, minute=2, second=3)
        norm = icalevents.icalparser.normalize(dt)

        self.assertTrue(type(norm) is datetime, "type is datetime")
        self.assertEqual(2016, norm.year, "year")
        self.assertEqual(11, norm.month, "month")
        self.assertEqual(13, norm.day, "day")
        self.assertEqual(1, norm.hour, "hour")
        self.assertEqual(2, norm.minute, "minute")
        self.assertEqual(3, norm.second, "second")
        self.assertEqual(0, norm.microsecond, "microsecond")
        self.assertEqual(UTC, norm.tzinfo, "timezone")
