import AppKit
import Foundation

public enum AuroraMacStarterCore {
    public static let appSurface = "AppKit NSApplication + NSWindow shell"

    @MainActor
    public static func smokeReport() -> String {
        let app = NSApplication.shared
        let window = makeWindow()

        return [
            "aurora_macos_starter_smoke: ok",
            "app_surface: \(appSurface)",
            "app_class: \(String(describing: type(of: app)))",
            "window_title: \(window.title)",
            "window_size: \(Int(window.frame.width))x\(Int(window.frame.height))",
            "product: aurora-macos-starter"
        ].joined(separator: "\n")
    }

    @MainActor
    public static func makeWindow() -> NSWindow {
        let frame = NSRect(x: 0, y: 0, width: 480, height: 300)
        let window = NSWindow(
            contentRect: frame,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "Aurora macOS Starter"
        window.contentView = makeContentView(frame: frame)
        return window
    }

    @MainActor
    private static func makeContentView(frame: NSRect) -> NSView {
        let view = NSView(frame: frame)
        let label = NSTextField(labelWithString: "Aurora macOS Starter")
        label.alignment = .center
        label.font = NSFont.systemFont(ofSize: 18, weight: .semibold)
        label.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
        return view
    }
}
