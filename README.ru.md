# MathRender

Рендерит LaTeX-формулы из ответов AI coding agents в панели VS Code. Вместо сырого `$$\int_0^1 x^2 dx$$` в терминале вы видите красиво отрисованную математику в реальном времени.

Поддерживаемые агенты:

- Codex
- Claude Code

## Как Это Работает

```
Codex или Claude Code отвечает с формулами
        |
    Срабатывает Stop hook агента
        |
    Python hook находит LaTeX вне code blocks
        |
    Отправляет ответ в VS Code extension через localhost HTTP
        |
    WebView-панель рендерит markdown + KaTeX
```

Расширение держит локальный HTTP-сервер и UI. Hook-скрипт только нормализует payload агента и отправляет ответы с формулами в `http://127.0.0.1:18573/response`.

## Возможности

- Поддержка Codex и Claude Code
- Автоустановка hooks при активации расширения
- Полный рендер ответа: текст и формулы вместе
- Python hook без внешних Python-зависимостей
- История, поиск, копирование исходного markdown/LaTeX
- Пауза/возобновление захвата
- Команда тестовой формулы без запуска агента

## Требования

- VS Code 1.85+
- Python 3.10+
- Codex и/или Claude Code

## Установка

### Marketplace

Установите MathRender из VS Code Marketplace и выполните:

```
MathRender: Show Panel
```

При активации MathRender копирует hook в `~/.mathrender/hook_send_formulas.py` и автоматически устанавливает конфиги:

- Codex: `~/.codex/hooks.json`
- Claude Code: `~/.claude/settings.json`

Важно: Codex может потребовать подтвердить новый или изменённый hook через `/hooks`. MathRender ставит hook автоматически, но trust-gate контролирует сам Codex.

### Из Исходников

```bash
python install.py
cd extension
npm install
npm run compile
npx @vscode/vsce package
code --install-extension mathrender-*.vsix
```

## Использование

В VS Code откройте Command Palette (`Ctrl+Shift+P`) и выполните:

- **MathRender: Show Panel** - открыть панель и запустить сервер
- **MathRender: Disable** - остановить сервер и закрыть панель
- **MathRender: Status** - показать сервер, hooks, историю и pause state
- **MathRender: Send Test Formula** - отправить тестовую формулу без Codex/Claude

По умолчанию MathRender выключен. Откройте панель, когда он нужен.

## Структура Проекта

```
extension/              VS Code extension
  src/extension.ts      HTTP server, WebView, commands, hook installers
  media/index.html      Frontend: markdown + KaTeX rendering
  media/hook_send_formulas.py
hook_send_formulas.py   Общий hook для Codex/Claude
install.py              Ручной установщик hooks
uninstall.py            Ручное удаление hooks
tests/                  Python-тесты hook-логики
```

## Тесты

На машинах с глобальными pytest-плагинами лучше отключать их автозагрузку:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest tests/ -v
cd extension
npm run compile
```

## Дисклеймер

Это независимый community-проект. Он не связан официально с OpenAI, Anthropic, Codex или Claude Code.

## Лицензия

[MIT](LICENSE)
