const assert = require('assert');

const {
  containsRenderableFormula,
  extractCodexAgentMessage,
} = require('../out/codexTranscript');

function testExtractsAgentMessage() {
  const line = JSON.stringify({
    type: 'event_msg',
    payload: {
      type: 'agent_message',
      message: 'Formula: $$E = mc^2$$',
      phase: 'final_answer',
    },
  });

  assert.strictEqual(extractCodexAgentMessage(line), 'Formula: $$E = mc^2$$');
}

function testIgnoresNonAgentMessage() {
  const line = JSON.stringify({
    type: 'response_item',
    payload: { type: 'message', role: 'assistant' },
  });

  assert.strictEqual(extractCodexAgentMessage(line), undefined);
}

function testIgnoresMalformedJson() {
  assert.strictEqual(extractCodexAgentMessage('{not json'), undefined);
}

function testDetectsRenderableFormula() {
  assert.strictEqual(containsRenderableFormula('Here is $$\\frac{1}{3}$$'), true);
  assert.strictEqual(containsRenderableFormula('Here is \\[x^2 + y^2\\]'), true);
  assert.strictEqual(containsRenderableFormula('Plain text only.'), false);
}

function testIgnoresFormulaInsideCodeFence() {
  const text = '```tex\n$$x^2$$\n```';
  assert.strictEqual(containsRenderableFormula(text), false);
}

testExtractsAgentMessage();
testIgnoresNonAgentMessage();
testIgnoresMalformedJson();
testDetectsRenderableFormula();
testIgnoresFormulaInsideCodeFence();

console.log('codexTranscript tests passed');
