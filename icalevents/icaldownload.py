"""
Downloads an iCal url or reads an iCal file.
"""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

import urllib3


def apple_data_fix(content: str) -> str:
    """
    Fix Apple tzdata bug.

    :param content: content to fix
    :return: fixed content
    """
    return content.replace("TZOFFSETFROM:+5328", "TZOFFSETFROM:+0053")


def apple_url_fix(url: str) -> str:
    """
    Fix Apple URL.

    :param url: URL to fix
    :return: fixed URL
    """
    if url.startswith("webcal://"):
        url = url.replace("webcal://", "http://", 1)
    return url


class ICalDownload:
    """
    Downloads or reads and decodes iCal sources.
    """

    def __init__(self, http: urllib3.PoolManager | None = None) -> None:
        # default http connection to use
        if http is None:
            http = urllib3.PoolManager()

        self.http = http

    def data_from_url(self, url: str, apple_fix: bool = False) -> str:
        """
        Download iCal data from URL.

        :param url: URL to download
        :param apple_fix: fix Apple bugs (protocol type and tzdata in iCal)
        :return: decoded (and fixed) iCal data
        """
        if apple_fix:
            url = apple_url_fix(url)

        response = self.http.request("GET", url)

        if not response.data:
            raise ConnectionError("Could not get data from %s!" % url)

        encoding = "utf-8"
        if content_type := response.headers.get("content-type"):
            with suppress(AttributeError, IndexError):
                encoding = content_type.split("charset=")[1]

        return self.decode(response.data, encoding, apple_fix=apple_fix)

    def data_from_file(self, file: str | Path, apple_fix: bool = False) -> str:
        """
        Read iCal data from file.

        :param file: file to read
        :param apple_fix: fix wrong Apple tzdata in iCal
        :return: decoded (and fixed) iCal data
        """
        with open(file, mode="rb") as f:
            content = f.read()

        if not content:
            raise OSError("File %s is not readable or is empty!" % file)

        return self.decode(content, apple_fix=apple_fix)

    def data_from_string(
        self, string_content: bytes | str, apple_fix: bool = False
    ) -> str:
        if not string_content:
            raise OSError("String content is not readable or is empty!")

        return self.decode(string_content, apple_fix=apple_fix)

    @staticmethod
    def decode(
        content: bytes | str, encoding: str = "utf-8", apple_fix: bool = False
    ) -> str:
        """
        Decode content using the set charset.

        :param content: content do decode
        :param encoding: the used charset for decoding the content
        :param apple_fix: fix Apple txdata bug
        :return: decoded (and fixed) content
        """
        if isinstance(content, bytes):
            content = content.decode(encoding)
        content = content.replace("\r", "")

        if apple_fix:
            content = apple_data_fix(content)

        return content
