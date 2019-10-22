import urllib.request
import datetime
import time
import sys

while True:
    page = urllib.request.urlopen('http://127.0.0.1')
    now = datetime.datetime.now().time()
    code = int(page.getcode())
    if code == 200:
        content = page.read().decode('UTF-8')
        print(str(now) + " " + content, end=' ')
        sys.stdout.flush()
        with open('log.txt', 'a') as log:
            log.write(str(now) + " " + content + "\n")
    else:
        print(str(now) + " " + code)
    print()
