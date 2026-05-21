# Dev Tooling User-Space Install Receipt - 2026-05-21

## Scope

Applied the dev-tooling recommendation fixes that can be completed without
Homebrew, Docker Desktop, full Xcode, or interactive administrator password
entry.

No nested repos were edited. No system package manager was installed. No Xcode
or Docker GUI install was attempted.

## Blocked System-Level Items

- Homebrew: official installer reached the sudo check and stopped because this
  Codex session cannot provide the required interactive administrator password.
- Docker Desktop: remains blocked behind Homebrew or a manual GUI installer.
- Full Xcode: `/Applications/Xcode.app` is absent, and `xcodebuild -version`
  reports that `/Library/Developer/CommandLineTools` is selected instead of full
  Xcode.

## User-Space Fixes Applied

- Rust installed through the official `rustup` bootstrap into:
  - `/Users/travisstreets/.cargo`
  - `/Users/travisstreets/.rustup`
- Rust tools exposed through existing PATH lane:
  - `/Users/travisstreets/.local/bin/rustc`
  - `/Users/travisstreets/.local/bin/cargo`
  - `/Users/travisstreets/.local/bin/rustup`
- Go `go1.26.3` installed from the official Go darwin/arm64 tarball into:
  - `/Users/travisstreets/.local/opt/go1.26.3`
- Go tools exposed through existing PATH lane:
  - `/Users/travisstreets/.local/bin/go`
  - `/Users/travisstreets/.local/bin/gofmt`

## Verification

```bash
rustc --version
cargo --version
rustup --version
go version
gofmt -h
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
python3 tools/aurora_recommendation_engine.py --persist-report --summary
```

Results:

- `rustc 1.95.0 (59807616e 2026-04-14)`
- `cargo 1.95.0 (f2d3ce0bd 2026-03-21)`
- `rustup 1.29.0 (28d1352db 2026-03-05)`
- `go version go1.26.3 darwin/arm64`
- Devkit status remains `WARN`, but tool findings dropped from `5` to `3`.
- Clean recommendation count dropped from `11` to `9`; the Rust and Go
  developer-tooling recommendations are no longer present.
- Remaining devkit findings:
  - `tool_docker_missing`
  - `tool_brew_missing`
  - `tool_xcodebuild_error`

## Sources

- Rust installer: `https://www.rust-lang.org/tools/install`
- Go latest version endpoint: `https://go.dev/VERSION?m=text`
- Go install docs: `https://go.dev/doc/install`
