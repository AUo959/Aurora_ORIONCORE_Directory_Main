# Dev Tooling Xcode Activation Receipt - 2026-05-21

## Scope

Recorded the user-completed full Xcode installation and license activation in
the root dev-tooling reports.

No nested repos were edited. No Homebrew or Docker install was performed.

## Evidence

```bash
xcode-select -p
xcodebuild -version
xcodebuild -showsdks
xcrun simctl list runtimes
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
```

Results:

- Active developer directory:
  `/Applications/Xcode.app/Contents/Developer`
- Xcode version:
  `Xcode 26.5`, build `17F42`
- SDKs visible through `xcodebuild -showsdks`:
  iOS `26.5`, iOS Simulator `26.5`, macOS `26.5`, tvOS `26.5`,
  tvOS Simulator `26.5`, visionOS `26.5`, visionOS Simulator `26.5`,
  watchOS `26.5`, watchOS Simulator `26.5`, and DriverKit `25.5`.
- `xcrun simctl list runtimes` runs outside the sandbox and returns an empty
  runtime list: `== Runtimes ==`.

## Devkit Impact

- Devkit tools changed from `16/19 ok` after Rust/Go install to `17/19 ok`.
- `tool_xcodebuild_error` is no longer present.
- Devkit install plan changed from `3` items to `2` items.
- Clean recommendation count changed from `9` to `8`; the Xcode developer
  tooling recommendation is no longer present.
- Remaining devkit findings:
  - `tool_docker_missing`
  - `tool_brew_missing`

## Remaining Work

Homebrew and Docker Desktop remain system-level or GUI-managed installs. They
are outside the root repo and still require explicit owner action.
