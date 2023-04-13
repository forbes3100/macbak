// macbak main -- iCloud backup via a Mac
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
import IOKit.ps

func isSystemAsleep() -> Bool {
    let snapshot = IOPSCopyPowerSourcesInfo().takeRetainedValue()
    let sources = IOPSCopyPowerSourcesList(snapshot).takeRetainedValue() as NSArray

    for ps in sources {
        let description = IOPSGetPowerSourceDescription(snapshot, ps as CFTypeRef).takeUnretainedValue() as NSDictionary

        if let state = description[kIOPSPowerSourceStateKey] as? String {
            if state == kIOPSACPowerValue as String {
                return false
            }
        }
    }

    return true
}

func macbak() {
    if isSystemAsleep() {
        exit(0)
    }

    let desktopURL = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent("Desktop")
    let logFilePath = desktopURL.appendingPathComponent("macbak.log")
    let currentDateTime = DateFormatter.localizedString(
        from: Date(),
        dateStyle: .medium,
        timeStyle: .medium
    )

    notes2Html()

    let logEntry = "\(currentDateTime)\n"
    if let data = logEntry.data(using: .utf8) {
        if let fileHandle = try? FileHandle(forWritingTo: logFilePath) {
            defer {
                fileHandle.closeFile()
            }
            fileHandle.seekToEndOfFile()
            fileHandle.write(data)
        } else {
            try? data.write(to: logFilePath, options: .atomic)
        }
    }
}

macbak()
