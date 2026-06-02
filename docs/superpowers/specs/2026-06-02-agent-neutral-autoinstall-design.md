# Agent-Neutral Auto-Install Design

## Goal

Make MathRender a VS Code extension for AI coding agents, with automatic hook installation for both Codex and Claude Code while preserving the existing local HTTP rendering model.

## Current State

MathRender currently copies `hook_send_formulas.py` into `~/.mathrender/` and auto-installs a Claude Code `Stop` hook by editing `~/.claude/settings.json`. The Python hook reads Claude-style JSON on stdin, extracts `last_assistant_message`, detects LaTeX outside code blocks, and posts the full response to the VS Code extension server at `127.0.0.1:18573`.

The extension already exposes a provider-neutral HTTP surface: `/health`, `/response`, `/formula`, `/pause`, `/resume`, `/clear`, `/history`, and `/status`.

## Design

MathRender should stay transport-first:

- The VS Code extension owns the HTTP server, history, webview, and status.
- The Python script is a shared agent hook that normalizes supported hook payloads into a response text.
- Agent-specific installation lives in small installer helpers, not in rendering logic.

Automatic installation on activation:

- Always copy the bundled hook to `~/.mathrender/hook_send_formulas.py`.
- Ensure `~/.claude/settings.json` exists and install or update a Claude `Stop` hook.
- Ensure `~/.codex/hooks.json` exists and install or update a Codex `Stop` command hook.
- Do not attempt to bypass Codex hook trust. Codex documents that non-managed command hooks must be reviewed and trusted before they run. MathRender can install the hook definition, but Codex owns the trust gate.

Codex hook shape:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/example/.mathrender/hook_send_formulas.py\"",
            "timeout": 5,
            "statusMessage": "Sending LaTeX to MathRender"
          }
        ]
      }
    ]
  }
}
```

Claude Code hook shape remains compatible with the existing settings structure:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/Users/example/.mathrender/hook_send_formulas.py\"",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ]
  }
}
```

## User Experience

The user installs the extension and opens the panel. MathRender auto-installs both supported agent hooks. The panel and docs should no longer position the product as "for Claude Code"; they should say "for AI coding agents" and explicitly list Codex and Claude Code.

Status should show the copied hook path and whether agent hooks are installed. The existing `Send Test Formula` command remains the setup smoke test independent of either agent.

## Risks

- Codex trust review prevents a true first-run zero-click capture in some environments. This is a Codex security gate, not something MathRender should bypass.
- Blind terminal parsing is out of scope. It is fragile, shell-specific, and would create false positives from commands and environment variables.
- Updating user-level JSON files must preserve unrelated hooks and settings.

## Test Strategy

- Add Python tests for agent payload normalization, including Claude `last_assistant_message`, Codex `last_assistant_message`, plain text fallback, invalid JSON, paused status, and no-formula suppression.
- Add TypeScript compile coverage by keeping installer changes type-safe and running `npm run compile`.
- Run the existing Python test suite with external pytest plugin autoload disabled.

## Release

Bump the VS Code extension from `0.7.1` to `0.8.0`, update changelog and README files, package a new VSIX, commit, and push to `origin main`.
