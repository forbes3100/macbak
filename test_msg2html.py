#!/usr/bin/env python3
#
# test_msg2html -- Unit tests for msg2html
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

import os
import os.path as path
import shutil
import unittest
import json
import sqlite3

# import subprocess
import msg2html

db_name = "test_msg.db"
att_dir = "TestAttachments/"
lib_dir = "~/Library/Messages/"
ext = "TestExtern/Messages/Attachments/"

# fmt: off
test_messages = [
    # guid, text,       handle_id, service, date,    from_me, cache_has_att
    ("100", "Test message 1a.\ufffcAfter.",
                        1, "SMS", 652552877020974848, 0, 1),
    ("101", "Test message 2.", 5, "iMessage", 652552877020975848, 1, 0),
    ("102", "Test message 3.\ufffc", 2, "iMessage", 652552877020976848, 0, 1),
    ("103", "Test message 4.\ufffcAnd bubbles\ufffc",
                        5, "iMessage", 652552876403117312, 0, 1),
]
# fmt: on

test_handles = [
    # rowid, id
    (1, "10"),
    (2, "11"),
    (5, "12"),
]

test_attachments = [
    # rowid, created_date, filename, mime_type, transfer_name
    (
        1,
        652552877020936812,
        "~/Library/Messages/TestAttachments/1e/27/at_1_ABCD/cat.jpeg",
        "image/jpeg",
        "cat.jpeg",
    ),
    (
        2,
        652552876503119324,
        "~/Library/Messages/TestAttachments/1e/27/at_0_ABCD/watermellon.jpeg",
        "image/jpeg",
        "watermellon.jpeg",
    ),
    (3, 652552875012345032, None, "image/jpeg", "cat_white2.jpeg"),
    (
        4,
        652552876403117312,
        "~/Library/Messages/TestAttachments/05/ef/at_0_1234_5678/HEART.HEIC",
        "image/heic",
        "HEART.HEIC",
    ),
    (
        5,
        652552876503119330,
        "~/Library/Messages/TestAttachments/05/ef/at_1_1234_5678/bubbles.m4a",
        "audio/x-m4a",
        "bubbles.m4a",
    ),
]

test_message_attachment_joins = [
    # message_id, attachment_id
    (1, 2),
    (3, 3),
    (4, 4),
    (4, 5),
]


class TestMsgToHtml(unittest.TestCase):
    def setUp(self):
        if os.path.exists(db_name):
            os.remove(db_name)
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE message (
             ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
             guid TEXT UNIQUE NOT NULL,
             text TEXT,
             handle_id INTEGER DEFAULT 0,
             service TEXT,
             date INTEGER,
             is_from_me INTEGER DEFAULT 0,
             cache_has_attachments INTEGER DEFAULT 0
            );"""
        )
        for message in test_messages:
            cur.execute(
                "INSERT INTO message (guid, text, handle_id, service,"
                " date, is_from_me, cache_has_attachments)"
                " VALUES (?,?,?,?,?,?,?)",
                message,
            )
        conn.commit()

        cur.execute(
            """
            CREATE TABLE handle (
             ROWID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
             id TEXT NOT NULL
            );"""
        )
        conn.commit()
        for handle in test_handles:
            cur.execute("INSERT INTO handle (rowid, id) VALUES (?,?)", handle)

        cur.execute(
            """
            CREATE TABLE attachment (
             ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
             created_date INTEGER DEFAULT 0,
             filename TEXT,
             mime_type TEXT,
             transfer_name TEXT
            );"""
        )
        for att in test_attachments:
            cur.execute("INSERT INTO attachment VALUES (?,?,?,?,?)", att)
        conn.commit()

        cur.execute(
            """
            CREATE TABLE message_attachment_join (
            message_id INTEGER REFERENCES message (ROWID),
            attachment_id INTEGER REFERENCES attachment (ROWID), 
            UNIQUE(message_id, attachment_id)
            );"""
        )
        for maj in test_message_attachment_joins:
            cur.execute(
                "INSERT INTO message_attachment_join VALUES (?,?)", maj
            )
        conn.commit()
        conn.close()

        # build expected HTML lines from table fields
        msg1 = test_messages[0][1].split("\ufffc")
        self.msg1a = f"<p>{msg1[0]}</p>\n"
        self.msg1b = f"<p>{msg1[1]}</p>\n"
        self.msg2 = f'<p class="me">{test_messages[1][1]}</p>\n'
        msg3 = test_messages[2][1].split("\ufffc")
        self.msg3 = f"<p>{msg3[0]}</p>\n"
        att1 = test_attachments[1]
        fn1 = att1[2][19:]
        self.info1 = f'<p class="j">{fn1}</p>'
        self.img1 = f'<img src="{fn1}" width="300">'
        att3 = test_attachments[3]
        fn3 = att3[2][19:]
        self.heic_jpeg = path.splitext(fn3)[0] + ".jpeg"
        self.img_heic_jpeg = f'<img src="{self.heic_jpeg}" width="300">'
        att4 = test_attachments[4]
        self.audio = att4[2][19:]
        self.src_audio = (
            "<audio controls>\n"
            f'<source src="{self.audio}" type="audio/x-m4a">\n'
            "Your browser does not support the audio tag.\n"
            "</audio>"
        )

    def convert_one_year(self, debug):
        year = 2021
        html_name = f"test_{year}_{debug}"
        html_file = html_name + ".html"

        # insure beforehand created files are not present
        if path.exists(html_file):
            ##print(f'\nDeleting previous {html_name}')
            os.remove(html_file)
        self.assertFalse(path.exists(html_file))
        if os.path.exists(self.heic_jpeg):
            ##print(f'\nDeleting previous {self.heic_jpeg}')
            os.remove(self.heic_jpeg)
        self.assertFalse(path.exists(self.heic_jpeg))

        ext_att_dir = None
        msg2html.debug = debug
        msg2html.convert(db_name, att_dir, year, ext_att_dir, html_name)
        self.assertTrue(path.exists(html_file))
        with open(html_file, "r") as f:
            text = f.read()

        self.assertIn("<html>\n<head>\n<style>", text)
        self.assertIn("</body>\n</html>", text)

        self.assertIn(self.msg1a, text)
        self.assertIn(self.msg1b, text)
        self.assertIn(self.msg2, text)
        self.assertIn(self.msg3, text)
        index_msg1a = text.index(self.msg1a)
        index_msg1b = text.index(self.msg1b)
        index_msg2 = text.index(self.msg2)
        self.assertTrue(index_msg1a < index_msg1b)
        self.assertTrue(index_msg1b < index_msg2)

        self.assertIn(self.img1, text)
        index_img1 = text.index(self.img1)
        self.assertTrue(index_msg1a < index_img1)
        self.assertTrue(index_img1 < index_msg1b)

        att1 = test_attachments[1]
        att1_dbg = (
            f'<p class="j">att 1,0,2021-09-05 09:41:17,100:<br>'
            f"652552876503119324,{att1[2]},{att1[3]},{att1[4]}</p>"
        )
        if debug > 0:
            self.assertIn(att1_dbg, text)
        else:
            self.assertNotIn(att1_dbg, text)
            self.assertIn(self.info1, text)

        self.assertTrue(path.exists(self.heic_jpeg), self.heic_jpeg)
        self.assertIn(self.img_heic_jpeg, text)

        self.assertTrue(path.exists(self.audio), self.audio)
        self.assertIn(self.src_audio, text)

    def test_1_one_year_dbg(self):
        self.convert_one_year(3)

    def test_2_one_year_no_dbg(self):
        self.convert_one_year(0)

    def test_3_external(self):
        cat2_dir = "bf/15/02BD53C0-4AB0-41B9-89E7-156935839169/"
        cat2_name = test_attachments[2][4]
        cat2_path = f"{att_dir}{cat2_dir}{cat2_name}"
        year = 2021
        msg2html.debug = 3

        # insure beforehand that ext files not present in local db
        if path.exists(cat2_path):
            ##print(f'\nDeleting previous {cat2_path}')
            os.remove(cat2_path)
        self.assertFalse(path.exists(cat2_path))

        # do a regular conversion and check that ext images are not there
        html_name = f"test_{year}_post_extern"
        ext_att_dir = None
        msg2html.convert(db_name, att_dir, year, ext_att_dir, html_name)
        with open(f"{html_name}.html", "r") as f:
            text = f.read()
        img_cat2 = f'<img src="{cat2_path}" width="300">'
        self.assertNotIn(img_cat2, text)

        # now do the conversion to html, including external attachments
        html_name = f"test_{year}_extern"
        ext_att_dir = "TestExtern"
        msg2html.convert(db_name, att_dir, year, ext_att_dir, html_name)
        with open(f"{html_name}.html", "r") as f:
            text = f.read()

        # check for info lines in html describing this copy
        self.assertIn("<html>\n<head>\n<style>", text)
        found_ext = f"Found extern file {ext}{cat2_dir}{cat2_name}<"
        self.assertIn(found_ext, text)
        copying_to = f"Copying to {cat2_path}<"
        self.assertIn(copying_to, text)
        copying_as = f"As {lib_dir}{att_dir}{cat2_dir}{cat2_name}<"
        self.assertIn(copying_as, text)

        # check that ext files were copied into local db
        self.assertTrue(path.exists(cat2_path))

        # do a regular conversion and see that new images were incorporated
        html_name = f"test_{year}_post_extern"
        ext_att_dir = None
        msg2html.convert(db_name, att_dir, year, ext_att_dir, html_name)
        with open(f"{html_name}.html", "r") as f:
            text = f.read()
        self.assertIn(img_cat2, text)

    def test_4_parser(self):
        if not (path.exists("chat.db") and path.exists("Attachments")):
            return

        html_dummy = "1000_dbg.html"
        if path.exists(html_dummy):
            os.remove(html_dummy)
        self.assertFalse(path.exists(html_dummy))
        if path.exists("test_links"):
            shutil.rmtree("test_links")
        have_links = path.exists("links")
        if have_links:
            os.rename("links", "test_links")
        self.assertFalse(path.exists("links"))

        msg2html.main(["1000", "-d", "11", "-f", "-e", "TestExtern"])

        self.assertTrue(path.exists(html_dummy))
        os.remove(html_dummy)
        self.assertTrue(path.exists("links"))
        shutil.rmtree("links")
        if have_links:
            os.rename("test_links", "links")

    def test_5_links(self):
        # remove any existing test_links dir
        msg2html.links = links = "test_links"
        if path.exists(links):
            shutil.rmtree(links)
        self.assertFalse(path.exists(links))

        # generate links in the test_links dir, and check for them
        os.makedirs(links)
        self.convert_one_year(0)
        self.assertTrue(path.exists(links))
        fn1 = path.join(links, path.split(test_attachments[1][2])[1])
        self.assertTrue(path.exists(fn1), fn1)
        fn2 = path.join(links, path.split(self.heic_jpeg)[1])
        self.assertTrue(path.exists(fn2), fn2)

        # generate the same links again so it has to make unique filenames
        self.convert_one_year(10)
        fn2se = path.splitext(fn2)
        fn2_1 = fn2se[0] + "_1" + fn2se[1]
        self.assertTrue(path.exists(fn2_1), fn2_1)


if __name__ == "__main__":
    unittest.main()
