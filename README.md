# iCalEvents

Simple Python 3 library to download, parse and query iCal sources.

[![Jazzband](https://jazzband.co/static/img/badge.svg)](https://jazzband.co/)

## Build info

![run pytest](https://github.com/jazzband/icalevents/actions/workflows/python-test.yml/badge.svg)

See Github Action [run pytest](https://github.com/jazzband/icalevents/actions)

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
