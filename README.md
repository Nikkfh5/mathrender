# MathRender

Renders LaTeX formulas from Claude Code in a VS Code panel. Instead of reading raw `$$\int_0^1 x^2 dx$$` in the terminal, you see beautifully rendered math in real time.

## How it works

```
Claude Code responds with formulas
        |
    Hook fires (Stop event)
        |
    Parses LaTeX from response
        |
    Sends to VS Code extension (localhost HTTP)
        |
    WebView panel renders markdown + KaTeX
```

- Full response rendering: text + formulas together, like a textbook
- Zero config: open the panel and it just works
- Zero dependencies: Python 3 stdlib for the hook, KaTeX from CDN
- Session history: scroll back through all responses
- Pause/resume: temporarily stop capturing without closing the panel

## Requirements

- **Windows** (also works on macOS/Linux)
- Python 3.10+
- Claude Code CLI or VS Code extension
- VS Code

## Install

### 1. Add the hook to Claude Code

```bash
python install.py
```

### 2. Build and install the VS Code extension

```bash
cd extension
npm install
npm run compile
npx @vscode/vsce package
code --install-extension mathrender-0.1.0.vsix
```

## Usage

In VS Code, open Command Palette (`Ctrl+Shift+P`) and run:

- **MathRender: Show Panel** — open the formula panel (also starts the server)
- **MathRender: Disable** — stop everything

MathRender is **off by default**. Open the panel when you need it. It stays active until you disable it or close VS Code.

## Uninstall

```bash
python uninstall.py
code --uninstall-extension mathrender.mathrender
```

## Project structure

```
extension/              VS Code extension (TypeScript)
  src/extension.ts      HTTP server + WebView + commands
  media/index.html      Frontend: markdown + KaTeX rendering
  package.json          Extension manifest
hook_send_formulas.py   Claude Code Stop hook
install.py              Hook installer
uninstall.py            Hook uninstaller
tests/                  Test suite
```

## How the hook works

The hook is configured as an async Stop event in Claude Code. On each response:

1. Python checks if the MathRender server is running (HTTP health check)
2. If running and not paused, checks if the response contains LaTeX (`$$...$$`, `$...$`, `\[...\]`, `\(...\)`)
3. If formulas found, sends the full response text to the VS Code extension
4. Extension pushes it to the WebView panel via postMessage
5. WebView renders markdown with KaTeX

## Running tests

```bash
python -m pytest tests/ -v
```

## Disclaimer

This is an independent community project. It is not affiliated with, endorsed by, or officially connected to [Anthropic](https://anthropic.com) in any way. Claude Code is a product of Anthropic.

## License

[MIT](LICENSE)
