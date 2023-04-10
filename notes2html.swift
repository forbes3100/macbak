// notes2html -- Back up Apple Notes
//
// Copyright (C) 2023 Scott Forbes
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

import Foundation
import ScriptingBridge

var writePdf = false // Set to back up notes as PDF, false for HTML
let maxNotes = 9999  // Set this to a small number when debugging

// ScriptingBridge interface to Notes.app

@objc fileprivate protocol NotesApplication {
    @objc optional var folders: [NotesFolder] { get }
}

@objc fileprivate protocol NotesFolder {
    @objc optional var name: String { get }
    @objc optional var notes: [NotesNote] { get }
}

@objc fileprivate protocol NotesNote {
    @objc optional var name: String { get }
    @objc optional var body: String { get }
    @objc optional var modificationDate: Date { get }
}

extension SBApplication: NotesApplication {}
extension SBObject: NotesFolder, NotesNote {}

fileprivate func backUpNote(notesBakPath: String, folderName: String, curNote: NotesNote) {
    let noteName = curNote.name!
    let noteModDate = curNote.modificationDate!

    let noteNameComponents = noteName.components(separatedBy: " ").prefix(4)
    let sanitizedNoteName = noteNameComponents.joined(separator: "_")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: ":", with: "_")

    let noteName2 = sanitizedNoteName.hasSuffix("_notes") ? sanitizedNoteName : sanitizedNoteName + "_notes"
    let fileExtension = writePdf ? ".pdf" : ".html"
    let finalNoteName = noteName2 + fileExtension

    let folderPath = notesBakPath + folderName + "/"
    let bakFile = folderPath + finalNoteName

    var needBak = false
    var needDelete = false
    
    let fileManager = FileManager.default
    let folderExists = fileManager.fileExists(atPath: folderPath)
    let bakFileExists = fileManager.fileExists(atPath: bakFile)
    
    if folderExists {
        if bakFileExists {
            let bakFileDate = try? fileManager.attributesOfItem(atPath: bakFile)[.modificationDate] as? Date
            if let bakFileDate = bakFileDate, bakFileDate < noteModDate {
                needBak = true
                needDelete = true
                
                let oldName = bakFile + ".old"
                try? fileManager.moveItem(atPath: bakFile, toPath: oldName)
            }
        } else {
            needBak = true
        }
    } else {
        try? fileManager.createDirectory(atPath: folderPath, withIntermediateDirectories: true, attributes: nil)
        needBak = true
    }
    
    if needBak {
        let b = curNote.body!.replacingOccurrences(of: "“", with: "&ldquo;")
            .replacingOccurrences(of: "“", with: "&ldquo;")
            .replacingOccurrences(of: "”", with: "&rdquo;")
            .replacingOccurrences(of: "’", with: "&rsquo;")
            .replacingOccurrences(of: "‘", with: "&lsquo;")
            .replacingOccurrences(of: "–", with: "&ndash;")
            .replacingOccurrences(of: "—", with: "&mdash;")
            .replacingOccurrences(of: "…", with: "&hellip;")
            .replacingOccurrences(of: "μ", with: "&mu;")
            .replacingOccurrences(of: "π", with: "&pi;")
        do {
            try b.write(toFile: bakFile, atomically: true, encoding: .utf8)
        } catch {
            print("Error writing to file: \(error.localizedDescription)")
        }
    }
    
    if needDelete {
        try? fileManager.removeItem(atPath: bakFile + ".old")
    }
}


func notes2Html() {
    let fileManager = FileManager.default

    let notesBakName = "notes_icloud_bak"
    let docsPath = try? fileManager.url(
        for: .documentDirectory,
        in: .userDomainMask,
        appropriateFor: nil,
        create: false
    ).path + "/"
    let notesBakPath = (docsPath ?? "") + notesBakName + "/"

    if !(fileManager.fileExists(atPath: notesBakPath)) {
        do {
            try fileManager.createDirectory(
                atPath: notesBakPath,
                withIntermediateDirectories: true,
                attributes: nil
            )
        } catch {
            print("Error creating backup folder: \(error.localizedDescription)")
        }
    }

    guard let notesApp = SBApplication(bundleIdentifier: "com.apple.Notes")
            as NotesApplication? else {
        print("Unable to access Notes application")
        return
    }
    
    guard let folders = notesApp.folders else {
        print("Unable to access Notes folders")
        return
    }
    
    var i = 0
    for folder in folders {
        if let folderName = folder.name {
            print("Folder: \(folderName)")
            if folderName != "Recently Deleted", let notes = folder.notes {
                i += 1
                if i > maxNotes {
                    break
                }
                for note in notes {
                    backUpNote(
                        notesBakPath: notesBakPath,
                        folderName: folderName,
                        curNote: note
                    )
                }
            }
            if i > maxNotes {
                break
            }
        }
    }
}
