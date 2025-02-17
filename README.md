# iCalEvents

Simple Python 3 library to download, parse and query iCal sources.

[![PyPI version](https://badge.fury.io/py/icalevents.svg)](https://badge.fury.io/py/icalevents)[![Jazzband](https://jazzband.co/static/img/badge.svg)](https://jazzband.co/)

## Build info

last push: [![Run pytest](https://github.com/jazzband/icalevents/actions/workflows/tests.yml/badge.svg)](https://github.com/jazzband/icalevents/actions/workflows/tests.yml)

master: [![Run pytest](https://github.com/jazzband/icalevents/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/jazzband/icalevents/actions/workflows/tests.yml?query=branch%3Amaster++)

## Documentation

https://icalevents.readthedocs.io/en/latest/

## Usage

### iCloud:

```python

from icalevents.icalevents import events

es  = events(<iCloud URL>, fix_apple=True)
```

### Google:

```python

from icalevents.icalevents import events

es  = events(<Google Calendar URL>)
```

# Contributing

You will need [poetry](https://github.com/python-poetry/poetry) and [pre-commit](https://pre-commit.com/index.html) installed and than run.

```bash
pre-commit install
```

Happy contributing!
