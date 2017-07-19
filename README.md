# iCalEvents

Simple Python 3 library to download, parse and query iCal sources.

## Build info

[![Build Status](https://travis-ci.org/irgangla/icalevents.svg?branch=master)](https://travis-ci.org/irgangla/icalevents)

https://travis-ci.org/irgangla/icalevents

[![codecov](https://codecov.io/gh/irgangla/icalevents/branch/master/graph/badge.svg)](https://codecov.io/gh/irgangla/icalevents)

https://codecov.io/gh/irgangla/icalevents

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
