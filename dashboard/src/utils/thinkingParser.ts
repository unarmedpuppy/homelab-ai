export interface ParsedContent {
  thinking: string | null;
  response: string;
  isThinkingComplete: boolean;
}

export function parseThinkingContent(raw: string): ParsedContent {
  // Complete thinking block: <thinking>...</thinking> followed by optional response
  const completeMatch = raw.match(/^<thinking>([\s\S]*?)<\/thinking>([\s\S]*)$/);
  if (completeMatch) {
    return {
      thinking: completeMatch[1].trim(),
      response: completeMatch[2].trimStart(),
      isThinkingComplete: true,
    };
  }

  // Partial: opening tag exists but closing tag not yet received (streaming)
  const partialMatch = raw.match(/^<thinking>([\s\S]*)$/);
  if (partialMatch) {
    return {
      thinking: partialMatch[1],
      response: '',
      isThinkingComplete: false,
    };
  }

  return {
    thinking: null,
    response: raw,
    isThinkingComplete: false,
  };
}
