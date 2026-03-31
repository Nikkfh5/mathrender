# MathRender

Рендерит LaTeX-формулы из Claude Code в панели VS Code. Вместо сырого `$$\int_0^1 x^2 dx$$` в терминале — красивые формулы в реальном времени.

## Как это работает

```
Claude Code отвечает с формулами
        |
    Срабатывает хук (Stop-событие)
        |
    Парсит LaTeX из ответа
        |
    Отправляет в VS Code расширение (localhost HTTP)
        |
    WebView-панель рендерит markdown + KaTeX
```

- Полный рендер ответа: текст + формулы вместе, как в учебнике
- Без настройки: открыл панель — работает
- Без зависимостей: Python 3 stdlib для хука, KaTeX с CDN
- История: можно скроллить назад и смотреть все ответы за сессию
- Пауза: можно приостановить без закрытия панели

## Требования

- **Windows** (также работает на macOS/Linux)
- Python 3.10+
- Claude Code CLI или VS Code extension
- VS Code

## Установка

### 1. Добавить хук в Claude Code

```bash
python install.py
```

### 2. Собрать и установить VS Code расширение

```bash
cd extension
npm install
npm run compile
npx @vscode/vsce package
code --install-extension mathrender-0.1.0.vsix
```

## Использование

В VS Code откройте Command Palette (`Ctrl+Shift+P`) и выполните:

- **MathRender: Show Panel** — открыть панель с формулами (также запускает сервер)
- **MathRender: Disable** — выключить всё

По умолчанию MathRender **выключен**. Откройте панель когда нужно. Она остаётся активной пока не выключите или не закроете VS Code.

## Удаление

```bash
python uninstall.py
code --uninstall-extension mathrender.mathrender
```

## Структура проекта

```
extension/              VS Code расширение (TypeScript)
  src/extension.ts      HTTP-сервер + WebView + команды
  media/index.html      Фронтенд: рендер markdown + KaTeX
  package.json          Манифест расширения
hook_send_formulas.py   Хук Claude Code (Stop-событие)
install.py              Установщик хуков
uninstall.py            Удаление хуков
tests/                  Тесты
```

## Как работает хук

Хук настроен как асинхронное Stop-событие в Claude Code. На каждый ответ:

1. Python проверяет, запущен ли сервер MathRender (HTTP health check)
2. Если запущен и не на паузе — проверяет, есть ли в ответе LaTeX (`$$...$$`, `$...$`, `\[...\]`, `\(...\)`)
3. Если формулы найдены — отправляет полный текст ответа в VS Code расширение
4. Расширение передаёт данные в WebView-панель через postMessage
5. WebView рендерит markdown с KaTeX

## Запуск тестов

```bash
python -m pytest tests/ -v
```

## Дисклеймер

Это независимый проект сообщества. Он не связан с [Anthropic](https://anthropic.com), не одобрен и не поддерживается ими. Claude Code — продукт Anthropic.

## Лицензия

[MIT](LICENSE)
