# MathRender Agent Guide

## Project

MathRender is a VS Code extension that renders LaTeX from AI coding agent responses in a side panel. The stable ingestion API is the local HTTP server in `extension/src/extension.ts`; agent-specific hooks are adapters and should stay small.

## Supported Agents

- Codex via `~/.codex/hooks.json`
- Claude Code via `~/.claude/settings.json`

Do not make the product Claude-only. Public copy should say "AI coding agents" and then list Codex and Claude Code explicitly where useful.

## Commands

Run from the repository root:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/ -v
```

Run from `extension/`:

```powershell
npm run compile
npx @vscode/vsce package
```

The pytest environment variable avoids unrelated globally installed pytest plugins on this Windows machine.

## Editing Rules

- Keep `hook_send_formulas.py` and `extension/media/hook_send_formulas.py` in sync.
- Preserve unrelated user hooks/settings when editing JSON config files.
- Do not bypass or fake Codex hook trust. MathRender may install hook definitions automatically; Codex owns hook review/trust.
- Bump `extension/package.json` and `extension/package-lock.json` together for releases.
- Keep generated VSIX files only when they are the intended release artifact.

## Release Checklist

1. Run Python tests with plugin autoload disabled.
2. Run `npm run compile` in `extension/`.
3. Package with `npx @vscode/vsce package`.
4. Check `git status --short` for unintended files.
5. Commit and push to `origin main` when the user asks for a repo push.
