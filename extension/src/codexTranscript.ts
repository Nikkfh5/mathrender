const LATEX_QUICK_CHECK = /\$\$[\s\S]+?\$\$|\$[^$\n]+\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)/;
const CODE_BLOCK = /```[\s\S]*?```|`[^`]+`|(?<=\n\n)(?: {4}|\t).+(?:\n(?: {4}|\t).+)*/g;

export function extractCodexAgentMessage(line: string): string | undefined {
    let parsed: unknown;
    try {
        parsed = JSON.parse(line);
    } catch {
        return undefined;
    }

    if (!parsed || typeof parsed !== 'object') {
        return undefined;
    }

    const item = parsed as { type?: unknown; payload?: unknown };
    if (item.type !== 'event_msg' || !item.payload || typeof item.payload !== 'object') {
        return undefined;
    }

    const payload = item.payload as { type?: unknown; message?: unknown };
    if (payload.type !== 'agent_message' || typeof payload.message !== 'string') {
        return undefined;
    }

    return payload.message;
}

export function containsRenderableFormula(text: string): boolean {
    const clean = text.replace(CODE_BLOCK, '');
    return LATEX_QUICK_CHECK.test(clean);
}
