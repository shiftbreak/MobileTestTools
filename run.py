#!/usr/bin/env python3
import sqlite3
import magic
import os
from pathlib import Path
import plistlib
import biplist
import sys
import argparse
import json
import pprint
from BinaryCookieReader import process

permissions = {
    "NSPhotoLibraryAddUsageDescription": "Your app adds photos to the user's photo library",
    "NSPhotoLibraryUsageDescription": "Your app accesses the user's photo library",
    "NSCameraUsageDescription": "Your app uses the device camera",
    "NSLocationAlwaysUsageDescription": "Your app uses location services all the time",
    "NSLocationWhenInUseUsageDescription": "Your app uses location services only when the app is running",
    "NSLocationUsageDescription": "DEPRECATED: Update to one of the above instead",
    "NSContactsUsageDescription": "Your app uses the address book",
    "NSCalendarsUsageDescription": "Your app uses or modifies the user's calendar information",
    "NSRemindersUsageDescription": "Your app creates reminders in the Reminders app",
    "NSHealthShareUsageDescription": "Your app uses data from the Health app",
    "NSHealthUpdateUsageDescription": "Your app provides health information to the Health app",
    "NFCReaderUsageDescription": "Your app uses the NFC reader",
    "NSBluetoothPeripheralUsageDescription": "Your app works with Bluetooth devices",
    "NSMicrophoneUsageDescription": "Your app uses the device microphone",
    "NSSiriUsageDescription": "Your app provides a SiriKit Intent",
    "NSSpeechRecognitionUsageDescription": "Your app uses speech recognition",
    "NSMotionUsageDescription": "Your app uses the device motion tracking hardware",
    "NSVideoSubscriberAccountUsageDescription": "(tvOS only) your app uses the video subscriber account",
    "NSAppleMusicUsageDescription": "Your app uses Apple Music integration",
    "NSFaceIDUsageDescription": "Your app uses FaceID"
}


def get_ios_permissions(infoPlistIn):
    print("==================== " + str(infoPlistIn) + " ====================")
    out = []
    with open(infoPlistIn, 'r') as f:
        text = f.read()
        for f in permissions:
            if f in text:
                out.append([f, permissions[f]])
    lens = []
    for col in zip(*out):
        lens.append(max([len(v) for v in col]))
    format = "  ".join(["{:<" + str(l) + "}" for l in lens])
    for row in out:
        print(format.format(*row))
    print("\n\n")


def do_sqlite(f):
    print("==================== " + str(f) + " ====================")

    conntemp = sqlite3.connect(':memory:')
    conn = sqlite3.connect(str(f))
    for line in conn.iterdump():
        try:
            conntemp.execute(line)
        except Exception:
            pass

    conntemp.commit()
    c = conntemp.cursor()
    res = c.execute("PRAGMA database_list;")
    print(res.fetchall())
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
        results = c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for row in results:
            table_name = row[0]
            results2 = c.execute(f"SELECT * from {table_name}")
            for rw in results2:
                print(rw)
    conntemp.close()


def formatData(data_in):
    pp = pprint.PrettyPrinter()
    try:
        return json.dumps(data_in, indent=4)
    except Exception:
        try:
            return pp.pformat(data_in)
        except Exception:
            return data_in
    return data_in


def do_plist(f, binary=False):
    print("==================== " + str(f) + " ====================")
    try:
        with open(f, 'rb') as fp:
            try:
                data = plistlib.load(fp)
            except plistlib.InvalidFileException:
                data = biplist.readPlist(fp)
            data_formatted = formatData(data)
            print(data_formatted)
            print("\n\n")
    except Exception as e:
        print(e)


def decode_keychain(f_in):
    k = json.load(open(f_in))
    for l in k:
        i_out = []
        for i in l:
            if i == 'dataHex':
                decoded = bytes.fromhex(l[i])
                try:
                    decoded = biplist.readPlistFromString(decoded)
                    l[i] = formatData(decoded)
                except:
                    l[i] = formatData(decoded)
    print(formatData(k))


def weak_keychain(f_in):
    k = json.load(open(f_in))
    for l in k:
        if l['accessible_attribute'] != "kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly" and l['accessible_attribute'] != "kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly":
            for i in l:
                if i == 'dataHex':
                    decoded = bytes.fromhex(l[i])
                    try:
                        decoded = biplist.readPlistFromString(decoded)
                        l[i] = formatData(decoded)
                    except:
                        l[i] = formatData(decoded)
            print(formatData(l))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IOS and Android data processor (by Shiftbreak)')

    parser.add_argument('-d', '--directory', dest='directory', help='Specify name of the directory to parse')
    parser.add_argument('-s', '--list-sqlite', action='store_true', dest='list_sqlite', help='List SQLite Databases.')
    parser.add_argument('-S', '--sqlite', action='store_true', dest='do_sqlite', help='Process SQLite Databases.')
    parser.add_argument('-B', '--binarycookies', action='store_true', dest='do_bincook', help='Process BinaryCookies.')
    parser.add_argument('-p', '--list-plist', action='store_true', dest='list_plist', help='List Binary and non-binary plists.')
    parser.add_argument('-P', '--plist', action='store_true', dest='do_plist', help='Process Binary and non-binary plists.')
    parser.add_argument('-i', '--image', action='store_true', dest='do_image', help='List images.')
    parser.add_argument('-k',  '--keychain', dest='keychain', help='Decode JSON Keychain dump drom objection.')
    parser.add_argument('-K',  '--weak-keychain', dest='keychain2', help='Print Keychain items which use weak protection')

    parser.add_argument('-m', '--list-mime', action='store_true', dest='do_mime', help='List Mime Types for all files.')
    parser.add_argument('-u', '--unique-mime', action='store_true', dest='do_umime', help='List Unique mime types')
    parser.add_argument('-z',  '--info-plist', dest='info_plist', help='Get Info.Plist permissions.')
    parser.add_argument('-x', '--ignore-strings', dest='ignore_strings', action='store_true', help='Ignore files in the strings directory ./Caches/[*].strings/en/')
    args = parser.parse_args()

    if args.keychain:
        decode_keychain(args.keychain)
        exit(0)

    if args.keychain2:
        weak_keychain(args.keychain2)
        exit(0)

    if args.info_plist:
        get_ios_permissions(args.info_plist)
        exit(0)

    result = list(Path(args.directory).rglob("*"))
    if args.do_umime:
        mimes = []
        for f in result:
            if not os.path.isdir(f):
                m = magic.from_file(str(f), mime=True)
                m2 = magic.from_file(str(f), mime=False)
                mimes.append(m + " " + m2)
        um = sorted(set(mimes))
        for m in um:
            print(m)
        exit(0)


    for f in result:
        if not os.path.isdir(f):
            b = open(f,"rb").read(2048)
            m = magic.from_buffer(b, mime=True)
            m2 = magic.from_buffer(b, mime=False)
            if args.do_sqlite and m == 'application/x-sqlite3':
                do_sqlite(f)
            if args.list_sqlite and m == 'application/x-sqlite3':
                print(f)
            if args.do_mime:
                print(str(f) + " - " + m + " " + m2)
            if args.do_plist:
                if args.ignore_strings:
                    if ".strings/en" in str(f):
                        continue
                if str(f).lower().endswith(".plist") and 'Apple binary property list' != m2:
                    do_plist(f, binary=False)
                if 'Apple binary property list' == m2:
                    do_plist(f, binary=True)
            if args.list_plist:
                if str(f).lower().endswith(".plist") and 'Apple binary property list' != m2:
                    print(f)
                if 'Apple binary property list' == m2:
                    print(f)
            if args.do_image:
                if 'image' in m + m2:
                    print(f)
            if args.do_bincook:
                if "Cookies.binarycookies" in str(f):
                    process(f)
