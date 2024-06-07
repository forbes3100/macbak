// icdrivebak -- Force all iCloud Drive files to be downloaded, for backup
//
// Copyright (C) 2024 Scott Forbes
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
import UniformTypeIdentifiers

// Define constants for paths
let home = NSHomeDirectory()
let icloud = home + "/Library/Mobile Documents/"
let icloudDocs = icloud + "com~apple~CloudDocs/"

// Initialize counters and flags
var haveShownHeader = false
var downloadCount = 0
var failCount = 0
var verbose = 1

// Mapping for app directory renames
let icloudAppDirRenames: [String: String] = [
    "bbedit": "BBEdit",
    "mobilegarageband": "GarageBand for iOS"
]

// Set of files to ignore
let ignoredFiles: Set<String> = [".DS_Store", ".Trash"]

// Function to force download of a file
func forceDownload(filePath: String, fileName: String) {
    let nsUrl = NSURL(fileURLWithPath: filePath)
    let fileManager = FileManager.default
    do {
        try fileManager.startDownloadingUbiquitousItem(at: nsUrl as URL)
        print("  \(fileName)")
        downloadCount += 1
    } catch {
        print("  *** FAILED to download \(fileName): \(error.localizedDescription)")
        failCount += 1
    }
}

// Check if a file is downloaded
func isFileDownloaded(filePath: String) -> Bool {
    let fileURL = URL(fileURLWithPath: filePath)
    let resourceValues = try? fileURL.resourceValues(forKeys: [.ubiquitousItemDownloadingStatusKey])
    if let status = resourceValues?.ubiquitousItemDownloadingStatus {
        return status == .current
    }
    return false
}

// Check if a directory is a package
func isPackage(atPath path: String) -> Bool {
    let fileURL = URL(fileURLWithPath: path)
    if let type = try? fileURL.resourceValues(forKeys: [.contentTypeKey]).contentType {
        return type.conforms(to: .package)
    }
    return false
}

// Recursively force download of directory contents
func forceDownloadDir(cloudDir: String, header: String? = nil, includeDirs: Bool = true) {
    let fileManager = FileManager.default
    let contents = try? fileManager.contentsOfDirectory(atPath: cloudDir)
    contents?.forEach { file in
        if !ignoredFiles.contains(file) {
            let path = cloudDir + file
            var isDir: ObjCBool = false
            fileManager.fileExists(atPath: path, isDirectory: &isDir)
            if isDir.boolValue {
                if !isPackage(atPath: path) {
                    forceDownloadDir(cloudDir: path + "/", header: header, includeDirs: includeDirs)
                }
            } else if !isFileDownloaded(filePath: path) {
                if let header = header, !haveShownHeader {
                    print(header)
                    haveShownHeader = true
                }
                forceDownload(filePath: path, fileName: file)
            }
        }
    }
}

// Insure all iCloud Drive files are downloaded or downloading
func icdrivebak() {
    if verbose >= 1 {
        print("Force download of iCloud Documents folder")
    }
    forceDownloadDir(cloudDir: icloudDocs, includeDirs: false)

    if verbose >= 1 {
        print("Force download of app folders")
    }
    haveShownHeader = false
    let fileManager = FileManager.default
    let apps = try? fileManager.contentsOfDirectory(atPath: icloud)
    apps?.forEach { app in
        let dir = icloud + app + "/Documents/"
        if fileManager.fileExists(atPath: dir) {
            let files = try? fileManager.contentsOfDirectory(atPath: dir)
            if let files = files, files.count > 0 {
                var name = app.split(separator: "~").last.map { String($0) } ?? app
                name = icloudAppDirRenames[name] ?? name
                forceDownloadDir(cloudDir: dir, header: "app \(name)/")
            }
        }
    }

    if downloadCount > 0 || failCount > 0 {
        if downloadCount > 0 {
            let s = downloadCount > 1 ? "s" : ""
            print("Started \(downloadCount) file\(s) downloading.")
        }
        if failCount > 0 {
            print(" \(failCount) files failed to download.")
        }
    } else {
        print("All downloaded.")
    }
}
