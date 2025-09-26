import unittest
from pathlib import Path

import icalevents.icaldownload


class ICalDownloadTests(unittest.TestCase):
    def test_apple_data_fix(self):
        data = """
DTSTART:18831118T120702
RDATE;VALUE=DATE-TIME:18831118T120702
TZNAME:PST
TZOFFSETFROM:+5328
TZOFFSETTO:-0800
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19180331T020000
        """
        expected = """
DTSTART:18831118T120702
RDATE;VALUE=DATE-TIME:18831118T120702
TZNAME:PST
TZOFFSETFROM:+0053
TZOFFSETTO:-0800
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:19180331T020000
        """
        res = icalevents.icaldownload.apple_data_fix(data)
        self.assertEqual(res, expected, "fix invalid TZOFFSETFROM")

    def test_apple_url_fix(self):
        data = "webcal://blah.blub/webcal/"
        expected = "http://blah.blub/webcal/"

        res = icalevents.icaldownload.apple_url_fix(data)
        self.assertEqual(res, expected, "fix url protocol")

    def test_apple_url_fix_right(self):
        data = "https://blah.blub/webcal/"

        res = icalevents.icaldownload.apple_url_fix(data)
        self.assertEqual(res, data, "no change")

    def test_data_from_file_google(self):
        file = "test/test_data/basic.ics"
        result = "test/test_data/basic_content.txt"

        expected = None

        with open(result, mode="r", encoding="utf-8") as f:
            expected = f.read()

        for kind, input_file in [("str", file), ("Path", Path(file))]:
            with self.subTest(kind):
                content = icalevents.icaldownload.ICalDownload().data_from_file(
                    input_file
                )

                self.assertEqual(
                    expected, content, "content form iCal file, Google format"
                )

    def test_data_from_file_apple(self):
        file = "test/test_data/icloud.ics"
        result = "test/test_data/icloud_content.txt"

        expected = None

        with open(result, mode="r", encoding="utf-8") as f:
            expected = f.read()

        content = icalevents.icaldownload.ICalDownload().data_from_file(
            file, apple_fix=True
        )

        self.assertEqual(expected, content, "content form iCal file, Apple format")

    def test_empty_file(self):
        empty_ical = "test/test_data/empty.ics"

        with self.assertRaises(OSError) as cm:
            icalevents.icaldownload.ICalDownload().data_from_file(empty_ical)

        self.assertEqual(
            str(cm.exception),
            "File test/test_data/empty.ics is not readable or is empty!",
        )
