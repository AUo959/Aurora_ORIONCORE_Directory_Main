# Dev Tooling Homebrew Docker Activation Receipt - 2026-05-21

## Scope

Recorded the user-completed Homebrew and Docker Desktop installation in the
root dev-tooling reports.

No nested repos were edited. No Docker containers or images were created during
this receipt pass.

## Evidence

```bash
zsh -lc 'brew --version'
zsh -lc 'docker --version'
zsh -lc 'docker compose version'
docker info
zsh -lc 'python3 tools/aurora_devkit.py --persist-report'
zsh -lc 'python3 tools/aurora_devkit.py --install-plan --persist-install-plan'
zsh -lc 'python3 tools/aurora_recommendation_engine.py --persist-report --summary'
```

Results:

- Homebrew: `Homebrew 5.1.13`
- Docker CLI: `Docker version 29.4.3, build 055a478`
- Docker Compose: `Docker Compose version v5.1.4`
- Docker daemon: `docker info` succeeds outside the sandbox with Docker Desktop
  server version `29.4.3`.
- Devkit: `READY`, `19/19` tools OK, no findings, no install-plan items.

## Devkit Impact

- `tool_brew_missing` is no longer present.
- `tool_docker_missing` is no longer present.
- Devkit install plan changed from `2` items to `0` items.
- Clean recommendation count changed from `8` to `6`; all developer-tooling
  recommendations are gone after the clean report refresh.

## Note

This Codex process may need an explicit login shell (`zsh -lc`) to see
Homebrew because `/opt/homebrew/bin` is added through the user's shell startup
configuration. The user's Terminal login shell resolves `brew` correctly.
