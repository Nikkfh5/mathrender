#!/bin/bash
# MathRender — установка
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$HOME/.claude/settings.json"
HOOK_CMD="test -f $DIR/.enabled && python3 $DIR/hook_send_formulas.py"

echo "MathRender — установка"
echo "Директория: $DIR"
echo ""

# 1. Проверяем Python 3
if ! command -v python3 &>/dev/null; then
  echo "Ошибка: Python 3 не найден"
  exit 1
fi
echo "[OK] Python 3 найден"

# 2. Проверяем Claude Code settings
if [ ! -f "$SETTINGS" ]; then
  echo "Ошибка: $SETTINGS не найден. Установлен ли Claude Code?"
  exit 1
fi
echo "[OK] Claude Code settings найден"

# 3. Проверяем, не установлен ли уже хук
if grep -q "hook_send_formulas" "$SETTINGS" 2>/dev/null; then
  echo "[OK] Хук уже установлен в settings.json"
else
  # Добавляем хук через Python (безопасная работа с JSON)
  python3 -c "
import json, sys

with open('$SETTINGS', 'r') as f:
    settings = json.load(f)

hook_entry = {
    'hooks': [{
        'type': 'command',
        'command': '''$HOOK_CMD''',
        'timeout': 5,
        'async': True,
    }]
}

if 'hooks' not in settings:
    settings['hooks'] = {}

if 'Stop' not in settings['hooks']:
    settings['hooks']['Stop'] = []

# Проверяем что хук ещё не добавлен
existing = [h for entry in settings['hooks']['Stop'] for h in entry.get('hooks', []) if 'hook_send_formulas' in h.get('command', '')]
if not existing:
    settings['hooks']['Stop'].append(hook_entry)

# SessionEnd — автоматическое выключение при завершении сессии
if 'SessionEnd' not in settings['hooks']:
    settings['hooks']['SessionEnd'] = []
existing_end = [h for entry in settings['hooks']['SessionEnd'] for h in entry.get('hooks', []) if 'mathrender' in h.get('command', '')]
if not existing_end:
    settings['hooks']['SessionEnd'].append({
        'hooks': [{
            'type': 'command',
            'command': '$DIR/mathrender off',
            'timeout': 5,
        }]
    })

with open('$SETTINGS', 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
  echo "[OK] Хук добавлен в settings.json"
fi

# 4. Добавляем алиас в shell
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
  if grep -q "mathrender" "$SHELL_RC" 2>/dev/null; then
    echo "[OK] Алиас уже есть в $(basename "$SHELL_RC")"
  else
    echo "" >> "$SHELL_RC"
    echo "# MathRender — рендер LaTeX-формул из Claude Code" >> "$SHELL_RC"
    echo "alias mathrender=\"$DIR/mathrender\"" >> "$SHELL_RC"
    echo "[OK] Алиас добавлен в $(basename "$SHELL_RC")"
  fi
else
  echo "[!] Shell RC не найден. Добавь вручную:"
  echo "    alias mathrender=\"$DIR/mathrender\""
fi

# 5. Делаем скрипты исполняемыми
chmod +x "$DIR/mathrender" "$DIR/hook_send_formulas.py"

echo ""
echo "Установка завершена!"
echo ""
echo "Использование:"
echo "  mathrender on      — включить (запускает сервер + открывает окно)"
echo "  mathrender off     — выключить"
echo "  mathrender pause   — приостановить"
echo "  mathrender resume  — возобновить"
echo "  mathrender status  — проверить статус"
echo ""
echo "Перезапусти терминал или выполни: source $SHELL_RC"
