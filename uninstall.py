#!/usr/bin/env python3
"""MathRender — cross-platform uninstaller for agent hooks."""

import json
from pathlib import Path

CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
CODEX_HOOKS = Path.home() / ".codex" / "hooks.json"


def remove_mathrender_hooks(path: Path) -> bool:
    if not path.exists():
        print(f"[OK] {path} not found")
        return False

    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    if not isinstance(settings, dict):
        print(f"[OK] {path} does not contain a settings object")
        return False

    changed = False
    for event in ("Stop", "SessionEnd"):
        if isinstance(settings.get("hooks"), dict) and isinstance(settings["hooks"].get(event), list):
            before = len(settings["hooks"][event])
            settings["hooks"][event] = [
                entry for entry in settings["hooks"][event]
                if not entry_has_mathrender_hook(entry)
            ]
            if len(settings["hooks"][event]) < before:
                changed = True
            if not settings["hooks"][event]:
                del settings["hooks"][event]

    if isinstance(settings.get("hooks"), dict) and not settings["hooks"]:
        del settings["hooks"]

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"[OK] Hooks removed from {path}")
    else:
        print(f"[OK] No MathRender hooks found in {path}")

    return changed


def entry_has_mathrender_hook(entry) -> bool:
    if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
        return False

    for hook in entry["hooks"]:
        if not isinstance(hook, dict):
            continue
        command = hook.get("command", "")
        if isinstance(command, str) and ("mathrender" in command or "hook_send_formulas" in command):
            return True
    return False


def uninstall():
    print("MathRender — uninstallation")

    remove_mathrender_hooks(CLAUDE_SETTINGS)
    remove_mathrender_hooks(CODEX_HOOKS)

    print()
    print("To uninstall the VS Code extension:")
    print("  code --uninstall-extension mathrender.mathrender")


if __name__ == "__main__":
    uninstall()
