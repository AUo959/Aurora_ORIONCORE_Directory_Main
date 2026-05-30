# Aurora macOS Starter

This is the smallest root-scoped Aurora macOS starter currently proven runnable
on this machine.

It proves only this app surface:

- SwiftPM executable: `aurora-macos-starter`
- Native macOS API surface: AppKit `NSApplication` plus an `NSWindow` shell
- Smoke mode: `--smoke`, which constructs the AppKit shell without opening a
  window, then exits and prints the proved surface

It does not claim an Aurora product UI, app bundle, signing flow, packaging
flow, Xcode project, or XCTest target.

## Commands

Use an external build scratch path so generated SwiftPM output stays out of the
root control-plane repo.

```bash
CLANG_MODULE_CACHE_PATH=/tmp/clang-module-cache \
swift build \
  --package-path tools/aurora_macos_starter \
  --scratch-path /tmp/aurora_macos_starter_build
```

```bash
CLANG_MODULE_CACHE_PATH=/tmp/clang-module-cache \
swift run \
  --package-path tools/aurora_macos_starter \
  --scratch-path /tmp/aurora_macos_starter_build \
  aurora-macos-starter --smoke
```
