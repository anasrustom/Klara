'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';
import type { ChatCitation, ChatResponse } from '@/types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: ChatCitation[];
  error?: boolean;
}

interface AIChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  chatId: string; // Unique identifier for this chat context (e.g., "dashboard", "contracts", "contract-123")
  contractId?: string; // When set, answers come from this contract only; otherwise from all the user's contracts
}

const STORAGE_PREFIX = 'klara_chat_v2_';

function loadMessages(chatId: string): Message[] {
  try {
    const saved = localStorage.getItem(STORAGE_PREFIX + chatId);
    const parsed = saved ? JSON.parse(saved) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveMessages(chatId: string, messages: Message[]) {
  try {
    localStorage.setItem(STORAGE_PREFIX + chatId, JSON.stringify(messages.filter(m => !m.error)));
  } catch {
    // Storage can be unavailable (private mode); the chat still works for this visit
  }
}

function CitationChips({ citations, showContract }: { citations: ChatCitation[]; showContract: boolean }) {
  const { t } = useLanguage();
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  if (citations.length === 0) return null;

  const label = (c: ChatCitation, i: number) => {
    const page = c.page ? `${t('chat.page')} ${c.page}` : `${t('chat.source')} ${i + 1}`;
    return showContract && c.contract_title ? `${c.contract_title} · ${page}` : page;
  };

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400 mb-2">{t('chat.sources')}</p>
      <div className="flex flex-wrap gap-1.5">
        {citations.map((c, i) => (
          <button
            key={`${c.contract_id ?? ''}-${c.chunk_id}-${i}`}
            type="button"
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
            title={c.snippet}
            aria-expanded={openIndex === i}
            className={`inline-flex items-center gap-1 max-w-full px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              openIndex === i
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-primary-50 text-primary-700 border-primary-100 hover:bg-primary-100'
            }`}
          >
            <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="truncate">{label(c, i)}</span>
          </button>
        ))}
      </div>
      {openIndex !== null && citations[openIndex] && (
        <div className="mt-2 rounded-lg bg-gray-50 border-s-4 border-primary-400 px-3 py-2 animate-fade-in">
          <p dir="auto" className="text-xs leading-relaxed text-gray-700 italic">
            &ldquo;{citations[openIndex].snippet}&rdquo;
          </p>
          {showContract && citations[openIndex].contract_id && (
            <Link
              href={`/contracts/${citations[openIndex].contract_id}`}
              className="inline-block mt-1.5 text-xs font-medium text-primary-600 hover:text-primary-700"
            >
              {t('chat.openContract')}
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

export default function AIChatSidebar({ isOpen, onClose, chatId, contractId }: AIChatSidebarProps) {
  const { t, language } = useLanguage();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isPortfolio = !contractId;
  const suggestions = isPortfolio
    ? [t('chat.suggest.portfolio.1'), t('chat.suggest.portfolio.2')]
    : [t('chat.suggest.contract.1'), t('chat.suggest.contract.2'), t('chat.suggest.contract.3')];

  // Load this chat's history when the context changes
  useEffect(() => {
    setMessages(loadMessages(chatId));
  }, [chatId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const updateMessages = (next: Message[]) => {
    setMessages(next);
    saveMessages(chatId, next);
  };

  const ask = async (question: string, history: Message[]) => {
    const userMessage: Message = { role: 'user', content: question, timestamp: new Date().toISOString() };
    const withQuestion = [...history, userMessage];
    updateMessages(withQuestion);
    setIsTyping(true);

    const fail = (content: string) =>
      updateMessages([...withQuestion, { role: 'assistant', content, timestamp: new Date().toISOString(), error: true }]);

    try {
      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({ message: question });
      if (contractId) params.set('contract_id', contractId);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat?${params.toString()}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.status === 401) return fail(t('chat.sessionExpired'));
      if (response.status === 404) return fail(t('chat.notFound'));
      if (!response.ok) return fail(t('chat.error'));

      const data: ChatResponse = await response.json();
      updateMessages([
        ...withQuestion,
        {
          role: 'assistant',
          content: data.response,
          citations: data.citations ?? [],
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch {
      fail(t('chat.error'));
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = (text?: string) => {
    const question = (text ?? inputMessage).trim();
    if (!question || isTyping) return;
    setInputMessage('');
    ask(question, messages.filter(m => !m.error));
  };

  const handleRetry = () => {
    const clean = messages.filter(m => !m.error);
    const last = clean[clean.length - 1];
    if (!last || last.role !== 'user' || isTyping) return;
    ask(last.content, clean.slice(0, -1));
  };

  const handleClear = () => {
    updateMessages([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString(language === 'ar' ? 'ar' : 'en', { hour: '2-digit', minute: '2-digit' });

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* Sidebar: slides in from the reading-end side (right in English, left in Arabic) */}
      <aside
        aria-hidden={!isOpen}
        aria-label={t('chat.title')}
        className={`fixed top-0 h-full w-full md:w-[450px] bg-white shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ease-in-out ltr:right-0 rtl:left-0 ${
          isOpen ? 'translate-x-0' : 'ltr:translate-x-full rtl:-translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white p-6 shadow-lg shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold">{t('chat.title')}</h2>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={handleClear}
                  disabled={isTyping}
                  title={t('chat.clear')}
                  aria-label={t('chat.clear')}
                  className="text-white/90 hover:text-white hover:bg-white/10 rounded-full p-2 transition-all disabled:opacity-50"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
              <button
                onClick={onClose}
                title={t('chat.close')}
                aria-label={t('chat.close')}
                className="text-white/90 hover:text-white hover:bg-white/10 rounded-full p-2 transition-all"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <p className="text-sm text-white/80">
            {isPortfolio ? t('chat.subtitle.portfolio') : t('chat.subtitle.contract')}
          </p>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-gray-50 to-white">
          {/* Welcome and suggested questions */}
          <div className="flex justify-start animate-fade-in">
            <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-white text-gray-800 shadow-md border border-gray-100">
              <p className="text-sm leading-relaxed">
                {isPortfolio ? t('chat.welcome.portfolio') : t('chat.welcome.contract')}
              </p>
            </div>
          </div>
          {messages.length === 0 && (
            <div className="flex flex-col items-start gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSendMessage(s)}
                  disabled={isTyping}
                  className="text-start text-sm px-3 py-2 rounded-xl border border-primary-200 bg-white text-primary-700 hover:bg-primary-50 transition-colors disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg'
                    : message.error
                      ? 'bg-red-50 text-red-800 border border-red-200'
                      : 'bg-white text-gray-800 shadow-md border border-gray-100'
                }`}
              >
                <p dir="auto" className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>
                {message.citations && (
                  <CitationChips citations={message.citations} showContract={isPortfolio} />
                )}
                {message.error && index === messages.length - 1 && (
                  <button
                    onClick={handleRetry}
                    disabled={isTyping}
                    className="mt-2 text-xs font-semibold text-red-700 underline hover:text-red-900 disabled:opacity-50"
                  >
                    {t('chat.retry')}
                  </button>
                )}
                <p className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-white/70' : message.error ? 'text-red-400' : 'text-gray-400'
                }`}>
                  {formatTime(message.timestamp)}
                </p>
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start animate-fade-in" role="status">
              <div className="bg-white text-gray-800 shadow-md border border-gray-100 rounded-2xl px-4 py-3 max-w-[85%]">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                    <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                  <span className="text-xs text-gray-500">{t('chat.thinking')}</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="shrink-0 bg-white border-t border-gray-200 p-4 shadow-lg">
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('chat.placeholder')}
                dir="auto"
                maxLength={2000}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
                rows={1}
                disabled={isTyping}
              />
            </div>
            <button
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isTyping}
              aria-label={t('chat.send')}
              className="px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
            >
              <svg className="w-5 h-5 rtl:-scale-x-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              <span className="hidden sm:inline">{t('chat.send')}</span>
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            {t('chat.hint')}
          </p>
        </div>
      </aside>
    </>
  );
}
