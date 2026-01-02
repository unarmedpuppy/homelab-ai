import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';

interface MarkdownContentProps {
  content: string;
  className?: string;
}

// Custom components for dark theme styling
const components: Components = {
  // Code blocks
  pre: ({ children }) => (
    <pre className="bg-gray-950 border border-gray-700 rounded p-3 my-2 overflow-x-auto text-sm">
      {children}
    </pre>
  ),
  code: ({ className, children, ...props }) => {
    const isInline = !className;
    if (isInline) {
      return (
        <code className="bg-gray-800 px-1.5 py-0.5 rounded text-blue-300 text-sm" {...props}>
          {children}
        </code>
      );
    }
    return (
      <code className="text-gray-300" {...props}>
        {children}
      </code>
    );
  },
  // Headers
  h1: ({ children }) => <h1 className="text-xl font-bold text-white mt-4 mb-2">{children}</h1>,
  h2: ({ children }) => <h2 className="text-lg font-semibold text-white mt-3 mb-2">{children}</h2>,
  h3: ({ children }) => <h3 className="text-base font-semibold text-gray-200 mt-2 mb-1">{children}</h3>,
  // Lists
  ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="text-gray-300">{children}</li>,
  // Links
  a: ({ href, children }) => (
    <a href={href} className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
  // Block elements
  p: ({ children }) => <p className="my-2">{children}</p>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-gray-600 pl-4 my-2 text-gray-400 italic">
      {children}
    </blockquote>
  ),
  // Tables
  table: ({ children }) => (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full border border-gray-700 text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-gray-800">{children}</thead>,
  th: ({ children }) => <th className="px-3 py-2 border border-gray-700 text-left font-semibold">{children}</th>,
  td: ({ children }) => <td className="px-3 py-2 border border-gray-700">{children}</td>,
  // Horizontal rule
  hr: () => <hr className="border-gray-700 my-4" />,
  // Strong/emphasis
  strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
};

export default function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`text-gray-300 text-sm ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
