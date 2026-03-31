# MathRender

Renders LaTeX formulas from Claude Code in a browser window. Instead of reading raw `$$\int_0^1 x^2 dx$$` in the terminal, you see beautifully rendered math in real time.

## How it works

```
Claude Code responds with formulas
        |
    Hook fires (Stop event)
        |
    Parses LaTeX from response
        |
    Sends full response to local server
        |
    Browser renders markdown + KaTeX
```

- Full response rendering: text + formulas together, like a textbook
- Auto-start: server launches automatically when needed
- Auto-stop: server shuts down when Claude Code session ends
- Zero dependencies: Python 3 stdlib + KaTeX from CDN
- Session history: scroll back through all responses
- Pause/resume: temporarily stop capturing without closing the window

## Requirements

- **macOS only** (tested on M3 Pro)
- Python 3.10+
- Claude Code CLI
- Any browser

## Install

```bash
git clone https://github.com/CKeJIeToH4uK/mathrender.git && cd mathrender
./install.sh
```

This will:
1. Add a Stop hook to `~/.claude/settings.json` (sends formulas to the server)
2. Add a SessionEnd hook (auto-stops the server when the session ends)
3. Add a `mathrender` alias to your shell

Restart your terminal after installation.

## Usage

```bash
mathrender on       # start server + open browser window
mathrender off      # stop everything
mathrender pause    # keep window, stop capturing new responses
mathrender resume   # resume capturing
mathrender status   # check current state
```

MathRender is **off by default**. Turn it on when you need it. It automatically turns off when you close the Claude Code session.

## Uninstall

```bash
./uninstall.sh
```

Removes hooks and alias. Project files remain in the directory.

## Project structure

```
server.py               HTTP server with SSE (stdlib, no deps)
index.html              Frontend: markdown + KaTeX rendering
hook_send_formulas.py   Claude Code Stop hook
mathrender              CLI control script (on/off/pause/resume)
install.sh              Installation script
uninstall.sh            Uninstallation script
tests/                  Test suite
```

## How the hook works

The hook is configured as an async Stop event in Claude Code. On each response:

1. Bash checks if `.enabled` flag exists (microseconds, no Python if off)
2. If enabled, Python checks if the server is paused
3. If not paused, checks if the response contains LaTeX (`$$...$$`, `$...$`, `\[...\]`, `\(...\)`)
4. If formulas found, sends the full response text to the local server
5. Server pushes it to the browser via SSE
6. Browser renders markdown with KaTeX

## Running tests

```bash
python3 -m pytest tests/ -v
```

## Disclaimer

This is an independent community project. It is not affiliated with, endorsed by, or officially connected to [Anthropic](https://anthropic.com) in any way. Claude Code is a product of Anthropic.

## License

[MIT](LICENSE)
