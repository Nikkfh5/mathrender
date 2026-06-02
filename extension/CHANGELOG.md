# Changelog

## 0.8.0 - 2026-06-02

- **feat**: Auto-install MathRender hooks for Codex via `~/.codex/hooks.json`
- **feat**: Keep Claude Code auto-install support through `~/.claude/settings.json`
- **feat**: Shared hook script now supports Codex and Claude Code `Stop` payloads
- **docs**: Reposition MathRender as an AI coding agent LaTeX renderer, with Codex and Claude Code called out explicitly
- **docs**: Add Codex-facing `AGENTS.md` and Claude-facing `CLAUDE.md` project guidance

## 0.7.0 — 2026-05-04

- **fix**: Hook no longer fires on shell variables (`$@`, `$1`, `$var`) inside fenced, inline, and 4-space-indented Markdown code blocks
- **fix**: `server_status()` handles malformed JSON from `/health` gracefully instead of crashing
- **fix**: Hook copied to `~/.mathrender/` — survives repo moves and renames
- **fix**: Hook path in `settings.json` auto-updates if the extension moves
- **fix**: Writes to `settings.json` and `history.json` are now atomic (temp + rename) — no corruption on concurrent access
- **fix**: `~/.mathrender/` and its files get restricted permissions (0o700 / 0o600) on Unix
- **feat**: `MathRender: Status` command — shows server port, hook path, history size, and pause state
- **feat**: `MathRender: Send Test Formula` command — sends a test formula to the panel without Claude
- **feat**: `mathrender.port` setting — customize the server port (default: 18573)
- **feat**: `mathrender.macros` setting — add custom KaTeX macros merged with built-ins (`\R`, `\N`, `\Z`, `\C`, `\Q`)
- **feat**: Hook reads `MATHRENDER_PORT` env variable for port override

## 0.6.1 — 2026-04-09

- Remove SVG copy button

## 0.6.0 — 2026-04-09

- History persistence across panel reloads
- Activity bar badge showing unread formula count
- Export history to LaTeX file
- Search with highlight (Ctrl+F)

## 0.5.0 — 2026-04-03

- Clean rebuild with stable HTTP server architecture

## 0.4.0 — 2026-04-03

- Skip redundant hook copy on reinstall
- System locale support
- Remove `setupHook` command (hook now auto-installs on activation)

## 0.3.0 — 2026-04-01

- Publish to VS Code Marketplace

## 0.2.0 — 2026-04-01

- Auto-install: extension sets up Claude Code hook on first launch
- Hook script bundled inside the extension package

## 0.1.0 — 2026-04-01

- Initial release: KaTeX rendering in VS Code panel via Claude Code stop hook
- Real-time formula rendering, session history, search, pause/resume/clear
- Dark and light theme support, cross-platform (Windows, macOS, Linux)
