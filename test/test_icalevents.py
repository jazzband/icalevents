import unittest
from icalevents import icalevents
from datetime import date, timedelta, datetime
from time import sleep
from dateutil.relativedelta import relativedelta
from dateutil.tz import UTC, gettz
from re import search
import textwrap
import pytz


class ICalEventsTests(unittest.TestCase):
    def test_events_url(self):
        url = "https://raw.githubusercontent.com/jazzband/icalevents/master/test/test_data/basic.ics"
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

        evs = icalevents.events(file=ical, start=start, end=end, sort=False)

        e1 = evs[1]
        self.assertEqual(e1.start.hour, 10, "check time with DST")
        self.assertEqual(
            timedelta(seconds=7200),
            e1.start.tzinfo.utcoffset(e1.start),
            "check UTC offset with DST",
        )

        e2 = evs[2]
        self.assertEqual(e2.start.hour, 10, "check time without DST")
        self.assertEqual(
            timedelta(seconds=3600),
            e2.start.tzinfo.utcoffset(e2.start),
            "check UTC offset without DST",
        )

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
        self.assertTrue(
            ev.all_day, "Recurring All-day Event's first instance is an all-day event"
        )

        start_2nd_instance = date(2018, 11, 6)
        end_2nd_instance = date(2018, 11, 7)

        event_set2 = icalevents.events(
            url=None, file=ical, start=start_2nd_instance, end=end_2nd_instance
        )
        ev_2 = event_set2[0]

        self.assertEqual(len(event_set2), 1)
        self.assertEqual(ev_2.summary, "Recurring All-day Event")
        self.assertEqual(
            ev_2.description, "All-day event recurring on tuesday each week"
        )
        self.assertTrue(
            ev_2.all_day,
            "Recurring All-day Event's second instance is an all-day event",
        )

    def test_events_rrule_until_all_day_ms(self):
        ical = "test/test_data/rrule_until_all_day_ms.ics"
        start = date(2021, 1, 1)
        end = date(2022, 1, 1)

        evs = icalevents.events(file=ical, start=start, end=end)
        ev_0 = evs[0]

        self.assertEqual(
            len(evs), 6, "Seven events and one is excluded"
        )  # rrule_until_all_day_ms has one exdate (EXDATE;TZID=W. Europe Standard Time:20210430T000000)
        self.assertEqual(
            ev_0.start, datetime(2021, 3, 19, 00, 0, 0, tzinfo=gettz("Europe/Berlin"))
        )
        self.assertTrue(ev_0.recurring, "Recurring all day event")
        self.assertEqual(ev_0.summary, "Away")

    def test_events_rrule_until_all_day_google(self):
        ical = "test/test_data/rrule_until_all_day_google.ics"
        start = date(2021, 1, 1)
        end = date(2022, 1, 1)

        evs = icalevents.events(file=ical, start=start, end=end, sort=True)
        ev = evs[0]

        self.assertEqual(len(evs), 3)
        self.assertEqual(
            ev.start, datetime(2021, 3, 24, 00, 0, 0, tzinfo=gettz("Europe/Zurich"))
        )
        self.assertTrue(ev.all_day, "All day event")
        self.assertEqual(ev.summary, "Busy")

    def test_events_rrule_until_only_date(self):
        ical = "test/test_data/rrule_until_only_date.ics"
        start = date(2021, 9, 29)
        end = date(2021, 10, 19)
        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(len(evs), 8)
        self.assertEqual(
            evs[0].start,
            datetime(2021, 9, 29, 13, 0, 0, 0, tzinfo=gettz("America/Boise")),
        )
        self.assertEqual(
            evs[-1].start,
            datetime(2021, 10, 18, 13, 0, 0, 0, tzinfo=gettz("America/Boise")),
        )

    def test_events_rrule_until(self):
        ical = "test/test_data/rrule_until.ics"
        start = date(2019, 4, 2)
        end = date(2019, 4, 3)

        evs = icalevents.events(file=ical, start=start, end=end)

        self.assertEqual(len(evs), 2)
        self.assertTrue(evs[0].recurring)
        self.assertEqual(evs[0].summary, "Recurring All-day Event")
        self.assertTrue(evs[1].recurring)
        self.assertEqual(evs[1].summary, "Daily lunch event")

    def test_event_attributes(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 7, 12)
        end = date(2017, 7, 13)

        ev = icalevents.events(url=None, file=ical, start=start, end=end)[0]

        self.assertEqual(ev.summary, "graue Restmülltonne")
        self.assertEqual(ev.description, "graue Restmülltonne nicht vergessen!")
        self.assertTrue(ev.all_day)

    def test_event_recurring_attribute(self):
        ical = "test/test_data/basic.ics"
        start = date(2017, 7, 12)
        end = date(2017, 7, 13)

        ev = icalevents.events(url=None, file=ical, start=start, end=end)[0]
        self.assertFalse(ev.recurring, "check recurring=False for non recurring event")

        ical = "test/test_data/recurring.ics"
        start = date(2018, 10, 15)
        end = date(2018, 11, 15)

        evs = icalevents.events(file=ical, start=start, end=end)

        e1 = evs[1]
        e2 = evs[2]
        self.assertTrue(e1.recurring, "check recurring=True for recurring event (1)")
        self.assertTrue(e2.recurring, "check recurring=True for recurring event (2)")

    def test_events_async_url(self):
        url = "https://raw.githubusercontent.com/jazzband/icalevents/master/test/test_data/basic.ics"
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

        icalevents.request_data(
            key,
            url=None,
            file=ical,
            string_content=None,
            start=start,
            end=end,
            fix_apple=False,
        )

        self.assertTrue(icalevents.all_done(key), "request is finished")
        self.assertEqual(len(icalevents.latest_events(key)), 2, "two events are found")

    def test_string_data(self):
        ical = "test/test_data/basic.ics"

        with open(ical, mode="rb") as f:
            string_content = f.read()

        start = date(2017, 5, 18)
        end = date(2017, 5, 19)
        key = "basic"

        icalevents.request_data(
            key,
            url=None,
            file=None,
            string_content=string_content,
            start=start,
            end=end,
            fix_apple=False,
        )

        self.assertTrue(icalevents.all_done(key), "request is finished")
        self.assertEqual(len(icalevents.latest_events(key)), 2, "two events are found")

    def test_events_no_description(self):
        ical = "test/test_data/no_description.ics"
        start = date(2018, 10, 15)
        end = date(2018, 11, 15)

        e1 = icalevents.events(file=ical, start=start, end=end)[0]

        self.assertIsNone(e1.description)
        self.assertIsNone(e1.summary)
        self.assertIsNone(e1.location)

    def test_event_created_last_modified(self):
        ical = "test/test_data/created_last_modified.ics"
        start = date(2017, 7, 12)
        end = date(2017, 7, 15)

        events = icalevents.events(url=None, file=ical, start=start, end=end)

        self.assertEqual(events[0].created, datetime(2017, 1, 3, 7, 4, 1, tzinfo=UTC))
        self.assertEqual(
            events[0].last_modified, datetime(2017, 7, 11, 14, 0, 50, tzinfo=UTC)
        )

        self.assertEqual(events[1].created, datetime(2017, 1, 4, 8, 4, 1, tzinfo=UTC))
        self.assertEqual(
            events[1].last_modified, datetime(2017, 1, 4, 8, 4, 1, tzinfo=UTC)
        )

        self.assertIsNone(events[2].created)
        self.assertIsNone(events[2].last_modified)

    def test_event_categories(self):
        ical = "test/test_data/categories_test.ics"
        start = date(2020, 11, 10)
        end = date(2020, 11, 19)
        events = icalevents.events(url=None, file=ical, start=start, end=end)
        self.assertEqual(
            events[0].categories, ["In19-S04-IT2403"], "event 1 is not equal"
        )
        self.assertEqual(
            events[1].categories,
            ["In19-S04-IT2406", "In19-S04-IT2405"],
            "event 2 is not equal",
        )

    def test_google_timezone(self):
        ical = "test/test_data/google_tz.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)

        e1 = evs[0]
        self.assertEqual(e1.start.hour, 0, "check start of the day")
        self.assertEqual(
            e1.start.tzinfo, gettz("Europe/Zurich"), "check tz as specified in calendar"
        )

    def test_ms_timezone(self):
        ical = "test/test_data/ms_tz.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)

        e1 = evs[0]
        self.assertEqual(e1.start.hour, 0, "check start of the day")
        self.assertEqual(
            e1.start.tzinfo, gettz("Europe/Berlin"), "check tz as specified in calendar"
        )

    def test_recurence_id_ms(self):
        ical = "test/test_data/recurrenceid_ms.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end, sort=True)

        self.assertEqual(len(evs), 42, "42 events in total - one was moved")

    def test_recurence_id_ms_moved(self):
        ical = "test/test_data/recurrenceid_ms.ics"
        start = date(2021, 4, 8)
        end = date(2021, 4, 10)

        evs = icalevents.events(file=ical, start=start, end=end, sort=True)
        self.assertEqual(evs[0].start.day, 10)

        self.assertEqual(len(evs), 1, "only one event - it was moved")

    def test_recurence_id_google(self):
        ical = "test/test_data/recurrenceid_google.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)

        self.assertEqual(len(evs), 4, "4 events in total")

    def test_cest(self):
        ical = "test/test_data/cest.ics"
        start = date(2010, 1, 1)
        end = date(2023, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)

        self.assertEqual(len(evs), 239, "239 events in total")

    def test_cest_2021_02(self):
        ical = "test/test_data/cest.ics"
        start = date(2021, 2, 1)
        end = date(2021, 2, 28)

        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(len(evs), 17, "17 in february")

    def test_cest_2021_03(self):
        ical = "test/test_data/cest.ics"
        start = date(2021, 3, 1)
        end = date(2021, 3, 31)

        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(len(evs), 30, "30 in march")

    def test_cest_2021_04(self):
        ical = "test/test_data/cest.ics"
        start = date(2021, 4, 1)
        end = date(2021, 5, 1)

        tz = gettz("Europe/Zurich")
        events = icalevents.events(
            file=ical, start=start, end=end, tzinfo=tz, sort=True, strict=True
        )
        # self.assertEqual(events[2].start, 2)

        times = [
            ((2021, 4, 1, 14, 0), (2021, 4, 1, 14, 30)),
            ((2021, 4, 1, 15, 30), (2021, 4, 1, 17, 0)),
            ((2021, 4, 2), (2021, 4, 3)),
            ((2021, 4, 5, 16, 00), (2021, 4, 5, 17, 0)),
            ((2021, 4, 7), (2021, 4, 8)),
            ((2021, 4, 8, 11, 0), (2021, 4, 8, 12, 0)),
            ((2021, 4, 8, 14, 30), (2021, 4, 8, 15, 0)),
            ((2021, 4, 8, 15, 0), (2021, 4, 8, 15, 30)),
            ((2021, 4, 9), (2021, 4, 10)),
            ((2021, 4, 12, 11, 0), (2021, 4, 12, 11, 30)),
            ((2021, 4, 12, 16, 0), (2021, 4, 12, 17, 0)),
            ((2021, 4, 14), (2021, 4, 15)),
            ((2021, 4, 15, 12, 0), (2021, 4, 15, 13, 0)),
            ((2021, 4, 15, 15, 0), (2021, 4, 15, 15, 30)),
            ((2021, 4, 16), (2021, 4, 17)),
            ((2021, 4, 19, 16, 0), (2021, 4, 19, 17, 0)),
            ((2021, 4, 21), (2021, 4, 22)),
            ((2021, 4, 22, 11, 0), (2021, 4, 22, 12, 0)),
            ((2021, 4, 22, 14, 45), (2021, 4, 22, 15, 15)),
            ((2021, 4, 23), (2021, 4, 24)),
            ((2021, 4, 26, 16, 0), (2021, 4, 26, 17, 0)),
            ((2021, 4, 28), (2021, 4, 29)),
            ((2021, 4, 29, 9, 0), (2021, 4, 29, 11, 0)),
            ((2021, 4, 29, 11, 0), (2021, 4, 29, 11, 30)),
            ((2021, 4, 29, 14, 15), (2021, 4, 29, 15, 00)),
            ((2021, 4, 29, 15, 0), (2021, 4, 29, 15, 30)),
            ((2021, 4, 30), (2021, 5, 1)),
        ]

        for index, time in enumerate(times):
            self.assertEqual(
                events[index].start,
                date(*time[0]) if len(time[0]) == 3 else datetime(*time[0], tzinfo=tz),
            )
            self.assertEqual(
                events[index].end,
                date(*time[1]) if len(time[1]) == 3 else datetime(*time[1], tzinfo=tz),
            )

        self.assertEqual(len(events), len(times))

    def test_cest_2021_05(self):
        ical = "test/test_data/cest.ics"
        start = date(2021, 5, 1)
        end = date(2021, 6, 1)

        tz = gettz("Europe/Zurich")
        events = icalevents.events(
            file=ical, start=start, end=end, tzinfo=tz, sort=True, strict=True
        )

        times = [
            ((2021, 5, 3, 16, 0), (2021, 5, 3, 17, 0)),
            ((2021, 5, 5), (2021, 5, 6)),
            ((2021, 5, 6, 11, 0), (2021, 5, 6, 12, 0)),
            ((2021, 5, 6, 15, 0), (2021, 5, 6, 15, 30)),
            ((2021, 5, 7), (2021, 5, 8)),
            ((2021, 5, 10, 16, 0), (2021, 5, 10, 17, 0)),
            ((2021, 5, 12), (2021, 5, 13)),
            ((2021, 5, 13, 15, 0), (2021, 5, 13, 15, 30)),
            ((2021, 5, 14), (2021, 5, 15)),
            ((2021, 5, 17, 16, 0), (2021, 5, 17, 17, 0)),
            ((2021, 5, 19), (2021, 5, 20)),
            ((2021, 5, 20, 11, 0), (2021, 5, 20, 12, 0)),
            ((2021, 5, 20, 12, 0), (2021, 5, 20, 13, 0)),
            ((2021, 5, 20, 15, 0), (2021, 5, 20, 15, 30)),
            ((2021, 5, 21), (2021, 5, 22)),
            ((2021, 5, 24, 16, 0), (2021, 5, 24, 17, 0)),
            ((2021, 5, 26), (2021, 5, 27)),
            ((2021, 5, 27, 15, 0), (2021, 5, 27, 15, 30)),
            ((2021, 5, 28), (2021, 5, 29)),
            ((2021, 5, 31, 16, 0), (2021, 5, 31, 17, 0)),
        ]

        for index, time in enumerate(times):
            self.assertEqual(
                events[index].start,
                date(*time[0]) if len(time[0]) == 3 else datetime(*time[0], tzinfo=tz),
            )
            self.assertEqual(
                events[index].end,
                date(*time[1]) if len(time[1]) == 3 else datetime(*time[1], tzinfo=tz),
            )

        self.assertEqual(len(events), len(times))

    def test_cest_2021_06(self):
        ical = "test/test_data/cest.ics"
        start = date(2021, 6, 1)
        end = date(2021, 6, 30)

        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(len(evs), 11, "11 in june")

    def test_cest_2021_07(self):
        ical = "test/test_data/cest.ics"
        start = date(2021, 7, 1)
        end = date(2021, 7, 31)

        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(len(evs), 1, "1 in july")

    def test_cest_1(self):
        ical = "test/test_data/cest_every_day_for_one_year.ics"
        start = date(2020, 1, 1)
        end = date(2024, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)

        self.assertEqual(
            len(evs),
            366,
            "366 events in total - one year + 1 (2021-11-11 to 2022-11-11)",
        )

    def test_cest_2(self):
        ical = "test/test_data/cest_every_second_day_for_one_year.ics"
        start = date(2020, 1, 1)
        end = date(2024, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(
            len(evs), 183, "183 events in total - one year (2021-11-11 to 2022-11-11)"
        )

    def test_cest_3(self):
        ical = "test/test_data/cest_with_deleted.ics"
        start = date(2020, 1, 1)
        end = date(2024, 12, 31)

        evs = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(
            len(evs), 3, "3 events in total - 5 events in rrule but 2 deleted"
        )

    def test_transparent(self):
        ical = "test/test_data/transparent.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1, e2] = icalevents.events(file=ical, start=start, end=end)

        self.assertTrue(e1.transparent, "respect transparency")
        self.assertFalse(e2.transparent, "respect opaqueness")

    def test_status_and_url(self):
        ical = "test/test_data/status_and_url.ics"
        start = date(2018, 10, 30)
        end = date(2018, 10, 31)

        [ev1, ev2, ev3, ev4, ev5] = icalevents.events(file=ical, start=start, end=end)
        self.assertEqual(ev1.status, "TENTATIVE")
        self.assertIsNone(ev1.url)
        self.assertEqual(ev2.status, "CONFIRMED")
        self.assertEqual(ev2.url, "https://example.com/")
        self.assertEqual(ev3.status, "CANCELLED")
        self.assertEqual(ev4.status, "CANCELLED")
        self.assertIsNone(ev5.status)

    def test_recurrence_tz(self):
        ical = "test/test_data/recurrence_tz.ics"
        start = datetime(2021, 10, 24, 00, 0, 0, tzinfo=gettz("Australia/Sydney"))
        end = datetime(2021, 10, 26, 00, 0, 0, tzinfo=gettz("Australia/Sydney"))

        [e1] = icalevents.events(file=ical, start=start, end=end)
        expect = datetime(2021, 10, 24, 9, 0, 0, tzinfo=gettz("Australia/Sydney"))
        self.assertEqual(
            e1.start, expect, "Recurring event matches event in ical (Issue #89)"
        )

    def test_attenddees_have_params(self):
        ical = "test/test_data/response.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1] = icalevents.events(file=ical, start=start, end=end)

        self.assertEqual(e1.attendee.params["PARTSTAT"], "DECLINED", "add paarams")
        self.assertEqual(
            e1.attendee, "mailto:calendar@gmail.com", "still is like a string"
        )

    def test_attenddees_can_be_multiple(self):
        ical = "test/test_data/multi_attendee_response.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1] = icalevents.events(file=ical, start=start, end=end)

        self.assertEqual(e1.attendee[0].params["PARTSTAT"], "DECLINED", "add paarams")
        self.assertEqual(
            e1.attendee[0], "mailto:calendar@gmail.com", "we have a list of attendees"
        )
        self.assertEqual(
            e1.attendee[1],
            "mailto:calendar@microsoft.com",
            "we have more than one attendee",
        )

    def test_floating(self):
        ical = "test/test_data/floating.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1, e2] = icalevents.events(file=ical, start=start, end=end)

        self.assertFalse(e1.transparent, "respect transparency")
        self.assertEqual(e1.start.hour, 6, "check start of the day")
        self.assertEqual(e1.end.hour, 14, "check end of the day")
        self.assertFalse(e1.floating, "respect floating time")
        self.assertEqual(e1.start.tzinfo, UTC, "check tz as default utc")

        self.assertTrue(e2.transparent, "respect transparency")
        self.assertEqual(e2.start.hour, 0, "check start of the day")
        self.assertEqual(e2.end.hour, 0, "check end of the day")
        self.assertTrue(e2.floating, "respect floating time")
        self.assertEqual(e2.start.tzinfo, UTC, "check tz as default utc")

    def test_floating_strict(self):
        ical = "test/test_data/floating.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1, e2] = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertFalse(e1.transparent, "respect transparency")
        self.assertEqual(
            e1.start.astimezone(pytz.utc).hour, 6, "check start of the day"
        )
        self.assertEqual(e1.end.astimezone(pytz.utc).hour, 14, "check end of the day")
        self.assertFalse(e1.floating, "respect floating time")
        self.assertEqual(e1.start.tzname(), "CEST", "check tz as specified in calendar")

        self.assertTrue(e2.transparent, "respect transparency")
        self.assertEqual(e2.start, date(2021, 10, 13), "check start of the day")
        self.assertEqual(e2.end, date(2021, 10, 14), "check end of the day")
        self.assertFalse(e2.floating, "dates are not floating floating time")

    def test_non_floating(self):
        ical = "test/test_data/non_floating.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1, e2] = icalevents.events(file=ical, start=start, end=end)

        self.assertFalse(e1.transparent, "respect transparency")
        self.assertEqual(e1.start.hour, 8, "check start of the day")
        self.assertEqual(e1.end.hour, 16, "check end of the day")
        self.assertFalse(e1.floating, "respect floating time")
        self.assertEqual(
            e1.start.tzinfo, gettz("Europe/Zurich"), "check tz as specified in calendar"
        )

        self.assertTrue(e2.transparent, "respect transparency")
        self.assertEqual(e2.start.hour, 0, "check start of the day")
        self.assertEqual(e2.end.hour, 0, "check end of the day")
        self.assertTrue(e2.floating, "respect floating time")
        self.assertEqual(
            e2.start.tzinfo, gettz("Europe/Zurich"), "check tz as specified in calendar"
        )

    def test_non_floating_strict(self):
        ical = "test/test_data/non_floating.ics"
        start = date(2021, 1, 1)
        end = date(2021, 12, 31)

        [e1, e2] = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertFalse(e1.transparent, "respect transparency")
        self.assertEqual(e1.start.hour, 8, "check start of the day")
        self.assertEqual(e1.end.hour, 16, "check end of the day")
        self.assertFalse(e1.floating, "respect floating time")
        self.assertEqual(e1.start.tzname(), "CEST", "check tz as specified in calendar")

        self.assertTrue(e2.transparent, "respect transparency")
        self.assertFalse(e2.floating, "respect floating time")
        self.assertTrue(e2.all_day, "it is an all day event")
        self.assertEqual(e2.start, date(2021, 10, 13), "it is an all day event")
        self.assertEqual(e2.end, date(2021, 10, 14), "it is an all day event")

    def test_recurring_override(self):
        ical = "test/test_data/recurring_override.ics"
        start = date(2021, 11, 23)
        end = date(2021, 11, 24)

        [e0, e1, e2] = icalevents.events(file=ical, start=start, end=end)

        # Here all dates are in utc because the .ics has two timezones and this causes a transformation
        self.assertEqual(e0.start, datetime(2021, 11, 23, 9, 0, tzinfo=UTC))
        self.assertEqual(e1.start, datetime(2021, 11, 23, 10, 45, tzinfo=UTC))
        self.assertEqual(
            e2.start,
            datetime(2021, 11, 23, 13, 0, tzinfo=UTC),
            "moved 1 hour from 12:00 to 13:00",
        )

    def test_recurring_tz_passover_fall(self):
        ical = "test/test_data/recurring_override.ics"
        start = date(2021, 8, 30)
        end = date(2021, 9, 18)

        tz = gettz("Europe/Zurich")
        events = icalevents.events(
            file=ical, start=start, end=end, tzinfo=tz, sort=True, strict=True
        )

        times = [
            ((2021, 8, 30, 8, 0), (2021, 8, 30, 17, 0)),
            ((2021, 8, 30, 9, 30), (2021, 8, 30, 10, 0)),
            ((2021, 8, 31, 10, 0), (2021, 8, 31, 10, 30)),
            ((2021, 8, 31, 10, 15), (2021, 8, 31, 10, 45)),
            ((2021, 8, 31, 13, 15), (2021, 8, 31, 14, 0)),
            ((2021, 9, 1, 9, 0), (2021, 9, 1, 10, 0)),
            ((2021, 9, 1, 9, 30), (2021, 9, 1, 10, 0)),
            ((2021, 9, 1, 12, 0), (2021, 9, 1, 13, 0)),
            ((2021, 9, 2, 10, 0), (2021, 9, 2, 10, 30)),
            ((2021, 9, 3, 8, 0), (2021, 9, 3, 8, 30)),
            ((2021, 9, 3, 9, 0), (2021, 9, 3, 9, 30)),
            ((2021, 9, 3, 9, 30), (2021, 9, 3, 10, 0)),
            ((2021, 9, 3, 15, 30), (2021, 9, 3, 16, 0)),
            ((2021, 9, 3, 17, 30), (2021, 9, 3, 19, 0)),
            ((2021, 9, 6, 8, 0), (2021, 9, 6, 17, 0)),
            ((2021, 9, 6, 9, 30), (2021, 9, 6, 10, 0)),
            ((2021, 9, 7, 9, 0), (2021, 9, 7, 12, 0)),
            ((2021, 9, 7, 9, 0), (2021, 9, 7, 12, 0)),
            ((2021, 9, 7, 10, 0), (2021, 9, 7, 10, 30)),
            ((2021, 9, 8, 9, 30), (2021, 9, 8, 10, 0)),
            ((2021, 9, 8, 12, 0), (2021, 9, 8, 13, 0)),
            ((2021, 9, 9), (2021, 9, 10)),
            ((2021, 9, 9, 10, 0), (2021, 9, 9, 10, 30)),
            ((2021, 9, 9, 11, 0), (2021, 9, 9, 12, 0)),
            ((2021, 9, 10, 8, 0), (2021, 9, 10, 8, 30)),
            ((2021, 9, 10, 9, 30), (2021, 9, 10, 10, 0)),
            ((2021, 9, 10, 17, 30), (2021, 9, 10, 19, 0)),
            ((2021, 9, 13, 9, 30), (2021, 9, 13, 10, 0)),
            ((2021, 9, 14, 9, 0), (2021, 9, 14, 10, 0)),
            ((2021, 9, 14, 10, 0), (2021, 9, 14, 10, 30)),
            ((2021, 9, 14, 15, 0), (2021, 9, 14, 15, 30)),
            ((2021, 9, 15, 9, 30), (2021, 9, 15, 10, 0)),
            ((2021, 9, 16, 10, 0), (2021, 9, 16, 10, 30)),
            ((2021, 9, 16), (2021, 9, 17)),
            ((2021, 9, 17, 9, 30), (2021, 9, 17, 10, 0)),
            ((2021, 9, 17, 17, 30), (2021, 9, 17, 19, 0)),
        ]

        for index, time in enumerate(times):
            self.assertEqual(
                events[index].start,
                date(*time[0]) if len(time[0]) == 3 else datetime(*time[0], tzinfo=tz),
            )
            self.assertEqual(
                events[index].end,
                date(*time[1]) if len(time[1]) == 3 else datetime(*time[1], tzinfo=tz),
            )

        self.assertEqual(len(events), len(times))

    def test_recurring_tz_passover_spring(self):
        ical = "test/test_data/recurring_override.ics"
        start = date(2022, 3, 6)
        end = date(2022, 4, 10)

        tz = gettz("Europe/Zurich")
        events = icalevents.events(
            file=ical, start=start, end=end, tzinfo=tz, sort=True, strict=True
        )

        times = [
            ((2022, 3, 8, 11, 45), (2022, 3, 8, 12, 0)),
            ((2022, 3, 10), (2022, 3, 11)),
            ((2022, 3, 10, 11, 0), (2022, 3, 10, 12, 0)),
            ((2022, 3, 15, 11, 45), (2022, 3, 15, 12, 0)),
            ((2022, 3, 22, 11, 45), (2022, 3, 22, 12, 0)),
            ((2022, 3, 22, 14, 00), (2022, 3, 22, 15, 0)),
            ((2022, 3, 24), (2022, 3, 25)),
            ((2022, 3, 29, 11, 45), (2022, 3, 29, 12, 0)),
            ((2022, 4, 3, 8, 0), (2022, 4, 3, 8, 30)),
            ((2022, 4, 7), (2022, 4, 8)),
        ]

        for index, time in enumerate(times):
            self.assertEqual(
                events[index].start,
                date(*time[0]) if len(time[0]) == 3 else datetime(*time[0], tzinfo=tz),
            )
            self.assertEqual(
                events[index].end,
                date(*time[1]) if len(time[1]) == 3 else datetime(*time[1], tzinfo=tz),
            )

        self.assertEqual(len(events), len(times))

    def test_multi_exdate_same_line(self):
        ical = "test/test_data/multi_exdate_same_line_ms.ics"
        tz = gettz("America/New_York")
        start = date(2022, 3, 1)
        end = date(2022, 5, 1)

        evs = icalevents.events(file=ical, start=start, end=end)

        # parsing starts at 2022-03-01
        self.assertEqual(evs[0].start, datetime(2022, 3, 11, 11, 0, 0, tzinfo=tz))
        # 2022-03-18 is excluded by EXDATE rule
        self.assertEqual(evs[1].start, datetime(2022, 3, 25, 11, 0, 0, tzinfo=tz))
        # 2022-04-01 is excluded by EXDATE rule
        # 2022-04-08 is excluded by EXDATE rule
        self.assertEqual(evs[2].start, datetime(2022, 4, 15, 11, 0, 0, tzinfo=tz))
        self.assertEqual(evs[3].start, datetime(2022, 4, 22, 11, 0, 0, tzinfo=tz))
        self.assertEqual(evs[4].start, datetime(2022, 4, 29, 11, 0, 0, tzinfo=tz))
        # parsing stops at 2022-05-01

    def test_google_2024(self):
        ical = "test/test_data/google_2024.ics"
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        [e1, *events] = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertEqual(e1.start.astimezone(pytz.utc).hour, 6, "starts at 6 utc")
        self.assertEqual(e1.end.astimezone(pytz.utc).hour, 7, "ends at 7 utc")
        self.assertFalse(e1.floating, "respect floating time")
        self.assertEqual(e1.start.tzname(), "CET", "check tz as specified in calendar")

        self.assertEqual(
            events[4].start.astimezone(pytz.utc).hour, 6, "starts at 6 utc"
        )
        self.assertEqual(
            events[5].start.astimezone(pytz.utc).hour,
            5,
            "starts at 5 utc summer time (+2:00)",
        )
        self.assertEqual(
            events[6].start.astimezone(pytz.utc).hour,
            5,
            "starts at 5 utc summer time (+2:00)",
        )

    def test_small_time_frame(self):
        ical = "test/test_data/small_time_frame.ics"

        PT = gettz("America/Los_Angeles")
        start = datetime(month=5, day=9, year=2023, tzinfo=PT)
        end = datetime(month=5, day=9, year=2023, hour=23, tzinfo=PT)

        events = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertEqual(len(events), 1, "1 events")

    def test_recurr_id_dtstart_missmatch(self):
        ical = "test/test_data/recurr_id_dtstart_missmatch.ics"
        tz = gettz("America/New_York")
        start = date(2022, 3, 1)
        end = date(2022, 6, 30)

        evs = icalevents.events(file=ical, start=start, end=end)

        # input file isn't in sorted order, so dates are out of order
        evs.sort(key=lambda ev: (ev.start, ev.sequence))

        self.assertEqual(len(evs), 4)

        # time didn't change, but description/summary did
        self.assertEqual(evs[0].start, datetime(2022, 3, 9, 13, 00, 0, tzinfo=tz))
        self.assertEqual(evs[0].summary, "Recurring Event - Exception 1")

        # time/description/summary changed
        self.assertEqual(evs[1].start, datetime(2022, 4, 13, 10, 30, 0, tzinfo=tz))
        self.assertEqual(evs[1].summary, "Recurring Event - Exception 2")

        # normally scheduled event
        self.assertEqual(evs[2].start, datetime(2022, 5, 11, 13, 00, 0, tzinfo=tz))
        self.assertEqual(evs[2].summary, "Recurring Event")

        # normally scheduled event
        self.assertEqual(evs[3].start, datetime(2022, 6, 8, 13, 00, 0, tzinfo=tz))
        self.assertEqual(evs[3].summary, "Recurring Event")

    def test_per_event_timezone(self):
        ical = "test/test_data/per_event_timezone.ics"
        start = date(2024, 1, 1)
        end = date(2024, 12, 30)

        events = icalevents.events(file=ical, start=start, end=end, strict=True)
        self.assertEqual(
            events[0].start.tzname(), "CET", "check tz as specified in calendar"
        )
        self.assertEqual(
            events[1].start.tzname(), "AWST", "check tz as specified in calendar"
        )

    def test_regression_repeating_events_raise_an_error(self):
        ical = "test/test_data/recurrence_tzinfo.ics"
        start = date(2023, 1, 1)
        end = date(2024, 12, 31)

        events = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertEqual(len(events), 6, "6 events")
        self.assertEqual(events[0].start, date(2023, 11, 27), "first on 27. nov")
        self.assertEqual(events[1].start, date(2023, 12, 4), "second event on 4. dec")
        self.assertEqual(events[2].start, date(2023, 12, 11), "third event on 11. dec")
        self.assertEqual(
            events[3].start,
            date(2024, 1, 1),
            "fourth event on 1. jan - 18. and 25. dec are excluded",
        )
        self.assertEqual(events[4].start, date(2024, 1, 8), "fifth event on 8. jan")

    def test_regression_recurring_events_with_timezones(self):
        # we need to test if all active events are returned, even if they do not fit fully in the defined window
        tz = gettz("Europe/Berlin")
        ical = "test/test_data/recurring_small_window.ics"
        start = datetime(2022, 1, 11, 0, 0, 1, tzinfo=tz)
        end = datetime(2022, 1, 11, 8, 0, 1, tzinfo=tz)

        events = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].end.hour, 8)

    def test_regression_offset_aware_comparison(self):
        ical = "test/test_data/regression_offset_native.ics"
        start = datetime(2020, 7, 1)
        end = datetime(2020, 7, 31)

        events = icalevents.events(file=ical, start=start, end=end, strict=True)

        self.assertEqual(len(events), 1)
