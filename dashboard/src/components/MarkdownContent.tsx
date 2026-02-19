import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

// Custom components for retro theme styling
const components: Components = {
  // Code blocks
  pre: ({ children }) => (
    <pre className="bg-[var(--retro-bg-dark)] border border-[var(--retro-border)] rounded p-3 my-2 overflow-x-auto text-sm font-mono">
      {children}
    </pre>
  ),
  code: ({ className, children, ...props }) => {
    const isInline = !className;
    if (isInline) {
      return (
        <code className="bg-[var(--retro-bg-light)] px-1.5 py-0.5 rounded text-[var(--retro-accent-cyan)] text-sm font-mono" {...props}>
          {children}
        </code>
      );
    }
    return (
      <code className="text-[var(--retro-text-primary)]" {...props}>
        {children}
      </code>
    );
  },
  // Headers
  h1: ({ children }) => (
    <h1 className="text-xl font-bold text-[var(--retro-text-primary)] mt-4 mb-2">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-semibold text-[var(--retro-text-primary)] mt-3 mb-2 uppercase tracking-wide">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-semibold text-[var(--retro-text-secondary)] mt-2 mb-1">
      {children}
    </h3>
  ),
  // Lists
  ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="text-[var(--retro-text-primary)]">{children}</li>,
  // Links
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-[var(--retro-accent-cyan)] hover:text-[var(--retro-accent-green)] hover:underline transition-colors"
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  ),
  // Block elements
  p: ({ children }) => <p className="my-2">{children}</p>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-[var(--retro-accent-cyan)] pl-4 my-2 text-[var(--retro-text-secondary)] italic bg-[var(--retro-bg-light)] py-2 rounded-r">
      {children}
    </blockquote>
  ),
  // Tables
  table: ({ children }) => (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full border border-[var(--retro-border)] text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-[var(--retro-bg-light)]">{children}</thead>,
  th: ({ children }) => (
    <th className="px-3 py-2 border border-[var(--retro-border)] text-left font-semibold text-[var(--retro-text-secondary)] uppercase text-xs tracking-wider">
      {children}
    </th>
  ),
  td: ({ children }) => <td className="px-3 py-2 border border-[var(--retro-border)]">{children}</td>,
  // Horizontal rule
  hr: () => <hr className="border-[var(--retro-border)] my-4" />,
  // Strong/emphasis
  strong: ({ children }) => <strong className="font-bold text-[var(--retro-text-primary)]">{children}</strong>,
  em: ({ children }) => <em className="italic text-[var(--retro-text-secondary)]">{children}</em>,
};

export default function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`text-[var(--retro-text-primary)] text-sm ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
