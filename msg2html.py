#!/usr/bin/env python3
#
# msg2html -- Convert a Mac Messages database into HTML
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

import sys, os, re, datetime
import os.path as path
import argparse
import shutil
import json
import sqlite3
import html
import pyemoji
import PIL
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

debug = 0
links = None
att_dir = None
ext_att_files = None
css = None
out = None

# Common HTML head and foot, including CSS
# classes are: d=date, i=my_info, j=info, c=container, cm=my_container,
# me=my_text, g=my_sms_text, n=name, p=text

html_head = """
<!DOCTYPE html>
<html>
<head>
<style>
.d   {
    background-color: #ffffff;
    color: #505050;
    font-size: 70%;
    margin-top: 20px;
    margin-bottom: 0px;
    margin-left: 400px;
    margin-right: 10px;
}
.i   {
    background-color: #ffffff;
    color: #505050;
    font-size: 70%;
    font-style: italic;
    margin-top: 0px;
    margin-bottom: 0px;
    margin-left: 250px;
    margin-right: 10px;
}
.j   {
    background-color: #ffffff;
    color: #505050;
    font-size: 70%;
    font-style: italic;
    margin-top: 0px;
    margin-bottom: 0px;
    margin-left: 0px;
    margin-right: 10px;
}
.c   {
    margin-top: 5px;
    margin-right: 300px;
}
.cm  {
    margin-top: 0px;
    margin-left: 250px;
    margin-right: 10px;
}
.me  {
    background-color: #1b86fd;
    color: #ffffff;
    font-size: 80%;
    font-family: verdana;
    width: fit-content;
    margin-left: auto;
}
.g   {
    background-color: #2dbf4f;
    color: #ffffff;
    font-size: 80%;
    font-family: verdana;
    width: fit-content;
    margin-left: auto;
}
.n   {
    background-color: #ffffff;
    color: #505050;
    font-size: 70%;
    margin-top: 0px;
    margin-bottom: 0px;
    margin-left: 40px;
}
p    {
    background-color: #e6e6e6;
    border-radius: 15px;
    font-size: 80%;
    color: #000000;
    font-family: verdana;
    padding: 5px;
    width: fit-content;
}
</style>
</head>
<body>

"""

html_tail = """

</body>
</html>
"""

class CSS:
    """Cascading Style Sheet classes, based on context."""

    def __init__(self, is_from_me, svc):
        if is_from_me:
            self.con_class = ' class="cm"'
            self.flex_class = (
                ' style="display: flex; justify-content: flex-end"'
            )
            bubble = ("me", "g")[svc == "SMS"]
            self.text_class = f' class="{bubble}"'
            self.info_class = ' class="i"'
            self.img_class = ' class="cm"'
        else:
            self.con_class = ' class="c"'
            self.flex_class = ""
            self.text_class = ""
            self.info_class = ' class="j"'
            self.img_class = ""


class Message:
    def __init__(self, msg):
        (
            self.rowid,
            self.date,
            self.guid,
            self.is_from_me,
            self.has_attach,
            self.handle_id,
            self.text,
            self.svc,
        ) = msg


lib_path = "~/Library/Messages/"
lib_path_len = len(lib_path)

def add_link_to(image_file_h, mime_t):
    """Create a (unique) symlink to image_file in the links dir."""

    if mime_t[:5] == "image":
        image_file = image_file_h.replace("%23", "#")
        image_path = path.realpath(image_file)
        if not path.exists(image_path):
            ##raise IOError(f'no image file {image_path}')
            return
        # keep original name unless it exists, if so add unique seq#
        image_name = path.split(image_file)[1]
        link = path.join(links, image_name)
        seq = 0
        link_name, link_ext = path.splitext(image_name)
        while path.exists(link):
            seq += 1
            link = path.join(links, f"{link_name}_{seq}{link_ext}")
        os.symlink(image_path, link)


def output_text(text):
    """Write text to output as HTML, converting emoji."""

    if debug > 0:
        utext = text.encode("unicode_escape")
        out.write(f"<p{css.info_class}>text({len(text)}) = {utext}</p>\n")
    if len(text) > 0:
        text = html.escape(text)
        text = text.encode("ascii", "xmlcharrefreplace")
        text = pyemoji.entities(text)
        text = text.replace("\n", "<br>")
        out.write(
            f"<div{css.con_class}><div{css.flex_class}>\n"
            f"<p{css.text_class}>{text}</p>\n"
            "</div></div>\n"
        )


def output_attachment(seq, msg, con, cursor):
    """Convert a message attachment to HTML and write to out file.

    seq: sequence number
    msg: Message
    con: open sqlite3 connection
    cursor: sqlite3 cursor
    """
    if not msg.has_attach:
        out.write(f"<p{css.info_class}>No attachment!</p>\n")
        return

    # get the attachment record corresponding to given message ID, using JOIN
    cursor.execute(
        """
        SELECT attachment.created_date, attachment.filename,
        attachment.mime_type, attachment.transfer_name FROM attachment
        INNER JOIN message_attachment_join ON
        attachment.rowid=message_attachment_join.attachment_id
        WHERE message_attachment_join.message_id=?
        LIMIT 1 OFFSET ?;""",
        (msg.rowid, seq),
    )
    a_date, a_libpath, mime_t, tr_name = cursor.fetchall()[0]
    if debug > 2:
        out.write(
            f"<p{css.info_class}>att {msg.rowid},{seq},{msg.date},{msg.guid}:"
            f"<br>{a_date},{a_libpath},{mime_t},{tr_name}</p>\n"
        )

    if debug > 1:
        out.write(f"<p{css.info_class}>a_libpath={a_libpath}</p>\n")
    a_path = None
    if a_libpath is None:
        # if no path to file in ~/Library/Messages, look for it in external
        # Attachments dir
        if tr_name in ext_att_files:
            src = path.join(ext_att_files[tr_name], tr_name)
            assert path.exists(src)
            src_sub = src.split("/")[-4:]
            a_path = path.join(att_dir, path.join(*src_sub))
            a_libpath = lib_path + a_path
            out.write(
                f"<p{css.info_class}>Found extern file {src}<br>\n"
                f"Copying to {a_path}<br>\nAs {a_libpath}</p>\n"
            )
            os.makedirs(path.split(a_path)[0], exist_ok=True)
            shutil.copy2(src, a_path)
            cursor.execute(
                """
                UPDATE attachment
                SET filename=?
                WHERE rowid IN (
                    SELECT attachment_id
                    FROM message_attachment_join
                    WHERE message_id=?
                    LIMIT 1 OFFSET ?
                );""",
                (a_libpath, msg.rowid, seq),
            )
            con.commit()
        else:
            out.write(f"<p{css.info_class}>No file! {tr_name} {mime_t}</p>\n")
            return
    else:
        if a_libpath[:lib_path_len] != lib_path:
            out.write(f"<p{css.info_class}>Not in library! {a_libpath}</p>\n")
            return
        a_path = a_libpath[lib_path_len:]

    # now have attached file's path-- output a reference to it
    if not path.exists(a_path):
        out.write(f"<p{css.info_class}>Expected file! {a_path}</p>\n")
        return
    a_path = a_path.replace("#", "%23")
    a_width = 300
    a_splitext = path.splitext(a_path)
    is_pp = a_splitext[1] == ".pluginPayloadAttachment"
    if debug > 1:
        out.write(
            f"<p{css.info_class}>a_path={a_path}, {mime_t}, {a_date}</p>\n"
        )
    else:
        out.write(f"<p{css.info_class}>{a_path}</p>\n")
    if mime_t and mime_t[:5] == "audio":
        out.write(
            f"<audio controls>\n"
            f'<source src="{a_path}" '
            f'type="audio/x-m4a">\n'
            f"Your browser does not support the audio tag.\n"
            f"</audio>\n"
        )
    elif not is_pp:
        if mime_t == "image/heic":
            if is_pp:
                a_width = 32
            # first convert image file to .jpeg
            jpeg_path = a_splitext[0] + ".jpeg"
            if not path.exists(jpeg_path):
                image = Image.open(a_path)
                image.save(jpeg_path, format="jpeg")
            a_path = jpeg_path
            mime_t = "image/jpeg"
            if debug > 1:
                out.write(
                    f"<p{css.info_class}>{a_path}, {mime_t}, {a_date}</p>\n"
                )
        # Mac Safari (at least) seems to want images & movies
        # in an img tag.
        out.write(f'<img{css.img_class} src="{a_path}" width="{a_width}">\n')
        if links and not msg.is_from_me:
            add_link_to(a_path, mime_t)


def convert(db, _att_dir, year, _ext_att_dir, out_name):
    """Convert one year of messages in database db to an HTML file.

    db: database file path
    _att_dir: Attachments dir
    year: desired year [int]
    _ext_att_dir: optional external Attributes dir for additional attachments
    out_name: output file base name
    """
    
    global att_dir, ext_att_dir, ext_att_files, css, out
    att_dir = _att_dir
    ext_att_dir = _ext_att_dir
    out = open(f"{out_name}.html", "w")
    out.write(html_head)

    # read phone-number-to-name handle json file
    handles_name = path.splitext(db)[0] + "_handles.json"
    with open(handles_name) as json_file:
        data = json.load(json_file)
    id_named_handles = {}
    for key, value in data.items():
        id_named_handles[key] = value
    if debug == 10:
        out.write(repr(id_named_handles))

    # if external Attributes directory path given, make a list of files there
    ext_att_files = {}
    if ext_att_dir and path.exists(ext_att_dir):
        for root, dirs, files in os.walk(ext_att_dir):
            if len(dirs) == 0:
                for f in files:
                    ext_att_files[f] = root
    if debug == 11:
        for f, root in ext_att_files.items():
            out.write(f"<p>root={root}, f={f}</p>\n")

    # convert all messages in database
    con = sqlite3.connect(db)
    cursor = con.cursor()
    cursor.execute("SELECT rowid, id FROM handle;")
    r = cursor.fetchall()
    handles = {}
    for rowid, id in r:
        handles[rowid] = id_named_handles.get(id, id)
    if debug == 10:
        out.write(f"<p>handles={repr(handles)}</p>\n")

    cursor.execute(
        """
        SELECT rowid, datetime(substr(date, 1, 9) + 978307200, 'unixepoch',
        'localtime') AS f_date, guid, is_from_me, cache_has_attachments,
        handle_id, text, service
        FROM message ORDER BY f_date;"""
    )
    rows = cursor.fetchall()
    prev_day = ""
    prev_who = None
    for row in rows:
        msg = Message(row)
        y = int(msg.date[:4])
        ##print(f'rowid={msg.rowid} year={y}')
        if y != year:
            continue
        if msg.handle_id == 0:
            msg.is_from_me = True
        day = msg.date[:10]
        if day != prev_day:
            out.write("<hr>")
        ##if debug and guid:
        ##    out.write(f'<p class="d">guid = {msg.guid}</p>')
        who = handles.get(msg.handle_id)
        css = CSS(msg.is_from_me, msg.svc)
        if msg.is_from_me:
            out.write(
                f'<p class="d">{msg.date} - from me, {msg.svc}'
                f" #{msg.rowid}</p>\n"
            )
        else:
            out.write(
                f'<p class="d">{msg.date} - from {who}, {msg.svc}'
                f" #{msg.rowid}</p>\n"
            )
            if who != prev_who or day != prev_day:
                out.write(f'<p class="n">{who}</p>\n')
                prev_who = who
        prev_day = day

        # possible cases:
        #   text
        #   attachment
        #   text 0, attachment 0, [text 1, attachment 1, ...] text n
        #
        if msg.text is not None:
            replace_obj_token = "\ufffc"
            i = 0
            seq = 0
            for m in re.finditer(replace_obj_token, msg.text):
                output_text(msg.text[i : m.start()])
                i = m.end()
                output_attachment(seq, msg, con, cursor)
                seq += 1
            output_text(msg.text[i:])
        else:
            output_attachment(0, msg, con, cursor)

    out.write(html_tail)
    out.close()


def main(argv):
    global debug, links

    parser = argparse.ArgumentParser(description="Convert messages to html")
    parser.add_argument("start_year", help="start year", type=int)
    parser.add_argument(
        "end_year", help="end year", type=int, nargs="?", default=None
    )
    parser.add_argument("-d", help="debug level", type=int, default=0)
    parser.add_argument("-e", help="external attachment library to search")
    parser.add_argument(
        "-f", help="generate attachment links", action="store_true"
    )
    args = parser.parse_args(argv)
    extra = ""
    if args.d:
        debug = args.d
        extra += "_dbg"
    if args.f:
        links = "links"
        os.makedirs(links, exist_ok=True)

    for year in range(args.start_year, (args.end_year or args.start_year) + 1):
        convert("chat.db", "Attachments", year, args.e, f"{year}{extra}")


if __name__ == "__main__":
    main(sys.argv[1:])
