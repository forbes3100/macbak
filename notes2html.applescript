# notes2html -- Back up Apple Notes to HTML
#
# Export each updated note to an .html file in ~/Documents/notes_icloud_bak folder.
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

# set this to a small number when debugging
set maxNotes to 9999

# select PDF or HTML backup file format
set writePdf to false

tell application "Finder"
	set notesBakName to "notes_icloud_bak"
	set docsPath to POSIX path of (path to documents folder as text)
	set notesBakPath to docsPath & notesBakName & "/"
end tell

tell application "System Events"
	# (Finder can't deal with POSIX paths)
	if not (folder notesBakPath exists) then
		make new folder at folder docsPath with properties {name:notesBakName}
	end if
end tell

set i to 0

tell application "Notes"
	repeat with f in folders
		set folderName to name of f
		log folderName as text
		if folderName is not "Recently Deleted" then
			repeat with curNote in notes in f
				set i to i + 1
				if i > maxNotes then
					exit repeat
				end if
				log "  " & (name of curNote) as text
				my backUpNote(notesBakPath, folderName, curNote)
			end repeat
		end if
		if i > maxNotes then
			exit repeat
		end if
	end repeat
end tell

on backUpNote(notesBakPath, folderName, curNote)
	tell application "Notes"
		set noteName to name of curNote
		set noteModDate to modification date of curNote
	end tell
	set noteName2 to do shell script "echo " & quoted form of noteName & " | cut -d \" \" -f 1-4 | tr ' ' '_' | tr '/' '_' | tr ':' '_'"
	if not (noteName2 ends with "_notes") then set noteName2 to noteName2 & "_notes"
	if my writePdf then
		set noteName2 to noteName2 & ".pdf"
	else
		set noteName2 to noteName2 & ".html"
	end if
	set folderPath to notesBakPath & folderName & "/"
	set bakFile to folderPath & "/" & noteName2
	## log noteName2 & ": " & noteModDate
	
	set needBak to false
	set needDelete to false
	tell application "System Events"
		if folder folderPath exists then
			if file bakFile exists then
				set f to file bakFile
				set fInfo to info for f
				set bakFileDate to modification date of fInfo
				log " Exists, bakFileDate: " & bakFileDate
				if bakFileDate < noteModDate then
					## log " NEEDS BACKUP"
					set needBak to true
					set needDelete to true
					set oldName to bakFile & ".old"
					set name of file bakFile to oldName
				end if
			else
				set needBak to true
			end if
		else
			make new folder at folder notesBakPath with properties {name:folderName}
			set needBak to true
		end if
	end tell
	
	if needBak then
		if my writePdf then
			tell application "Notes"
				tell curNote
					show
				end tell
			end tell
			
			tell application "System Events" to tell process "Notes"
				click menu item "Export as PDF…" of menu "File" of menu bar 1
				# go to folder named in clipboard
				set the clipboard to bakFile as text
				delay 1
				keystroke "G" using {command down, shift down}
				delay 1
				keystroke "v" using {command down}
				delay 1
				keystroke return
				delay 1
				keystroke return
				delay 1
			end tell
			
		else
			tell application "Notes"
				set b to body of curNote
			end tell
			set b to my replaceText(b, "“", "&ldquo;")
			set b to my replaceText(b, "”", "&rdquo;")
			set b to my replaceText(b, "’", "&rsquo;")
			set b to my replaceText(b, "‘", "&lsquo;")
			set b to my replaceText(b, "–", "&ndash;")
			set b to my replaceText(b, "—", "&mdash;")
			set b to my replaceText(b, "…", "&hellip;")
			set b to my replaceText(b, "μ", "&mu;")
			set b to my replaceText(b, "π", "&pi;")
			tell current application
				set f to open for access POSIX file bakFile with write permission
				set eof of f to 0
				write b to f starting at eof as «class utf8»
				close access f
			end tell
		end if
	end if
	
	if needDelete then
		tell application "System Events"
			delete file oldName
		end tell
	end if
	
end backUpNote

on replaceText(textString, findString, replaceString)
	set prevTIDs to AppleScript's text item delimiters
	set AppleScript's text item delimiters to findString
	set textItems to text items of textString
	set AppleScript's text item delimiters to replaceString
	set newText to textItems as text
	set AppleScript's text item delimiters to prevTIDs
	return newText
end replaceText
