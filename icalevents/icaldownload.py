"""
Downloads an iCal url or reads an iCal file.
"""
from httplib2 import Http


def apple_data_fix(content):
    """
    Fix Apple tzdata bug.

    :param content: content to fix
    :return: fixed content
    """
    return content.replace('TZOFFSETFROM:+5328', 'TZOFFSETFROM:+0053')


def apple_url_fix(url):
    """
    Fix Apple URL.

    :param url: URL to fix
    :return: fixed URL
    """
    if url.startswith("webcal://"):
        url = url.replace('webcal://', 'http://', 1)
    return url


class ICalDownload:
    """
    Downloads or reads and decodes iCal sources.
    """
    def __init__(self, http=None, encoding='utf-8'):
        # default http connection to use
        if http is None:
            try:
                http = Http('.cache')
            except (PermissionError, OSError):
                # Cache disabled if no write permission in working directory
                http = Http()

        self.http = http
        self.encoding = encoding

    def data_from_url(self, url, apple_fix=False):
        """
        Download iCal data from URL.

        :param url: URL to download
        :param apple_fix: fix Apple bugs (protocol type and tzdata in iCal)
        :return: decoded (and fixed) iCal data
        """
        if apple_fix:
            url = apple_url_fix(url)

        _, content = self.http.request(url)

        if not content:
            raise ConnectionError('Could not get data from %s!' % url)

        return self.decode(content, apple_fix=apple_fix)

    def data_from_file(self, file, apple_fix=False):
        """
        Read iCal data from file.

        :param file: file to read
        :param apple_fix: fix wrong Apple tzdata in iCal
        :return: decoded (and fixed) iCal data
        """
        with open(file, mode='rb') as f:
            content = f.read()

        if not content:
            raise IOError("File %f is not readable or is empty!" % file)

        return self.decode(content, apple_fix=apple_fix)

    def data_from_string(self, string_content, apple_fix=False):
        if not string_content:
            raise IOError("String content is not readable or is empty!")

        return self.decode(string_content, apple_fix=apple_fix)

    def decode(self, content, apple_fix=False):
        """
        Decode content using the set charset.

        :param content: content do decode
        :param apple_fix: fix Apple txdata bug
        :return: decoded (and fixed) content
        """
        content = content.decode(self.encoding)
        content = content.replace('\r', '')

        if apple_fix:
            content = apple_data_fix(content)

        return content
