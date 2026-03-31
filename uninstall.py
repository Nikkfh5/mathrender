#!/usr/bin/env python3
"""MathRender — cross-platform uninstaller for Claude Code hooks."""

import json
import sys
from pathlib import Path


def uninstall():
    print("MathRender — uninstallation")

    settings_path = Path.home() / ".claude" / "settings.json"
    if not settings_path.exists():
        print("No settings.json found, nothing to uninstall.")
        return

    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    changed = False
    for event in ("Stop", "SessionEnd"):
        if "hooks" in settings and event in settings["hooks"]:
            before = len(settings["hooks"][event])
            settings["hooks"][event] = [
                entry for entry in settings["hooks"][event]
                if not any(
                    "mathrender" in h.get("command", "") or
                    "hook_send_formulas" in h.get("command", "")
                    for h in entry.get("hooks", [])
                )
            ]
            if len(settings["hooks"][event]) < before:
                changed = True
            if not settings["hooks"][event]:
                del settings["hooks"][event]

    if "hooks" in settings and not settings["hooks"]:
        del settings["hooks"]

    if changed:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("[OK] Hooks removed from settings.json")
    else:
        print("No MathRender hooks found in settings.json")

    print()
    print("To uninstall the VS Code extension:")
    print("  code --uninstall-extension mathrender.mathrender")


if __name__ == "__main__":
    uninstall()
