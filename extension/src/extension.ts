import * as vscode from 'vscode';
import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

const HOST = '127.0.0.1';
let PORT = 18573; // overridden from mathrender.port setting in activate()
const MAX_BODY = 1024 * 1024; // 1 MB
const MAX_HISTORY = 500;
const PAGE_SIZE = 50;
const HOOK_DIR = path.join(os.homedir(), '.mathrender');
const HOOK_FILE = path.join(HOOK_DIR, 'hook_send_formulas.py');
const HISTORY_FILE = path.join(HOOK_DIR, 'history.json');
const CLAUDE_SETTINGS = path.join(os.homedir(), '.claude', 'settings.json');

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
let unreadCount = 0;
let sidebarView: vscode.TreeView<string> | undefined;

// --- Helpers ---

function atomicWrite(filePath: string, content: string): void {
    const tmp = filePath + '.tmp';
    fs.writeFileSync(tmp, content, 'utf-8');
    fs.renameSync(tmp, filePath);
}

function setRestrictivePerms(filePath: string): void {
    if (process.platform !== 'win32') {
        try { fs.chmodSync(filePath, 0o600); } catch { /* ignore */ }
    }
}

function setRestrictiveDirPerms(dirPath: string): void {
    if (process.platform !== 'win32') {
        try { fs.chmodSync(dirPath, 0o700); } catch { /* ignore */ }
    }
}

// --- Hook auto-install ---

function ensureHookInstalled(extensionUri: vscode.Uri): void {
    try {
        if (!fs.existsSync(HOOK_DIR)) {
            fs.mkdirSync(HOOK_DIR, { recursive: true });
        }
        setRestrictiveDirPerms(HOOK_DIR);
        const srcHook = path.join(extensionUri.fsPath, 'media', 'hook_send_formulas.py');
        if (fs.existsSync(srcHook)) {
            const srcContent = fs.readFileSync(srcHook);
            const dstExists = fs.existsSync(HOOK_FILE);
            if (!dstExists || !srcContent.equals(fs.readFileSync(HOOK_FILE))) {
                fs.copyFileSync(srcHook, HOOK_FILE);
                setRestrictivePerms(HOOK_FILE);
            }
        }

        if (!fs.existsSync(CLAUDE_SETTINGS)) {
            return;
        }

        const raw = fs.readFileSync(CLAUDE_SETTINGS, 'utf-8');
        let settings: Record<string, unknown>;
        try {
            settings = JSON.parse(raw);
        } catch {
            return;
        }

        const hookPath = HOOK_FILE.replace(/\\/g, '/');
        const isWindows = process.platform === 'win32';
        const hookCmd = isWindows
            ? `python "${hookPath}"`
            : `python3 "${hookPath}"`;

        if (!settings.hooks || typeof settings.hooks !== 'object') {
            settings.hooks = {};
        }
        const hooks = settings.hooks as Record<string, unknown[]>;

        if (!Array.isArray(hooks.Stop)) {
            hooks.Stop = [];
        }

        // Find existing hook entry and check if path needs updating
        let found = false;
        let updated = false;
        for (const entry of hooks.Stop as any[]) {
            for (const h of entry?.hooks || []) {
                if (typeof h?.command === 'string' && h.command.includes('hook_send_formulas')) {
                    found = true;
                    if (h.command !== hookCmd) {
                        h.command = hookCmd;
                        updated = true;
                    }
                }
            }
        }

        if (!found) {
            hooks.Stop.push({
                hooks: [{
                    type: 'command',
                    command: hookCmd,
                    timeout: 5,
                    async: true,
                }]
            });
            updated = true;
        }

        if (updated) {
            atomicWrite(CLAUDE_SETTINGS, JSON.stringify(settings, null, 2) + '\n');
            vscode.window.showInformationMessage(
                found ? 'MathRender: Hook path updated' : 'MathRender: Hook installed for Claude Code'
            );
        }
    } catch (err) {
        console.error('[MathRender] Hook install error:', err);
    }
}

// --- History persistence ---

function loadHistory(): void {
    try {
        if (fs.existsSync(HISTORY_FILE)) {
            const raw = fs.readFileSync(HISTORY_FILE, 'utf-8');
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) {
                history = parsed.slice(-MAX_HISTORY);
            }
        }
    } catch (err) {
        console.error('[MathRender] Failed to load history:', err);
    }
}

function saveHistory(): void {
    try {
        if (!fs.existsSync(HOOK_DIR)) {
            fs.mkdirSync(HOOK_DIR, { recursive: true });
            setRestrictiveDirPerms(HOOK_DIR);
        }
        atomicWrite(HISTORY_FILE, JSON.stringify(history));
        setRestrictivePerms(HISTORY_FILE);
    } catch (err) {
        console.error('[MathRender] Failed to save history:', err);
    }
}

// --- Badge ---

function updateBadge(): void {
    if (sidebarView) {
        sidebarView.badge = unreadCount > 0
            ? { value: unreadCount, tooltip: `${unreadCount} new formulas` }
            : undefined;
    }
}

// --- History ---

function addToHistory(entry: HistoryEntry): void {
    if (history.length >= MAX_HISTORY) {
        history.shift();
    }
    history.push(entry);
}

// --- HTTP ---

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
                            timestamp: data.timestamp || new Date().toLocaleTimeString(),
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
                            timestamp: new Date().toLocaleTimeString(),
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
                        saveHistory();
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

// --- WebView ---

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
            // Badge: increment if panel not visible
            if (!panel || !panel.visible) {
                unreadCount++;
                updateBadge();
            }
            saveHistory();
        });
    }

    if (panel) {
        panel.reveal();
        unreadCount = 0;
        updateBadge();
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

    // Send user-defined KaTeX macros to webview
    const macros = vscode.workspace.getConfiguration('mathrender').get<Record<string, string>>('macros', {});
    if (Object.keys(macros).length > 0) {
        panel.webview.postMessage({ type: 'config', macros });
    }

    if (history.length > 0) {
        for (let i = 0; i < history.length; i += PAGE_SIZE) {
            const page = history.slice(i, i + PAGE_SIZE);
            panel.webview.postMessage({ type: 'history', entries: page });
        }
    }

    // Reset badge when panel becomes visible
    panel.onDidChangeViewState(() => {
        if (panel?.visible) {
            unreadCount = 0;
            updateBadge();
        }
    });

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
                    saveHistory();
                    break;
                case 'export': {
                    const texContent = history
                        .filter(e => e.type === 'response')
                        .map(e => e.text)
                        .join('\n\n---\n\n');
                    vscode.workspace.openTextDocument({
                        content: texContent,
                        language: 'latex',
                    }).then(doc => vscode.window.showTextDocument(doc));
                    break;
                }
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

    unreadCount = 0;
    updateBadge();
}

function stopAll(): void {
    saveHistory();
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
    unreadCount = 0;
    updateBadge();
    vscode.window.showInformationMessage('MathRender disabled');
}

// --- Activation ---

export function activate(context: vscode.ExtensionContext): void {
    PORT = vscode.workspace.getConfiguration('mathrender').get<number>('port', 18573);

    ensureHookInstalled(context.extensionUri);
    loadHistory();

    // Sidebar tree view for badge
    const treeDataProvider: vscode.TreeDataProvider<string> = {
        getTreeItem: () => new vscode.TreeItem(''),
        getChildren: () => [],
    };
    sidebarView = vscode.window.createTreeView('mathrender.sidebar', {
        treeDataProvider,
    });
    context.subscriptions.push(sidebarView);

    context.subscriptions.push(
        vscode.commands.registerCommand('mathrender.show', () => showPanel(context)),
        vscode.commands.registerCommand('mathrender.on', () => showPanel(context)),
        vscode.commands.registerCommand('mathrender.off', () => stopAll()),
        vscode.commands.registerCommand('mathrender.status', () => {
            const parts = [
                `Server: ${server ? `running on port ${PORT}` : 'stopped'}`,
                `Hook: ${fs.existsSync(HOOK_FILE) ? HOOK_FILE : 'not found'}`,
                `History: ${history.length}/${MAX_HISTORY} entries`,
                `State: ${paused ? 'paused' : 'active'}`,
            ];
            vscode.window.showInformationMessage(parts.join('  |  '));
        }),
        vscode.commands.registerCommand('mathrender.sendTest', () => {
            if (!server) {
                showPanel(context);
            }
            const entry: HistoryEntry = {
                type: 'response',
                text: 'Test: $$E = mc^2$$ and $$\\int_{-\\infty}^{\\infty} e^{-x^2}\\,dx = \\sqrt{\\pi}$$',
                timestamp: new Date().toLocaleTimeString(),
            };
            addToHistory(entry);
            panel?.webview.postMessage(entry);
            saveHistory();
        }),
    );
}

export function deactivate(): void {
    saveHistory();
    if (server) {
        server.close();
        server = undefined;
    }
    panel = undefined;
    cachedHtml = undefined;
}
