import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, GitCommit, AlertCircle } from 'lucide-react';
import { chatApi } from '../services/api';
import { useRepo } from '../store/repoStore';

export default function ChatPage() {
  const { activeRepo } = useRepo();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('causal');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !activeRepo) return;

    const userMsg = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await chatApi.query({
        query: input,
        repo_id: activeRepo.repo_id,
        mode,
      });
      const data = res.data.data;

      const assistantMsg = {
        role: 'assistant',
        content: mode === 'causal' ? data.explanation : data.answer,
        sources: mode === 'causal' ? data.evidence_commits : data.sources,
        mode,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'error', content: err.response?.data?.detail || 'Query failed. Check that Ollama is running.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!activeRepo) {
    return (
      <div className="p-8">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 max-w-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium text-amber-900">No repository selected</p>
            <p className="text-sm text-amber-700 mt-1">
              Go to the Repository tab and ingest a repository before starting a chat session.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="border-b border-slate-200 bg-white px-8 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">{activeRepo.repo_name}</h1>
          <p className="text-xs text-slate-500">Ask questions about this repository's history and evolution</p>
        </div>
        <div className="flex bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => setMode('chat')}
            className={mode === 'chat' ? 'px-3 py-1.5 text-xs font-medium rounded-md transition bg-white text-slate-900 shadow-sm' : 'px-3 py-1.5 text-xs font-medium rounded-md transition text-slate-500'}
          >
            Repo Chat
          </button>
          <button
            onClick={() => setMode('causal')}
            className={mode === 'causal' ? 'px-3 py-1.5 text-xs font-medium rounded-md transition bg-white text-slate-900 shadow-sm' : 'px-3 py-1.5 text-xs font-medium rounded-md transition text-slate-500'}
          >
            Causal Reasoning
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-5">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20">
            <Sparkles className="w-8 h-8 mx-auto mb-3 text-slate-300" />
            <p className="text-sm">
              {mode === 'causal' ? 'Ask why questions, for example: Why was the routing system refactored?' : 'Ask anything about the codebase, for example: How does authentication work?'}
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
            <div className={
              msg.role === 'user'
                ? 'max-w-2xl rounded-xl px-4 py-3 text-sm bg-slate-900 text-white'
                : msg.role === 'error'
                ? 'max-w-2xl rounded-xl px-4 py-3 text-sm bg-red-50 text-red-700 border border-red-200'
                : 'max-w-2xl rounded-xl px-4 py-3 text-sm bg-white border border-slate-200 text-slate-800'
            }>
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Evidence</p>
                  {msg.sources.slice(0, 4).map((s, j) => (
                    <div key={j} className="flex items-center gap-2 text-xs text-slate-500">
                      <GitCommit className="w-3 h-3 flex-shrink-0" />
                      <span className="font-mono">{s.sha}</span>
                      <span>-</span>
                      <span>{s.date}</span>
                      {s.relevance !== undefined && (
                        <span>- {Math.round(s.relevance * 100)}% relevant</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 flex items-center gap-2 text-sm text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              {mode === 'causal' ? 'Analyzing commit history...' : 'Thinking...'}
            </div>
          </div>
        )}
        <div ref={bottomRef}></div>
      </div>

      <form onSubmit={handleSend} className="border-t border-slate-200 bg-white px-8 py-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={mode === 'causal' ? 'Why was X changed?' : 'Ask a question...'}
            className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-5 rounded-lg transition flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
