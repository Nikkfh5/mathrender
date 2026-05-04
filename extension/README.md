# MathRender — LaTeX Formula Renderer for Claude Code

**See math as it's meant to be seen.** MathRender renders LaTeX formulas from Claude Code responses in a beautiful side panel inside VS Code — powered by KaTeX.

Instead of reading raw `$$\int_0^1 x^2 dx$$` in the terminal, you get properly typeset mathematics in real time.

## Features

- **Real-time rendering** — formulas appear instantly as Claude responds
- **Full markdown support** — text, headings, code blocks, tables + math together
- **Display & inline math** — `$$...$$` and `$...$` both supported
- **Session history** — scroll back through all formula responses
- **Search** — filter responses by text or formula content (Ctrl+F)
- **Copy source** — copy raw LaTeX/markdown with one click
- **Pause/Resume** — temporarily stop capturing without closing the panel
- **Dark & Light themes** — automatically matches your VS Code theme
- **Zero dependencies** — Python 3 stdlib for the hook, KaTeX from CDN

## How It Works

```
Claude Code responds with formulas
        |
    Hook fires (Stop event)
        |
    Python parses LaTeX from response
        |
    HTTP POST to VS Code extension
        |
    WebView panel renders with KaTeX
```

The extension runs a lightweight HTTP server inside VS Code. A Claude Code hook (Python script) detects LaTeX in responses and sends them to the panel. No external processes, no browser windows — everything stays inside VS Code.

## Quick Start

### 1. Install the extension

Install from VS Code Marketplace — search for **MathRender** in Extensions (`Ctrl+Shift+X`).

### 2. Open the panel

Press `Ctrl+Shift+P` and run:

> **MathRender: Show Panel**

That's it. The extension **automatically installs** the Claude Code hook on first launch. No cloning, no scripts, no extra setup. Start asking Claude about math and formulas will appear in the panel.

> **Note:** Python 3.10+ must be installed and available as `python` (Windows) or `python3` (macOS/Linux).

## Commands

Open with `Ctrl+Shift+P` → type **MathRender**.

| Command | Description |
|---------|-------------|
| `MathRender: Show Panel` | Open the formula panel (starts the server) |
| `MathRender: Enable` | Same as Show Panel |
| `MathRender: Disable` | Stop server and close panel |
| `MathRender: Status` | Show server port, hook path, history count, and pause state |
| `MathRender: Send Test Formula` | Inject a test formula into the panel — verify setup without Claude |

## Panel Controls

| Button | Action |
|--------|--------|
| **Search** | Toggle search bar (also `Ctrl+F`) |
| **Pause** | Stop capturing new responses |
| **Resume** | Resume capturing |
| **Clear** | Clear session history |
| **Copy** | Copy raw source (appears on hover) |

## Settings

Open with `Ctrl+,` → search **MathRender**.

| Setting | Default | Description |
|---------|---------|-------------|
| `mathrender.port` | `18573` | Port for the local HTTP server. Change if 18573 is already in use. Reopen the panel after changing. |
| `mathrender.macros` | `{}` | Custom KaTeX macros merged with built-ins. Example: `{"\\vec": "\\mathbf{#1}"}` |

Built-in macros: `\R` `\N` `\Z` `\C` `\Q` (number sets).

## Supported LaTeX Syntax

| Syntax | Example |
|--------|---------|
| Display math | `$$\int_0^1 x^2 dx = \frac{1}{3}$$` |
| Inline math | `$E = mc^2$` |
| Bracket notation | `\[...\]` and `\(...\)` |
| Common macros | `\R`, `\N`, `\Z`, `\C`, `\Q` for number sets |

## Requirements

- **VS Code** 1.85+
- **Python** 3.10+
- **Claude Code** CLI or VS Code extension

## Uninstall

```bash
python uninstall.py
```

Then remove the extension from VS Code.

## Links

- [GitHub Repository](https://github.com/Nikkfh5/mathrender)
- [Report Issues](https://github.com/Nikkfh5/mathrender/issues)
- Telegram: [@voidnyan](https://t.me/voidnyan)
- Email: v-353@yandex.com

## License

[MIT](https://github.com/Nikkfh5/mathrender/blob/main/LICENSE)

---

*This is an independent community project. It is not affiliated with, endorsed by, or officially connected to [Anthropic](https://anthropic.com). Claude Code is a product of Anthropic.*
