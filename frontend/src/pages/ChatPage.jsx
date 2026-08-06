import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, AlertCircle, Database, Layers, Cpu, CheckCircle2 } from 'lucide-react';
import { chatApi } from '../services/api';
import { useRepo } from '../store/repoStore';
import ChatMessage from '../components/chat/ChatMessage';

export default function ChatPage() {
  const { activeRepo, chatState, setChatState } = useRepo();
  const { messages, input, mode } = chatState;

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Initializing search...');
  const bottomRef = useRef(null);
  const abortControllerRef = useRef(null);
  const tokenBufferRef = useRef('');
  const bufferTimerRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, statusMessage]);

  useEffect(() => {
    return () => {
      // Abort in-flight requests on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (bufferTimerRef.current) {
        clearInterval(bufferTimerRef.current);
      }
    };
  }, []);

  const updateInput = (val) => {
    setChatState((prev) => ({ ...prev, input: val }));
  };

  const updateMode = (newMode) => {
    if (loading && abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
    }
    setChatState((prev) => ({ ...prev, mode: newMode }));
  };

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || !activeRepo) return;

    // Abort previous in-flight request if present
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const queryText = input.trim();
    const userMsg = { role: 'user', content: queryText };

    // Optimistic Assistant Message placeholder
    const streamingAssistantIdx = messages.length + 1;
    const initialAssistantMsg = {
      role: 'assistant',
      content: '',
      sources: [],
      mode,
      query: queryText,
      intent: 'IMPLEMENTATION',
      evidence_match_score: null,
      answer_confidence: null,
      isStreaming: true,

    };

    // Optimistic UI Update: append user message + assistant placeholder immediately
    setChatState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMsg, initialAssistantMsg],
      input: '',
    }));

    setLoading(true);
    setStatusMessage('Connecting to temporal RAG pipeline...');
    tokenBufferRef.current = '';

    // Setup 25ms token buffer interval to minimize React re-renders during 60 FPS streaming
    bufferTimerRef.current = setInterval(() => {
      if (tokenBufferRef.current) {
        const chunkToFlush = tokenBufferRef.current;
        tokenBufferRef.current = '';

        setChatState((prev) => {
          const newMsgs = [...prev.messages];
          const lastIdx = newMsgs.length - 1;
          if (lastIdx >= 0 && newMsgs[lastIdx].role === 'assistant') {
            newMsgs[lastIdx] = {
              ...newMsgs[lastIdx],
              content: (newMsgs[lastIdx].content || '') + chunkToFlush,
            };
          }
          return { ...prev, messages: newMsgs };
        });
      }
    }, 25);

    try {
      await chatApi.queryStream(
        {
          query: queryText,
          repo_id: activeRepo.repo_id,
          mode,
        },
        {
          signal: controller.signal,
          onStatus: (msg) => {
            setStatusMessage(msg);
          },
          onMetadata: (meta) => {
            setChatState((prev) => {
              const newMsgs = [...prev.messages];
              const lastIdx = newMsgs.length - 1;
              if (lastIdx >= 0 && newMsgs[lastIdx].role === 'assistant') {
                newMsgs[lastIdx] = {
                  ...newMsgs[lastIdx],
                  sources: meta.sources || [],
                  intent: meta.intent || 'IMPLEMENTATION',
                  evidence_match_score: meta.evidence_match_score || 85,
                  answer_confidence: meta.answer_confidence || 82,
                };
              }
              return { ...prev, messages: newMsgs };
            });
          },
          onToken: (token) => {
            tokenBufferRef.current += token;
          },
          onDone: () => {
            // Flush remaining buffer
            if (tokenBufferRef.current) {
              const remaining = tokenBufferRef.current;
              tokenBufferRef.current = '';
              setChatState((prev) => {
                const newMsgs = [...prev.messages];
                const lastIdx = newMsgs.length - 1;
                if (lastIdx >= 0 && newMsgs[lastIdx].role === 'assistant') {
                  newMsgs[lastIdx] = {
                    ...newMsgs[lastIdx],
                    content: (newMsgs[lastIdx].content || '') + remaining,
                    isStreaming: false,
                  };
                }
                return { ...prev, messages: newMsgs };
              });
            }
          },
        }
      );
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Stream request aborted by user');
        return;
      }
      console.error('Streaming Chat API Error:', err);
      const errMsg = err.message || 'Query failed. Ensure local Ollama model is running.';
      setChatState((prev) => ({
        ...prev,
        messages: [...prev.messages, { role: 'error', content: errMsg }],
      }));
    } finally {
      if (bufferTimerRef.current) {
        clearInterval(bufferTimerRef.current);
      }
      setLoading(false);
    }
  };

  const handleRegenerate = (queryText) => {
    if (!queryText) return;
    updateInput(queryText);
    setTimeout(() => {
      handleSend();
    }, 50);
  };

  const handleSampleQuery = (sampleText) => {
    updateInput(sampleText);
  };

  if (!activeRepo) {
    return (
      <div className="p-8 max-w-4xl">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 flex items-start gap-4 shadow-sm">
          <div className="p-2 bg-amber-100 rounded-lg text-amber-700">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-bold text-amber-900">No Repository Selected</h2>
            <p className="text-sm text-amber-800 mt-1">
              Please go to the <strong>Repository</strong> tab and ingest a public GitHub repository to start asking architectural and causal questions.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Top Bar Header */}
      <div className="border-b border-slate-200 bg-white px-8 py-4 flex items-center justify-between shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-slate-900">{activeRepo.repo_name}</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
              Active Context
            </span>
          </div>
          <p className="text-xs text-slate-500">Ask natural language questions about codebase history, design decisions, and evolution</p>
        </div>

        {/* Mode Toggle Pills */}
        <div className="flex bg-slate-100 rounded-xl p-1 border border-slate-200">
          <button
            onClick={() => updateMode('chat')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition ${
              mode === 'chat'
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Repo Chat
          </button>
          <button
            onClick={() => updateMode('causal')}
            className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition ${
              mode === 'causal'
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Causal Reasoning ("Why")
          </button>
        </div>
      </div>

      {/* Main Message Thread */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center shadow-sm my-12 space-y-4">
              <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
                <Sparkles className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">Start Conversational Exploration</h2>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                  {mode === 'causal'
                    ? 'Ask causal questions about developer design decisions, refactoring rationale, or architecture modifications.'
                    : 'Ask any question about codebase structure, function usage, or historical commit changes.'}
                </p>
              </div>

              {/* Sample Queries */}
              <div className="pt-4 border-t border-slate-100">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Try Sample Questions:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {mode === 'causal' ? (
                    <>
                      <button onClick={() => handleSampleQuery("Why was the routing system refactored?")} className="text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-700 border border-slate-200 px-3 py-1.5 rounded-lg transition">
                        "Why was the routing system refactored?"
                      </button>
                      <button onClick={() => handleSampleQuery("Why were authentication handlers updated?")} className="text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-700 border border-slate-200 px-3 py-1.5 rounded-lg transition">
                        "Why were authentication handlers updated?"
                      </button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => handleSampleQuery("How does authentication and token validation work?")} className="text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-700 border border-slate-200 px-3 py-1.5 rounded-lg transition">
                        "How does authentication and token validation work?"
                      </button>
                      <button onClick={() => handleSampleQuery("What are the main entry point files in this project?")} className="text-xs bg-slate-50 hover:bg-emerald-50 hover:text-emerald-700 border border-slate-200 px-3 py-1.5 rounded-lg transition">
                        "What are the main entry point files in this project?"
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Render Thread Messages */}
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} onRegenerate={handleRegenerate} />
          ))}

          {/* Real-time SSE Retrieval Status Indicator */}
          {loading && (
            <div className="flex justify-start mb-6">
              <div className="max-w-xl w-full bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex items-center gap-3">
                <Loader2 className="w-4 h-4 text-emerald-600 animate-spin flex-shrink-0" />
                <span className="text-xs font-semibold text-slate-700">{statusMessage}</span>
              </div>
            </div>
          )}

          <div ref={bottomRef}></div>
        </div>
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} className="border-t border-slate-200 bg-white px-8 py-4 shadow-lg">
        <div className="max-w-5xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => updateInput(e.target.value)}
            placeholder={
              mode === 'causal'
                ? 'Ask a "Why" question (e.g. Why was X changed or introduced?)...'
                : 'Ask anything about codebase structure, function usage, or commit history...'
            }
            className="flex-1 px-4 py-3 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent font-sans"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white px-6 py-3 rounded-xl transition flex items-center gap-2 font-medium text-sm shadow-sm"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  );
}

