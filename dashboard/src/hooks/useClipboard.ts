import { useState, useCallback, useRef } from 'react';

export function useClipboard(resetDelay = 2000) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const copy = useCallback((text: string, id?: string) => {
    navigator.clipboard.writeText(text).then(() => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setCopiedId(id ?? text);
      timeoutRef.current = setTimeout(() => setCopiedId(null), resetDelay);
    });
  }, [resetDelay]);

  return { copiedId, copy };
}
