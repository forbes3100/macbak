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
    // (requires macOS 11+)
    //return ProcessInfo.processInfo.isLowPowerModeEnabled
    return false
}

// Get the Application Support directory
func getApplicationSupportDirectory() -> URL {
    let fileManager = FileManager.default
    guard let appSupportDirectory = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else {
        fatalError("Failed to create URL for application support directory")
    }
    
    // Create a subdirectory for macbak if it doesn't exist
    let appDirectory = appSupportDirectory.appendingPathComponent("macbak")
    if !fileManager.fileExists(atPath: appDirectory.path) {
        do {
            try fileManager.createDirectory(at: appDirectory, withIntermediateDirectories: true, attributes: nil)
        } catch {
            fatalError("Failed to create application support directory: \(error)")
        }
    }
    
    return appDirectory
}

func macbak() {
    if isSystemAsleep() {
        exit(0)
    }

    let appDirectory = getApplicationSupportDirectory()
    let logFilePath = appDirectory.appendingPathComponent("macbak.log")

    let currentDateTime = DateFormatter.localizedString(
        from: Date(),
        dateStyle: .medium,
        timeStyle: .medium
    )

    //notes2Html()
    msg2html(htmlDir: appDirectory.path)

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
