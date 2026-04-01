import * as vscode from 'vscode';
import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';

const HOST = '127.0.0.1';
const PORT = 18573;
const MAX_BODY = 1024 * 1024; // 1 MB
const MAX_HISTORY = 500;
const PAGE_SIZE = 50;

interface HistoryEntry {
    type: string;
    text: string;
    timestamp: string;
}

const CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
};

let panel: vscode.WebviewPanel | undefined;
let server: http.Server | undefined;
let history: HistoryEntry[] = [];
let paused = false;

function addToHistory(entry: HistoryEntry): void {
    if (history.length >= MAX_HISTORY) {
        history.shift();
    }
    history.push(entry);
}

function readBody(req: http.IncomingMessage): Promise<string> {
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        let size = 0;
        req.on('data', (chunk: Buffer) => {
            size += chunk.length;
            if (size > MAX_BODY) {
                req.destroy();
                reject(new Error('Request too large'));
                return;
            }
            chunks.push(chunk);
        });
        req.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
        req.on('error', reject);
    });
}

function jsonResponse(res: http.ServerResponse, status: number, data: unknown): void {
    const body = JSON.stringify(data);
    res.writeHead(status, {
        'Content-Type': 'application/json; charset=utf-8',
        ...CORS_HEADERS,
    });
    res.end(body);
}

function startHttpServer(onResponse: (entry: HistoryEntry) => void): http.Server {
    const srv = http.createServer(async (req, res) => {
        const url = new URL(req.url || '/', `http://${HOST}:${PORT}`);

        if (req.method === 'OPTIONS') {
            res.writeHead(204, CORS_HEADERS);
            res.end();
            return;
        }

        try {
            if (req.method === 'GET') {
                switch (url.pathname) {
                    case '/health':
                        jsonResponse(res, 200, { status: 'ok', paused });
                        break;
                    case '/history': {
                        const offset = parseInt(url.searchParams.get('offset') || '0', 10) || 0;
                        const limit = parseInt(url.searchParams.get('limit') || String(history.length), 10) || history.length;
                        jsonResponse(res, 200, history.slice(offset, offset + limit));
                        break;
                    }
                    case '/status':
                        jsonResponse(res, 200, { paused });
                        break;
                    default:
                        jsonResponse(res, 404, { error: 'Not found' });
                }
            } else if (req.method === 'POST') {
                switch (url.pathname) {
                    case '/response': {
                        const body = await readBody(req);
                        let data: { text?: string; timestamp?: string };
                        try {
                            data = JSON.parse(body);
                        } catch {
                            data = { text: body };
                        }
                        const entry: HistoryEntry = {
                            type: 'response',
                            text: data.text || '',
                            timestamp: data.timestamp || new Date().toLocaleTimeString('ru-RU'),
                        };
                        addToHistory(entry);
                        onResponse(entry);
                        jsonResponse(res, 200, { ok: true });
                        break;
                    }
                    case '/formula': {
                        const body = await readBody(req);
                        let data: { formulas?: string[]; context?: string };
                        try {
                            data = JSON.parse(body);
                        } catch {
                            data = { formulas: [body] };
                        }
                        const entry: HistoryEntry = {
                            type: 'formulas',
                            text: JSON.stringify(data),
                            timestamp: new Date().toLocaleTimeString('ru-RU'),
                        };
                        addToHistory(entry);
                        onResponse(entry);
                        jsonResponse(res, 200, { ok: true, count: (data.formulas || []).length });
                        break;
                    }
                    case '/pause':
                        paused = true;
                        jsonResponse(res, 200, { paused });
                        panel?.webview.postMessage({ type: 'paused', paused: true });
                        break;
                    case '/resume':
                        paused = false;
                        jsonResponse(res, 200, { paused });
                        panel?.webview.postMessage({ type: 'paused', paused: false });
                        break;
                    case '/clear':
                        history = [];
                        jsonResponse(res, 200, { ok: true });
                        panel?.webview.postMessage({ type: 'clear' });
                        break;
                    default:
                        jsonResponse(res, 404, { error: 'Not found' });
                }
            } else {
                jsonResponse(res, 405, { error: 'Method not allowed' });
            }
        } catch (err) {
            console.error('[MathRender] Request error:', err);
            try {
                jsonResponse(res, 500, { error: 'Internal server error' });
            } catch {
                // response already sent or destroyed
            }
        }
    });

    srv.on('error', (err: NodeJS.ErrnoException) => {
        if (err.code === 'EADDRINUSE') {
            vscode.window.showErrorMessage(
                `MathRender: Port ${PORT} is already in use. Stop any existing MathRender server first.`
            );
        } else {
            vscode.window.showErrorMessage(`MathRender: Server error: ${err.message}`);
        }
    });

    srv.listen(PORT, HOST, () => {
        console.log(`MathRender server running on http://${HOST}:${PORT}`);
    });

    return srv;
}

let cachedHtml: string | undefined;

function getWebviewHtml(extensionUri: vscode.Uri): string {
    if (!cachedHtml) {
        const htmlPath = path.join(extensionUri.fsPath, 'media', 'index.html');
        try {
            cachedHtml = fs.readFileSync(htmlPath, 'utf-8');
        } catch (err) {
            console.error('[MathRender] Failed to read index.html:', err);
            return '<html><body><h1>Error: index.html not found</h1></body></html>';
        }
    }
    return cachedHtml;
}

function showPanel(context: vscode.ExtensionContext): void {
    if (!server) {
        server = startHttpServer((entry) => {
            try {
                panel?.webview.postMessage(entry);
            } catch (err) {
                console.error('[MathRender] postMessage error:', err);
            }
        });
    }

    if (panel) {
        panel.reveal();
        return;
    }

    panel = vscode.window.createWebviewPanel(
        'mathrender',
        'MathRender',
        vscode.ViewColumn.Two,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
        }
    );

    panel.webview.html = getWebviewHtml(context.extensionUri);

    // Send history in pages to avoid flooding WebView
    if (history.length > 0) {
        for (let i = 0; i < history.length; i += PAGE_SIZE) {
            const page = history.slice(i, i + PAGE_SIZE);
            panel.webview.postMessage({ type: 'history', entries: page });
        }
    }

    // Handle messages from WebView (pause/resume/clear)
    panel.webview.onDidReceiveMessage(
        (message) => {
            switch (message.command) {
                case 'pause':
                    paused = true;
                    break;
                case 'resume':
                    paused = false;
                    break;
                case 'clear':
                    history = [];
                    break;
            }
        },
        undefined,
        context.subscriptions
    );

    panel.onDidDispose(
        () => {
            panel = undefined;
        },
        null,
        context.subscriptions
    );
}

function stopAll(): void {
    if (server) {
        server.close();
        server = undefined;
    }
    if (panel) {
        panel.dispose();
        panel = undefined;
    }
    history = [];
    paused = false;
    cachedHtml = undefined;
    vscode.window.showInformationMessage('MathRender disabled');
}

export function activate(context: vscode.ExtensionContext): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('mathrender.show', () => showPanel(context)),
        vscode.commands.registerCommand('mathrender.on', () => showPanel(context)),
        vscode.commands.registerCommand('mathrender.off', () => stopAll()),
    );
}

export function deactivate(): void {
    if (server) {
        server.close();
        server = undefined;
    }
    panel = undefined;
    cachedHtml = undefined;
}
