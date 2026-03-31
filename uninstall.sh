#!/bin/bash
# MathRender — удаление
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS="$HOME/.claude/settings.json"

echo "MathRender — удаление"

# 1. Останавливаем сервер
"$DIR/mathrender" off 2>/dev/null || true
echo "[OK] Сервер остановлен"

# 2. Убираем хук из settings.json
if [ -f "$SETTINGS" ] && grep -q "hook_send_formulas" "$SETTINGS"; then
  python3 -c "
import json

with open('$SETTINGS', 'r') as f:
    settings = json.load(f)

for event in ('Stop', 'SessionEnd'):
    if 'hooks' in settings and event in settings['hooks']:
        settings['hooks'][event] = [
            entry for entry in settings['hooks'][event]
            if not any('mathrender' in h.get('command', '') or 'hook_send_formulas' in h.get('command', '')
                       for h in entry.get('hooks', []))
        ]
        if not settings['hooks'][event]:
            del settings['hooks'][event]
if 'hooks' in settings and not settings['hooks']:
    del settings['hooks']

with open('$SETTINGS', 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write('\n')
"
  echo "[OK] Хук удалён из settings.json"
fi

# 3. Убираем алиас из shell RC
for RC in "$HOME/.zshrc" "$HOME/.bashrc"; do
  if [ -f "$RC" ] && grep -q "mathrender" "$RC"; then
    grep -v "# MathRender\|alias mathrender" "$RC" > "$RC.tmp" && mv "$RC.tmp" "$RC"
    echo "[OK] Алиас удалён из $(basename "$RC")"
  fi
done

# 4. Чистим рабочие файлы
rm -f "$DIR/.enabled" "$DIR/.server.pid"

echo ""
echo "MathRender удалён. Файлы проекта остались в $DIR"
echo "Для полного удаления: rm -rf $DIR"
