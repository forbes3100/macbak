#!/usr/bin/env python3
#
# icdrivebak -- Force all iCloud Drive files to be downloaded, for backup
#
# Copyright (C) 2023 Scott Forbes
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os, sys
import os.path as path
import shutil
import urllib.parse
import objc_util

home = os.path.expanduser("~")
icloud = home + "/Library/Mobile Documents/"
icloud_docs = icloud + "com~apple~CloudDocs/"

have_shown_header = False
download_count = 0
fail_count = 0
verbose = 0

icloud_app_dir_renames = {
    "bbedit": "BBEdit",
    "mobilegarageband": "GarageBand for iOS",
}

ignored_files = (".DS_Store", ".Trash")


def force_download(f_path, f):
    global download_count, fail_count
    url = objc_util.nsurl(
        'file://' + urllib.parse.quote(f_path.encode('utf8'))
    )
    file_mgr = objc_util.ObjCClass('NSFileManager').defaultManager()
    ret = file_mgr.startDownloadingUbiquitousItemAtURL_error_(url, None)
    if ret:
        print(f"  {f}")
        download_count += 1
    else:
        print(f"  *** FAILED to download {f}")
        fail_count += 1


def force_download_dir(cloud_dir, header=None, include_dirs=True):
    global have_shown_header
    for f in os.listdir(cloud_dir):
        if f not in ignored_files:
            p = cloud_dir + f
            if path.isdir(p):
                force_download_dir(p + "/", header)
            else:
                name, ext = path.splitext(f)
                if name[0] == "." and ext == ".icloud":
                    if (header is not None) and (not have_shown_header):
                        print(header)
                        have_shown_header = True
                    force_download(p, name[1:])


def main():
    global have_shown_header, download_count, fail_count

    if verbose >= 1:
        print("Force download of iCloud Documents folder")
    force_download_dir(icloud_docs, include_dirs=False)

    if verbose >= 1:
        print("Force download of app folders")
    have_shown_header = False
    for a in os.listdir(icloud):
        d = icloud + a + "/Documents/"
        if path.exists(d):
            files = os.listdir(d)
            if len(files) > 0:
                name = a.split("~")[-1]
                name = icloud_app_dir_renames.get(name, name)
                force_download_dir(d, f"app {name}/")

    if download_count > 0 or fail_count > 0:
        if download_count > 0:
            s = 's' if download_count > 1 else ''
            print(f"Started {download_count} file{s} downloading.")
        if fail_count > 0:
            print(f" {fail_count} files failed to download.")
    else:
        print("All downloaded.")


if __name__ == "__main__":
    main()
