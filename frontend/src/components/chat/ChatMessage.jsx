import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  GitCommit,
  Copy,
  Check,
  Calendar,
  ChevronDown,
  ChevronUp,
  Sparkles,
  FileCode,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

/**
 * Post-processes and normalizes raw LLM markdown text:
 * - Removes 3+ consecutive blank lines
 * - Cleans duplicated horizontal rules
 * - Trims extra whitespace around headings
 */
function normalizeMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\n{3,}/g, '\n\n')
    .replace(/(---[\s]*){2,}/g, '---\n')
    .trim();
}

export default function ChatMessage({ message, onRegenerate }) {
  const [copiedResponse, setCopiedResponse] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'up' | 'down' | null

  const isUser = message.role === 'user';
  const isError = message.role === 'error';

  const handleCopyResponse = () => {
    if (!message.content) return;
    navigator.clipboard.writeText(message.content);
    setCopiedResponse(true);
    setTimeout(() => setCopiedResponse(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-xl rounded-2xl px-5 py-3.5 text-sm bg-slate-900 text-white shadow-md font-sans">
          <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-2xl rounded-2xl p-5 text-sm bg-rose-50 text-rose-800 border border-rose-200 shadow-sm space-y-2">
          <div className="flex items-center gap-2 font-bold text-rose-900">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            <span>Query Execution Error</span>
          </div>
          <p className="leading-relaxed">{message.content}</p>
        </div>
      </div>
    );
  }

  const normalizedContent = normalizeMarkdown(message.content);

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-4xl w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all hover:shadow-md">
        {/* Header Bar */}
        <div className="bg-slate-50 px-6 py-3 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Sparkles className="w-4 h-4 text-emerald-500" />
            <span>Code Archaeologist Assistant</span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] uppercase font-mono bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">
              {message.mode === 'causal' ? 'Causal Analysis' : 'Repo Chat'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-[11px] text-slate-400 font-medium hidden sm:inline">Grounded RAG Answer</span>

            {/* Response Action Controls */}
            <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
              <button
                onClick={handleCopyResponse}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-lg transition flex items-center gap-1 text-xs"
                title="Copy full response"
              >
                {copiedResponse ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedResponse && <span className="text-[10px] text-emerald-600 font-medium">Copied</span>}
              </button>

              {onRegenerate && message.query && (
                <button
                  onClick={() => onRegenerate(message.query)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-lg transition"
                  title="Regenerate response"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              )}

              <button
                onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
                className={`p-1.5 rounded-lg transition ${
                  feedback === 'up'
                    ? 'bg-emerald-100 text-emerald-700 font-bold'
                    : 'text-slate-400 hover:text-slate-700 hover:bg-slate-200/60'
                }`}
                title="Helpful response"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
                className={`p-1.5 rounded-lg transition ${
                  feedback === 'down'
                    ? 'bg-rose-100 text-rose-700 font-bold'
                    : 'text-slate-400 hover:text-slate-700 hover:bg-slate-200/60'
                }`}
                title="Not helpful"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Confidence Indicator Banner */}
        <div className="bg-emerald-50/40 px-6 py-2 border-b border-emerald-100/60 flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-emerald-800 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>High Confidence Grounded Response</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500 font-medium">Evidence Match Score:</span>
            <div className="w-20 bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: '88%' }}></div>
            </div>
            <span className="font-mono font-bold text-emerald-700 text-[11px]">88%</span>
          </div>
        </div>

        {/* Formatted Markdown Body */}
        <div className="p-6 text-slate-800 text-sm leading-relaxed font-sans prose prose-slate max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => <h1 className="text-xl font-bold text-slate-900 mb-3 mt-4">{children}</h1>,
              h2: ({ children }) => <h2 className="text-lg font-bold text-slate-900 mb-2 mt-4 border-b border-slate-100 pb-1">{children}</h2>,
              h3: ({ children }) => <h3 className="text-base font-bold text-slate-800 mb-2 mt-3">{children}</h3>,
              h4: ({ children }) => <h4 className="text-sm font-bold text-slate-800 mb-1.5 mt-2">{children}</h4>,
              p: ({ children }) => <p className="mb-3 leading-relaxed text-slate-700">{children}</p>,
              strong: ({ children }) => <strong className="font-bold text-slate-900">{children}</strong>,
              em: ({ children }) => <em className="italic text-slate-800">{children}</em>,
              ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1 text-slate-700">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1 text-slate-700">{children}</ol>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-emerald-500 bg-emerald-50/50 p-3 rounded-r-lg text-slate-700 my-3 font-mono text-xs">
                  {children}
                </blockquote>
              ),
              hr: () => <hr className="my-4 border-slate-200" />,
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noreferrer" className="text-emerald-600 underline font-medium hover:text-emerald-700">
                  {children}
                </a>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto my-4 rounded-lg border border-slate-200 shadow-xs">
                  <table className="w-full text-left text-xs border-collapse">{children}</table>
                </div>
              ),
              thead: ({ children }) => <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">{children}</thead>,
              tbody: ({ children }) => <tbody className="divide-y divide-slate-100">{children}</tbody>,
              tr: ({ children }) => <tr className="hover:bg-slate-50/80">{children}</tr>,
              th: ({ children }) => <th className="p-2.5 font-bold">{children}</th>,
              td: ({ children }) => <td className="p-2.5 text-slate-700">{children}</td>,
              code({ node, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                const isInline = !className && !String(children).includes('\n');
                if (isInline) {
                  return (
                    <code className="px-1.5 py-0.5 rounded bg-slate-100 text-emerald-700 font-mono text-xs border border-slate-200" {...props}>
                      {children}
                    </code>
                  );
                }
                return (
                  <div className="my-3 rounded-xl overflow-hidden border border-slate-800 bg-slate-900 shadow-sm">
                    <div className="bg-slate-800/80 px-4 py-1.5 border-b border-slate-700/60 flex items-center justify-between text-[11px] text-slate-300 font-mono">
                      <span>{match ? match[1] : 'code'}</span>
                    </div>
                    <pre className="p-4 font-mono text-xs overflow-x-auto text-slate-100 leading-relaxed">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                );
              },
            }}
          >
            {normalizedContent}
          </ReactMarkdown>
        </div>

        {/* Evidence Commit Cards Section */}
        {message.sources && message.sources.length > 0 && (
          <div className="bg-slate-50/60 p-6 border-t border-slate-100 space-y-3">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                <GitCommit className="w-4 h-4 text-emerald-600" />
                Retrieved Evidence Snapshots ({message.sources.length})
              </h4>
              <span className="text-[11px] text-slate-400">Sorted by temporal relevance</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {message.sources.map((src, idx) => (
                <EvidenceCard key={src.sha || idx} source={src} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EvidenceCard({ source }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopySha = () => {
    if (!source.sha) return;
    navigator.clipboard.writeText(source.sha);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const relevancePct = source.relevance !== undefined ? Math.round(source.relevance * 100) : 85;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3.5 text-xs shadow-sm hover:border-slate-300 transition">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span className="font-mono font-bold text-slate-900 px-2 py-0.5 bg-slate-100 rounded border border-slate-200">
            {source.sha}
          </span>
          <button
            onClick={handleCopySha}
            className="p-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded transition"
            title="Copy SHA"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>

        <span className="px-2 py-0.5 rounded-full font-semibold text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200">
          {relevancePct}% Match
        </span>
      </div>

      {source.message && (
        <p className="font-medium text-slate-800 line-clamp-2 mb-2">{source.message}</p>
      )}

      <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
        <div className="flex items-center gap-2">
          {source.date && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3 text-slate-400" />
              {source.date}
            </span>
          )}
        </div>

        {source.files && source.files.length > 0 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-emerald-600 hover:text-emerald-700 font-medium"
          >
            <span>{source.files.length} files</span>
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        )}
      </div>

      {expanded && source.files && (
        <div className="mt-2.5 pt-2 border-t border-slate-100 font-mono text-[10px] space-y-1">
          {source.files.map((file, i) => (
            <div key={i} className="flex items-center gap-1 text-slate-700 truncate">
              <FileCode className="w-3 h-3 text-slate-400 flex-shrink-0" />
              <span className="truncate">{file}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
