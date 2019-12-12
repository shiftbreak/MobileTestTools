#!/usr/bin/env python3
import sqlite3
import magic
import os
from pathlib import Path
import plistlib
import argparse


def do_sqlite(f):

    conntemp = sqlite3.connect(':memory:')
    conn = sqlite3.connect(str(f))
    for line in conn.iterdump():
        try:
            conntemp.execute(line)
        except Exception:
            pass

    conntemp.commit()
    c = conntemp.cursor()
    try:
        results = c.execute("SELECT request_object, response_object FROM cfurl_cache_blob_data")
        for row in results:
            print("========================================")
            request = row[0]
            response = row[1]
            a = plistlib.loads(request)
            b = plistlib.loads(response)

            headers = a['Array'][19]
            url = a['Array'][1]['_CFURLString']
            method = a['Array'][18]
            print(method + " " + url)
            for h in headers:
                if h != "__hhaa__":
                    print(h + " " + headers[h])

            print("\n\n")
            headers = b['Array'][4]
            for n in headers:
                if n != "__hhaa__":
                    print(n + " " + headers[n])
            print("\n\n\n")
    except sqlite3.OperationalError:
        pass
    conntemp.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IOS and Android data processor (by Shiftbreak)')

    parser.add_argument('-d', '--directory', dest='directory', help='Specify name of the directory to parse')
    parser.add_argument('-s', '--sqlite', action='store_true', dest='do_sqlite', help='Process SQLite Databases.')
    args = parser.parse_args()

    result = list(Path(args.directory).rglob("*"))
    for f in result:
        if not os.path.isdir(f):
            m = magic.from_file(str(f), mime=True)
            if args.do_sqlite and m == 'application/x-sqlite3':
                do_sqlite(f)
