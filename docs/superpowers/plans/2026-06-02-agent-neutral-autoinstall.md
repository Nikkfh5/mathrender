# Agent-Neutral Auto-Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automatic Codex hook installation while preserving Claude Code support and making MathRender agent-neutral.

**Architecture:** Keep the existing local HTTP server as the stable ingestion API. Refactor the Python hook into payload-normalization plus send logic, and refactor the VS Code extension installer into shared hook-copying plus per-agent JSON installers.

**Tech Stack:** Python 3 stdlib hook and tests, VS Code extension in TypeScript, npm/tsc, VSCE packaging.

---

## Files

- Modify: `hook_send_formulas.py`
- Modify: `extension/media/hook_send_formulas.py`
- Modify: `tests/test_hook.py`
- Modify: `extension/src/extension.ts`
- Modify: `extension/package.json`
- Modify: `extension/package-lock.json`
- Modify: `extension/README.md`
- Modify: `README.md`
- Modify: `README.ru.md`
- Modify: `extension/CHANGELOG.md`
- Add: `AGENTS.md`
- Add: `CLAUDE.md`

## Tasks

- [ ] **Task 1: Add failing Python tests for provider-neutral hook parsing**

Add tests in `tests/test_hook.py` that call a new `extract_response_text()` helper. Cover Claude/Codex `last_assistant_message`, text fallback, invalid JSON, and no-formula suppression through `main()`.

Run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/test_hook.py -v
```

Expected before implementation: failures for missing `extract_response_text()`.

- [ ] **Task 2: Implement provider-neutral Python hook**

In both `hook_send_formulas.py` and `extension/media/hook_send_formulas.py`, add `extract_response_text(hook_data)` and make `main()` use it. Keep behavior silent on invalid input and paused/down server. Keep `send_response()` unchanged except for type clarity.

Run the hook tests again. Expected: pass.

- [ ] **Task 3: Add automatic Codex hook installer in TypeScript**

In `extension/src/extension.ts`, split `ensureHookInstalled()` into:

- hook directory copy;
- Claude settings installer;
- Codex hooks installer.

Install Codex into `~/.codex/hooks.json` under `hooks.Stop`, preserving unrelated hooks and updating existing MathRender hook commands by matching `hook_send_formulas`.

Run:

```powershell
npm run compile
```

Expected: TypeScript compile passes.

- [ ] **Task 4: Update install/uninstall scripts for manual repo installs**

Update `install.py` to install both Claude and Codex hooks. Update `uninstall.py` to remove MathRender hooks from both `~/.claude/settings.json` and `~/.codex/hooks.json`.

Run Python hook tests again. Expected: pass.

- [ ] **Task 5: Update docs, metadata, and agent guidance**

Update package display name, description, keywords, view welcome text, README files, changelog, `AGENTS.md`, and `CLAUDE.md`. Bump `extension/package.json` and `extension/package-lock.json` from `0.7.1` to `0.8.0`.

- [ ] **Task 6: Verify and package**

Run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/ -v
npx @vscode/vsce package
git status --short
```

Expected: Python tests pass, TypeScript compile passes through VSCE prepublish, `mathrender-0.8.0.vsix` is produced, and git status contains only intended files.

- [ ] **Task 7: Commit and push**

Run:

```powershell
git add .
git commit -m "feat: add Codex auto-install support"
git push origin main
```

Expected: commit succeeds and push updates `origin/main`.
