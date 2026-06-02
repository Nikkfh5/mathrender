# MathRender

Renders LaTeX formulas from AI coding agent responses in a VS Code panel. Instead of reading raw `$$\int_0^1 x^2 dx$$` in the terminal, you see rendered math in real time.

Supported agents:

- Codex
- Claude Code

## How It Works

```
Codex or Claude Code responds with formulas
        |
    Agent Stop hook runs
        |
    Python hook detects LaTeX outside code blocks
        |
    HTTP POST to the VS Code extension
        |
    WebView panel renders markdown + KaTeX
```

The extension owns the local HTTP server and rendering UI. Agent hooks are small adapters that send assistant responses to `http://127.0.0.1:18573/response`.

## Features

- Full response rendering: text and formulas together
- Automatic hook installation for Codex and Claude Code
- Python stdlib hook, no Python package dependencies
- Session history and search
- Pause/resume capture without closing the panel
- Test formula command independent of either agent

## Requirements

- VS Code 1.85+
- Python 3.10+
- Codex and/or Claude Code

## Install

### Marketplace

Install MathRender from the VS Code Marketplace, then run:

```
MathRender: Show Panel
```

On activation, MathRender copies the hook to `~/.mathrender/hook_send_formulas.py` and installs:

- Codex hook config in `~/.codex/hooks.json`
- Claude Code hook config in `~/.claude/settings.json`

Codex may require you to trust new or changed hooks through `/hooks` before it runs them. MathRender installs the hook definition automatically, but Codex owns that security gate.

### From Source

```bash
python install.py
cd extension
npm install
npm run compile
npx @vscode/vsce package
code --install-extension mathrender-*.vsix
```

## Usage

In VS Code, open Command Palette (`Ctrl+Shift+P`) and run:

- **MathRender: Show Panel** - open the formula panel and start the server
- **MathRender: Disable** - stop the server and close the panel
- **MathRender: Status** - show server, hook, history, and pause state
- **MathRender: Send Test Formula** - inject a test formula without Codex or Claude

MathRender is off by default. Open the panel when you need it.

## Project Structure

```
extension/              VS Code extension
  src/extension.ts      HTTP server, WebView, commands, hook installers
  media/index.html      Frontend: markdown + KaTeX rendering
  media/hook_send_formulas.py
hook_send_formulas.py   Shared Codex/Claude hook
install.py              Manual hook installer
uninstall.py            Manual hook uninstaller
tests/                  Python hook tests
```

## Running Tests

Disable external pytest plugin autoload on machines with unrelated global pytest plugins:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v
cd extension && npm run compile
```

On PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/ -v
cd extension; npm run compile
```

## Disclaimer

This is an independent community project. It is not affiliated with, endorsed by, or officially connected to OpenAI, Anthropic, or the Codex/Claude Code teams.

## License

[MIT](LICENSE)
