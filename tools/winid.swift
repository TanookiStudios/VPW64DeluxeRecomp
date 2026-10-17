// Print the CGWindowID of the first on-screen window owned by the named process.
// Usage: swift tools/winid.swift <process name>
import CoreGraphics
import Foundation
let name = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "VPW64Deluxe"
let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as! [[String: Any]]
for w in list {
    if (w[kCGWindowOwnerName as String] as? String) == name, let id = w[kCGWindowNumber as String] as? Int,
       let bounds = w[kCGWindowBounds as String] as? [String: Any], (bounds["Height"] as? Double ?? 0) > 100 {
        print(id); exit(0)
    }
}
FileHandle.standardError.write("no window for \(name)\n".data(using: .utf8)!); exit(1)
