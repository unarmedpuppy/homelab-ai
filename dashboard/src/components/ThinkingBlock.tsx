import { useState, useEffect } from 'react';

interface ThinkingBlockProps {
  thinking: string;
  isStreaming?: boolean;
  isThinkingComplete?: boolean;
}

export default function ThinkingBlock({
  thinking,
  isStreaming = false,
  isThinkingComplete = true,
}: ThinkingBlockProps) {
  const isActivelyThinking = isStreaming && !isThinkingComplete;
  const [isOpen, setIsOpen] = useState(isActivelyThinking);

  useEffect(() => {
    if (isActivelyThinking) {
      setIsOpen(true);
    } else if (!isStreaming) {
      setIsOpen(false);
    }
  }, [isActivelyThinking, isStreaming]);

  return (
    <div className="thinking-block">
      <button
        className="thinking-block-header"
        onClick={() => setIsOpen(o => !o)}
        aria-expanded={isOpen}
      >
        <span className={`thinking-block-chevron ${isOpen ? 'open' : ''}`}>▸</span>
        <span className="thinking-block-label">
          {isActivelyThinking ? 'Thinking...' : 'Thinking'}
        </span>
        {isActivelyThinking && <span className="thinking-block-dot" />}
      </button>
      <div className={`thinking-block-body ${isOpen ? 'open' : ''}`}>
        <div className="thinking-block-content">
          {thinking}
          {isActivelyThinking && <span className="thinking-block-cursor" />}
        </div>
      </div>
    </div>
  );
}
