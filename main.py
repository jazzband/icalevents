from icalevents.icalevents import events_async, latest_events, all_done
from time import sleep


if __name__ == '__main__':
    keys = []

    with open('calendars.txt', mode='r', encoding='utf-8') as f:
        counter = 1

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


            key = "req_%d" % counter
            counter += 1
            keys.append(key)
            events_async(key, url, fix_apple=fix_apple)



    while keys:
        print("%d request running." % len(keys))

        for k in keys[:]:
            if all_done(k):
                print("Request %s finished." % k)
                keys.remove(k)

                es = latest_events(k)

                for e in es:
                    print(e)

        sleep(2)
