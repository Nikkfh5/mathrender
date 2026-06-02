# MathRender - LaTeX Formula Renderer for AI Coding Agents

**See math as it is meant to be seen.** MathRender renders LaTeX formulas from Codex and Claude Code responses in a VS Code side panel powered by KaTeX.

Instead of reading raw `$$\int_0^1 x^2 dx$$` in the terminal, you get properly typeset mathematics in real time.

## Features

- **Codex + Claude Code support** - automatic hook installation for both agents
- **Real-time rendering** - formulas appear as agent responses finish
- **Full markdown support** - text, headings, code blocks, tables, and math together
- **Display and inline math** - `$$...$$`, `$...$`, `\[...\]`, and `\(...\)`
- **Session history** - scroll back through captured formula responses
- **Search** - filter responses by text or formula content
- **Copy source** - copy raw LaTeX/markdown with one click
- **Pause/Resume** - temporarily stop capturing without closing the panel
- **Zero Python package dependencies** - the hook uses Python stdlib only

## How It Works

```
Codex or Claude Code responds with formulas
        |
    Stop hook runs
        |
    Python detects LaTeX outside code blocks
        |
    HTTP POST to the VS Code extension
        |
    WebView panel renders markdown + KaTeX
```

The extension runs a lightweight HTTP server inside VS Code. The hook script sends formula-bearing assistant responses to the local server. No external browser window is required.

## Quick Start

### 1. Install the extension

Install from VS Code Marketplace, then open the command palette.

### 2. Open the panel

Run:

> **MathRender: Show Panel**

On activation, MathRender automatically copies its hook script to `~/.mathrender/hook_send_formulas.py` and installs supported agent hooks:

- Codex: `~/.codex/hooks.json`
- Claude Code: `~/.claude/settings.json`

Codex may still require hook trust review through `/hooks` before running a newly installed or changed hook. MathRender installs the hook automatically; Codex controls that security review.

## Commands

Open with `Ctrl+Shift+P` and type **MathRender**.

| Command | Description |
|---------|-------------|
| `MathRender: Show Panel` | Open the formula panel and start the server |
| `MathRender: Enable` | Same as Show Panel |
| `MathRender: Disable` | Stop the server and close the panel |
| `MathRender: Status` | Show server, hook, history, and pause state |
| `MathRender: Send Test Formula` | Inject a test formula without Codex or Claude Code |

## Settings

Open with `Ctrl+,` and search **MathRender**.

| Setting | Default | Description |
|---------|---------|-------------|
| `mathrender.port` | `18573` | Port for the local HTTP server. Reopen the panel after changing it. |
| `mathrender.macros` | `{}` | Custom KaTeX macros merged with built-ins. Example: `{"\\vec": "\\mathbf{#1}"}` |

Built-in macros: `\R` `\N` `\Z` `\C` `\Q`.

## Requirements

- VS Code 1.85+
- Python 3.10+
- Codex and/or Claude Code

## Links

- [GitHub Repository](https://github.com/Nikkfh5/mathrender)
- [Report Issues](https://github.com/Nikkfh5/mathrender/issues)
- Telegram: [@voidnyan](https://t.me/voidnyan)
- Email: v-353@yandex.com

## License

[MIT](https://github.com/Nikkfh5/mathrender/blob/main/LICENSE)

---

This is an independent community project. It is not affiliated with, endorsed by, or officially connected to OpenAI, Anthropic, or the Codex/Claude Code teams.
