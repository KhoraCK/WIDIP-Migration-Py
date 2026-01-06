import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';
import type { Components } from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const components: Components = {
    // Code blocks
    code({ className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const isInline = !match && !className;

      if (isInline) {
        return (
          <code
            className="px-1.5 py-0.5 bg-bg-code rounded text-sm font-mono text-accent"
            {...props}
          >
            {children}
          </code>
        );
      }

      return (
        <CodeBlock language={match?.[1]}>
          {String(children).replace(/\n$/, '')}
        </CodeBlock>
      );
    },

    // Paragraphs
    p({ children }) {
      return <p className="mb-4 last:mb-0 leading-relaxed">{children}</p>;
    },

    // Headers
    h1({ children }) {
      return <h1 className="text-2xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>;
    },
    h2({ children }) {
      return <h2 className="text-xl font-bold mb-3 mt-5 first:mt-0">{children}</h2>;
    },
    h3({ children }) {
      return <h3 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h3>;
    },

    // Lists
    ul({ children }) {
      return <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>;
    },
    ol({ children }) {
      return <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>;
    },
    li({ children }) {
      return <li className="leading-relaxed">{children}</li>;
    },

    // Links
    a({ href, children }) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:text-accent-hover underline"
        >
          {children}
        </a>
      );
    },

    // Blockquotes
    blockquote({ children }) {
      return (
        <blockquote className="border-l-4 border-accent pl-4 my-4 italic text-text-secondary">
          {children}
        </blockquote>
      );
    },

    // Tables
    table({ children }) {
      return (
        <div className="overflow-x-auto my-4">
          <table className="min-w-full border border-border rounded-lg overflow-hidden">
            {children}
          </table>
        </div>
      );
    },
    thead({ children }) {
      return <thead className="bg-bg-secondary">{children}</thead>;
    },
    th({ children }) {
      return (
        <th className="px-4 py-2 text-left text-sm font-semibold border-b border-border">
          {children}
        </th>
      );
    },
    td({ children }) {
      return (
        <td className="px-4 py-2 text-sm border-b border-border">{children}</td>
      );
    },

    // Horizontal rule
    hr() {
      return <hr className="my-6 border-border" />;
    },

    // Strong/Bold
    strong({ children }) {
      return <strong className="font-semibold">{children}</strong>;
    },

    // Emphasis/Italic
    em({ children }) {
      return <em className="italic">{children}</em>;
    },
  };

  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
      {content}
    </ReactMarkdown>
  );
}
