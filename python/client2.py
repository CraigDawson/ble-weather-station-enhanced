#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Created : Wed 01 Aug 2018 05:53:06 PM EDT
# Modified: Tue 07 Aug 2018 07:17:47 AM EDT

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

import better_exceptions  # noqa: F401
from icecream import ic


def baseUnixTimestamp():
    return '%s |> ' % datetime.now()


def baseCreateRotatingLog():
    """
    Creates a rotating log with output
    file based on this file's name
    """
    base = os.path.basename(__file__)
    root = os.path.splitext(base)[0]
    logFile = '.'.join([root, 'log'])

    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)

    # add a rotating handler
    handler = RotatingFileHandler(
        logFile,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5)
    logger.addHandler(handler)

    return logger


def baseDebugInfoOut(s):
    """
    icecream output function into a
    rotating log with time stamps and
    to STDOUT
    """
    global log

    log.info(s)
    print(s)


# Configure icecream with time stamp and output to
# file and screen
ic.configureOutput(prefix=baseUnixTimestamp, outputFunction=baseDebugInfoOut)

# Create log file that icecream will output to
log = baseCreateRotatingLog()


def main():
    try:
        fn = sys.argv[1]
    except IndexError:
        print('Usage: {} file_name'.format(sys.argv[0]))
        sys.exit(1)

    ic(fn)

    import requests

    url = "http://localhost:5000"
    # url = "http://ryoko3.local:5000"

    print("Files on Server:")
    response = requests.get(
        '{}/filesBarriersEngagingTelecomRelating'.format(url))
    ic(response.status_code)
    ic(response.json())

    # http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file

    print('-' * 23)

    print("Uploading file: {}".format(fn))
    fin = open(fn, 'rb')
    files = {'file': fin}
    try:
        r = requests.post(
            '{}/uploadAlgeriaFreedomBraceletWorlds'.format(url), files=files)
        ic(r.status_code)
    finally:
        fin.close()


if __name__ == '__main__':
    main()
