from icalevents.icalevents import events


if __name__ == '__main__':
    with open('calendars.txt', mode='r', encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                break

            name, url = line.split(maxsplit=1)
            name = name.strip()
            url = url.strip()

            fix_apple = False
            if name == 'icloud':
                fix_apple = True

            es  = events(url, fix_apple=fix_apple)

            print("%d event found for URL %s" % (len(es), url))

            for e in es:
                print(e)
