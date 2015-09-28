#!/usr/bin/env python

'''Downloads all the backgrounds that are currently on
the chromecast landing page at the highest quality possible,
at any given time there are only up to ~100 and they change
on each page load. Meaning that each time you run the script
additional backgrounds may be found.
'''

from __future__ import print_function
import argparse
from os import path
from os import makedirs
import requests
import re
import sqlite3 as sql
try: # Py3
    from urllib.parse import unquote
except ImportError: # Py2
    from urllib import unquote


__app_name__ = 'chromecast-background-downloader'
__author__ = 'mrasband'


def cache_dir():
    '''Background cache directory'''
    try:
        from appdirs import user_cache_dir
        return user_cache_dir(__app_name__, __author__)
    except ImportError:
        return './'


def data_dir():
    '''Background storage location'''
    try:
        from appdirs import user_data_dir
        return user_data_dir(__app_name__, __author__)
    except ImportError:
        return './backgrounds'


def create_dir_if_not_exists(dirname):
    '''Create a directory if it doesn't exist'''
    if not path.exists(dirname):
        makedirs(dirname)
    return dirname


# Chromecast Page as seen on a chromecast device
BASE_URL = 'https://clients3.google.com/cast/chromecast/home/v/c9541b08'


def main():
    parser = argparse.ArgumentParser(
        description="Download high quality Chromecast images.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--cache-dir',
        action='store',
        default=cache_dir(),
        help='Directory to save the backgrounds cache.')
    parser.add_argument(
        '--backgrounds-dir',
        action='store',
        default=data_dir(),
        help='Directory where backgrounds will be saved.')
    args = parser.parse_args()

    create_dir_if_not_exists(args.backgrounds_dir)
    create_dir_if_not_exists(args.cache_dir)

    print('Saving backgrounds to', args.backgrounds_dir)

    conn = sql.connect(path.join(args.cache_dir, 'chromecast-backgrounds.sqlite3'))
    with conn:
        conn.execute('CREATE TABLE IF NOT EXISTS backgrounds(id INTEGER PRIMARY KEY AUTOINCREMENT, original_url TEXT UNIQUE, updated_url TEXT, downloaded INTEGER DEFAULT 0)')

    r = requests.get(BASE_URL)
    r.raise_for_status()

    # The raw body has \x22 instead of "
    body_text = re.sub(r'\\x22', '"', r.text)
    # Urls have back slashes escaping forwards and newlines
    body_text = re.sub(r'\\|\\n', '', body_text)
    # Locate the sub-string we care about, that actually contains the background urls.
    json_parse = re.search(r'JSON.parse\(\'([^)]+)', body_text)
    if json_parse:
        cur = conn.cursor()

        # I've had issues with anything other than JPGs in the past, we are just
        # ignoring anything that isn't a jpg (<1% estimated)
        for it in re.finditer(r'"(https://[^"]+?\.jpg)"', json_parse.group(1)):
            original_url = it.group(1)
            url = unquote(original_url).replace('s1280-w1280-c-h720', 's2560')
            filename = path.basename(url)

            cur.execute("SELECT * from backgrounds where original_url=? LIMIT 1", (it.group(1),))
            existing = cur.fetchone()
            background_id = None
            if existing and existing[3]:
                print('Skipping duplicate background:', filename)
                continue
            elif not existing:
                cur.execute("INSERT INTO backgrounds(original_url, updated_url, downloaded) VALUES (?, ?, ?)", (original_url, url, 0))
                background_id = cur.lastrowid
            else:
                background_id = existing[0]

            r = requests.get(url, stream=True)
            with open(path.join(args.backgrounds_dir, filename), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                print('Saved new background:', filename)
            cur.execute("UPDATE backgrounds SET downloaded=? WHERE id=?", (1, background_id))
        conn.commit()
    else:
        print('Unable to find backgrounds, the page may have changed.')


if __name__ == '__main__':
    main()