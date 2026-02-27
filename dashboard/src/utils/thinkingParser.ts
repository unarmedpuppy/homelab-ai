export interface ParsedContent {
  thinking: string | null;
  response: string;
  isThinkingComplete: boolean;
}

// Matches <thinking> (Claude) and <think> (Qwen/DeepSeek) tags
const OPEN_TAG = /^<think(?:ing)?>/;
const COMPLETE_RE = /^<think(?:ing)?>([\s\S]*?)<\/think(?:ing)?>([\s\S]*)$/;
const PARTIAL_RE = /^<think(?:ing)?>([\s\S]*)$/;

export function parseThinkingContent(raw: string): ParsedContent {
  // Complete thinking block followed by optional response
  const completeMatch = raw.match(COMPLETE_RE);
  if (completeMatch) {
    return {
      thinking: completeMatch[1].trim(),
      response: completeMatch[2].trimStart(),
      isThinkingComplete: true,
    };
  }

  // Partial: opening tag exists but closing tag not yet received (streaming)
  if (OPEN_TAG.test(raw)) {
    const partialMatch = raw.match(PARTIAL_RE);
    if (partialMatch) {
      return {
        thinking: partialMatch[1],
        response: '',
        isThinkingComplete: false,
      };
    }
  }

  return {
    thinking: null,
    response: raw,
    isThinkingComplete: false,
  };
}
