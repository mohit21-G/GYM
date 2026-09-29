import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../config/api';
import { MessageBubble, ChatMessageItem } from '../components/chat/MessageBubble';
import { TypingIndicator } from '../components/chat/TypingIndicator';
import {
  Send,
  Sparkles,
  RefreshCw,
  PlusCircle,
  MessageSquare,
  AlertCircle,
  Flame,
  Utensils,
  Droplets,
  Scale,
} from 'lucide-react';

export const ChatPage: React.FC = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const fetchSessions = async () => {
    try {
      setInitialLoading(true);
      const res = await apiClient.get('/chat/sessions');
      const list = Array.isArray(res.data) ? res.data : (res.data?.items || res.data?.data || []);
      setSessions(list);
      if (list.length > 0) {
        loadSession(list[0].id);
      } else {
        setInitialLoading(false);
      }
    } catch (err: any) {
      setError('Failed to load chat history. Please try again.');
      setInitialLoading(false);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      setCurrentSessionId(sessionId);
      const res = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
      const rawMessages = Array.isArray(res.data) ? res.data : (res.data?.items || res.data?.data || []);
      const parsed = rawMessages.map((m: any) => {

        let cardData = null;
        if (m.rawEntities) {
          try {
            cardData = JSON.parse(m.rawEntities);
          } catch {}
        }
        const isFoodCards = cardData?.groupedFoodCards || cardData?.ui?.groupedFoodCards;
        return {
          id: m.id,
          sender: m.sender,
          message: m.message,
          createdAt: m.createdAt,
          cardType: isFoodCards
            ? 'FOOD_LOG_CARDS'
            : m.detectedIntent?.includes('SUMMARY')
            ? 'SUMMARY'
            : m.detectedIntent?.startsWith('CREATE_')
            ? 'LOG_RESULT'
            : undefined,
          cardData: isFoodCards
            ? {
                groupedFoodCards: cardData.groupedFoodCards || cardData.ui?.groupedFoodCards,
                dailyNutritionSummary: cardData.dailyNutritionSummary || cardData.ui?.dailyNutritionSummary,
                cards: cardData.cards,
              }
            : cardData,
        };
      });
      setMessages(parsed);
    } catch (err) {
      console.error(err);
    } finally {
      setInitialLoading(false);
    }
  };

  const createNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    setError(null);
    setInputValue('');

    // Optimistically append user message
    const userMsg: ChatMessageItem = {
      sender: 'USER',
      message: text,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await apiClient.post('/chat/message', {
        sessionId: currentSessionId || undefined,
        message: text,
      });

      const resPayload = res.data?.data || res.data || {};
      const newSessionId = resPayload.sessionId || res.data?.sessionId;
      if (newSessionId && !currentSessionId) {
        setCurrentSessionId(newSessionId);
        setSessions((prev) => [
          { id: newSessionId, title: text.slice(0, 30) },
          ...prev,
        ]);
      }

      const botMsg: ChatMessageItem = {
        sender: 'ASSISTANT',
        message: resPayload.message || resPayload.replyText || resPayload.replyMessage || res.data?.message || '',
        createdAt: new Date().toISOString(),
        cardType: resPayload.ui?.type || res.data?.cardType,
        cardData: resPayload.ui?.groupedFoodCards
          ? {
              groupedFoodCards: resPayload.ui.groupedFoodCards,
              dailyNutritionSummary: resPayload.ui.dailyNutritionSummary,
              cards: resPayload.ui?.cards,
            }
          : resPayload.ui?.data || resPayload.ui?.cards || resPayload.data || res.data?.cardData,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const msg =
        err.response?.data?.message ||
        'Unable to process your request. Please check your connection and try again.';
      setError(Array.isArray(msg) ? msg.join(', ') : msg);
    } finally {
      setLoading(false);
    }
  };

  const starterSuggestions = [
    {
      label: 'Gujarati Meal',
      text: 'Savare 2 roti ane daal khadhi',
      icon: Utensils,
    },
    {
      label: 'Hindi Workout',
      text: 'Aaj maine 45 minute cardio kiya',
      icon: Flame,
    },
    {
      label: 'Hydration',
      text: 'Drank 500ml water just now',
      icon: Droplets,
    },
    {
      label: 'Weight Log',
      text: 'My weight is 72.5 kg today',
      icon: Scale,
    },
    {
      label: 'Daily Summary',
      text: 'What are my total calories today?',
      icon: Sparkles,
    },
  ];

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden bg-slate-950">
      {/* Sidebar for session history */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 hidden md:flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-slate-800">
          <button
            onClick={createNewChat}
            className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 font-medium text-sm transition-all cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-3 py-2">
            Conversations
          </div>
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => loadSession(s.id)}
              className={`w-full text-left px-3 py-2.5 rounded-xl text-xs flex items-center space-x-2.5 transition-all truncate cursor-pointer ${
                currentSessionId === s.id
                  ? 'bg-slate-800 text-emerald-400 font-medium border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{s.title || 'Conversation'}</span>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="text-xs text-slate-500 px-3 py-2">No past conversations</p>
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full bg-slate-900/40 relative">
        {/* Messages scroll container */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {error && (
            <div className="max-w-xl mx-auto p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center space-x-3 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <div className="flex-1">{error}</div>
              <button
                onClick={() => setError(null)}
                className="hover:underline text-rose-200 font-semibold"
              >
                Dismiss
              </button>
            </div>
          )}

          {initialLoading ? (
            <div className="h-full flex items-center justify-center">
              <div className="flex items-center space-x-2 text-slate-400 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                <span>Loading assistant...</span>
              </div>
            </div>
          ) : messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex flex-col items-center justify-center text-center px-4 max-w-xl mx-auto">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/25 mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">
                How can I help you today?
              </h3>
              <p className="text-sm text-slate-400 mb-8 max-w-md">
                Log your meals, workouts, water, weight, or sleep using natural
                language in English, Hindi, Gujarati, or Hinglish.
              </p>

              <div className="w-full space-y-2">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-left mb-2">
                  Try asking:
                </div>
                {starterSuggestions.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(item.text)}
                      className="w-full p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 hover:border-emerald-500/40 text-left text-xs flex items-center justify-between text-slate-300 hover:text-white transition-all group cursor-pointer shadow-sm"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center group-hover:scale-105 transition-transform">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="font-semibold text-slate-200">
                            {item.label}:{' '}
                          </span>
                          <span className="text-slate-400 group-hover:text-slate-300">
                            "{item.text}"
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <>
              {messages.map((m, idx) => (
                <MessageBubble
                  key={m.id || idx}
                  msg={m}
                  onSelectOption={(text) => handleSendMessage(text)}
                />
              ))}
              {loading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Chat input box */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 backdrop-blur-md">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="max-w-4xl mx-auto flex items-center space-x-3"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Log food, workouts, sleep, or water in English, Hindi, or Gujarati..."
              disabled={loading}
              className="flex-1 bg-slate-800 border border-slate-700/80 rounded-2xl px-5 py-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !inputValue.trim()}
              className="p-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-2xl shadow-lg shadow-emerald-500/25 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer flex-shrink-0"
              title="Send message"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
