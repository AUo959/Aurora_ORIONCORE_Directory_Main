import AppKit
import AuroraMacStarterCore

@main
struct AuroraMacStarterMain {
    @MainActor
    static func main() {
        if CommandLine.arguments.contains("--smoke") {
            print(AuroraMacStarterCore.smokeReport())
            return
        }

        let app = NSApplication.shared
        let delegate = AuroraMacStarterAppDelegate()
        app.delegate = delegate
        app.setActivationPolicy(.regular)
        app.run()
    }
}

final class AuroraMacStarterAppDelegate: NSObject, NSApplicationDelegate {
    private var window: NSWindow?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let window = AuroraMacStarterCore.makeWindow()
        self.window = window
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }
}
