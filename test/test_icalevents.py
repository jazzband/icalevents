import unittest
from icalevents import icalevents
from datetime import date, timedelta, datetime
from time import sleep
from dateutil.relativedelta import relativedelta
from dateutil.tz import UTC
from re import search


class ICalEventsTests(unittest.TestCase):
    def test_events_url(self):
        url = "https://raw.githubusercontent.com/irgangla/icalevents/master/test/test_data/basic.ics"
        start = date(2017, 5, 18)
        end = date(2017, 5, 19)

        evs = icalevents.events(url=url, file=None, start=start, end=end)

        self.assertEqual(len(evs), 2, "two events are found")

    def test_events_start(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 5, 16)

        evs = icalevents.events(url=None, file=ical, start=start)

        self.assertEqual(len(evs), 3, "three events are found")

    def test_events(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 5, 18)
        end = date(2017, 5, 19)

        evs = icalevents.events(url=None, file=ical, start=start, end=end)

        self.assertEqual(len(evs), 2, "two events are found")
        
    def test_events_duration(self):
        ical = "test/test_data/duration.ics"
        start = date(2018, 1, 1)
        end = date(2018, 2, 1)
        
        evs = icalevents.events(file=ical, start=start, end=end)
        
        e1 = evs[0]
        self.assertEqual(e1.start.day, 10, "explicit event start")
        self.assertEqual(e1.end.day, 13, "implicit event end")

        e2 = evs[1]
        self.assertEqual(e2.start.hour, 10, "explicit event start")
        self.assertEqual(e2.end.hour, 13, "implicit event end")

        e3 = evs[2]
        self.assertEqual(e3.start.hour, 12, "explicit event start")
        self.assertEqual(e3.end.hour, 12, "implicit event end")
        
    def test_events_recurring(self):
        ical = "test/test_data/recurring.ics"
        start = date(2018, 10, 15)
        end = date(2018, 11, 15)
        
        evs = icalevents.events(file=ical, start=start, end=end)
        
        e1 = evs[1]
        self.assertEqual(e1.start.hour, 10, "check time with DST")
        self.assertEqual(e1.start.tzinfo.utcoffset(e1.start), timedelta(seconds=7200), "check UTC offset with DST")
        
        e2 = evs[2]
        self.assertEqual(e2.start.hour, 10, "check time without DST")
        self.assertEqual(e2.start.tzinfo.utcoffset(e2.start), timedelta(seconds=3600), "check UTC offset without DST")
        
        self.assertEqual(e2.start.day, 5, "Check observance of exdate.")
        
    def test_events_exdates(self):
        ical = "test/test_data/recurring.ics"
        start = date(2018, 6, 1)
        end = date(2018, 6, 30)
        
        evs = icalevents.events(file=ical, start=start, end=end)
        
        self.assertEqual(evs[0].start.day, 1, "check first recurrence.")
        self.assertEqual(evs[1].start.day, 15, "check first exdate.")
        self.assertEqual(evs[2].start.day, 29, "check second exdate.")

    def test_events_all_day_recurring(self):
        ical = "test/test_data/recurring.ics"
        start = date(2018, 10, 30)
        end = date(2018, 10, 31)

        evs = icalevents.events(file=ical, start=start, end=end)

        event_set = icalevents.events(url=None, file=ical, start=start, end=end)
        ev = event_set[0]

        self.assertEqual(len(event_set), 1)
        self.assertEqual(ev.summary, "Recurring All-day Event")
        self.assertEqual(ev.description, "All-day event recurring on tuesday each week")
        self.assertTrue(ev.all_day, "Recurring All-day Event's first instance is an all-day event")

        start_2nd_instance = date(2018, 11, 6)
        end_2nd_instance = date(2018, 11, 7)

        event_set2 = icalevents.events(url=None, file=ical, start=start_2nd_instance, end=end_2nd_instance)
        ev_2 = event_set2[0]

        self.assertEqual(len(event_set2), 1)
        self.assertEqual(ev_2.summary, "Recurring All-day Event")
        self.assertEqual(ev_2.description, "All-day event recurring on tuesday each week")
        self.assertTrue(ev_2.all_day, "Recurring All-day Event's second instance is an all-day event")


    def test_event_attributes(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 7, 12)
        end = date(2017, 7, 13)

        ev = icalevents.events(url=None, file=ical, start=start, end=end)[0]

        self.assertEqual(ev.summary, "graue Restmülltonne")
        self.assertEqual(ev.description, "graue Restmülltonne nicht vergessen!")
        self.assertTrue(ev.all_day)

    def test_events_async_url(self):
        url = "https://raw.githubusercontent.com/irgangla/icalevents/master/test/test_data/basic.ics"
        start = date(2017, 5, 18)
        end = date(2017, 5, 19)
        key = "basic"

        icalevents.events_async(key, url=url, file=None, start=start, end=end)

        sleep(4)

        self.assertTrue(icalevents.all_done(key), "request is finished")
        self.assertEqual(len(icalevents.latest_events(key)), 2, "two events are found")

    def test_events_async(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 5, 18)
        end = date(2017, 5, 19)
        key = "basic"

        icalevents.events_async(key, url=None, file=ical, start=start, end=end)

        sleep(4)

        self.assertTrue(icalevents.all_done(key), "request is finished")
        self.assertEqual(len(icalevents.latest_events(key)), 2, "two events are found")

    def test_request_data(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 5, 18)
        end = date(2017, 5, 19)
        key = "basic"

        icalevents.request_data(key, url=None, file=ical, string_content=None, start=start, end=end, fix_apple=False)

        self.assertTrue(icalevents.all_done(key), "request is finished")
        self.assertEqual(len(icalevents.latest_events(key)), 2, "two events are found")

    def test_string_data(self):
        ical = "test/test_data/basic.ics"

        with open(ical, mode='rb') as f:
            string_content = f.read()

        start = date(2017, 5, 18)
        end = date(2017, 5, 19)
        key = "basic"

        icalevents.request_data(key, url=None, file=None, string_content=string_content, start=start, end=end,
                                fix_apple=False)

        self.assertTrue(icalevents.all_done(key), "request is finished")
        self.assertEqual(len(icalevents.latest_events(key)), 2, "two events are found")
        
    def test_event_str(self):
        ical = "test/test_data/duration.ics"
        start = date(2018, 1, 1)
        end = date(2018, 2, 1)
        n = datetime.now(UTC)
        m = relativedelta(hour=0, minute=0, second=0, microsecond=0)
        
        evs = icalevents.events(file=ical, start=start, end=end)
        
        e1 = evs[0]
        self.assertIsNotNone(search(r"ended", str(e1.copy_to(n - relativedelta(days=5) + m))), "stringify past event")
        self.assertIsNotNone(search(r"today", str(e1.copy_to(n - relativedelta(days=1) + m))), "stringify ongoing event")
        self.assertIsNotNone(search(r"days left", str(e1.copy_to(n + relativedelta(days=3) + m))), "stringify future event")
        
        e2 = evs[1]
        self.assertIsNotNone(search(r"ended", str(e2.copy_to(n - relativedelta(hours=5)))), "stringify past event")
        self.assertIsNotNone(search(r"now", str(e2.copy_to(n - relativedelta(hours=1)))), "stringify ongoing event")
        self.assertIsNotNone(search(r"hours left", str(e2.copy_to(n + relativedelta(hours=3)))), "stringify future event")
        self.assertIsNotNone(search(r"days left", str(e2.copy_to(n + relativedelta(days=3)))), "stringify future event")
