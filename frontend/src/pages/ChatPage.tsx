import React, { useState, useEffect, useRef } from 'react';
import { apiClient } from '../config/api';
import { MessageBubble, ChatMessageItem } from '../components/chat/MessageBubble';
import { TypingIndicator } from '../components/chat/TypingIndicator';
import { EditFoodLogModal } from '../components/food/EditFoodLogModal';
import { FoodLogEntryData } from '../components/food/FoodLogEntry';
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
  const [editingEntry, setEditingEntry] = useState<FoodLogEntryData | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 136; // Approx 4-5 lines of text with 22px line height + padding
      if (scrollHeight > maxHeight) {
        textareaRef.current.style.height = `${maxHeight}px`;
        textareaRef.current.style.overflowY = 'auto';
      } else {
        textareaRef.current.style.height = `${Math.max(48, scrollHeight)}px`;
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
  }, [inputValue]);

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
          if (typeof m.rawEntities === 'string') {
            try {
              cardData = JSON.parse(m.rawEntities);
            } catch {}
          } else if (typeof m.rawEntities === 'object') {
            cardData = m.rawEntities;
          }
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

  const handleSaveEditedLog = async (updatedData: {
    foodName: string;
    quantity: number;
    unit: string;
    mealType: string;
    loggedAt?: string;
  }) => {
    if (!editingEntry) return;

    const res = await apiClient.patch(`/food-logs/${editingEntry.id}`, {
      foodName: updatedData.foodName,
      quantity: updatedData.quantity,
      unit: updatedData.unit,
      mealType: updatedData.mealType,
      loggedAt: updatedData.loggedAt,
    });

    const respData = res.data;
    const updatedDoc = respData.entry || respData;
    const updatedDailySummary = respData.dailyNutritionSummary;

    // Update React state immediately across messages
    setMessages((prevMessages) => {
      return prevMessages.map((msg) => {
        if (!msg.cardData?.groupedFoodCards) return msg;

        const updatedCards = msg.cardData.groupedFoodCards.map((card: any) => {
          const entryExists = card.entries?.some((e: any) => e.id === editingEntry.id);
          if (!entryExists) return card;

          const updatedEntries = card.entries.map((e: any) => {
            if (e.id === editingEntry.id) {
              return {
                ...e,
                foodName: updatedDoc.foodName || updatedDoc.food_name || updatedData.foodName,
                quantity: updatedDoc.quantity ?? updatedDoc.quantity_amount ?? updatedData.quantity,
                unit: updatedDoc.unit || updatedDoc.quantity_unit || updatedData.unit,
                calories: updatedDoc.calories,
                mealType: updatedDoc.mealType || updatedDoc.meal_type || updatedData.mealType,
                timeFormatted: updatedDoc.timeFormatted ?? e.timeFormatted,
                macros: updatedDoc.macros || {
                  proteinG: updatedDoc.protein_g ?? updatedDoc.proteinG ?? 0,
                  carbsG: updatedDoc.carbs_g ?? updatedDoc.carbsG ?? 0,
                  fatG: updatedDoc.fat_g ?? updatedDoc.fatG ?? 0,
                  fiberG: updatedDoc.fiber_g ?? updatedDoc.fiberG ?? 0,
                },
              };
            }
            return e;
          });

          // Recalculate card totals
          const totalQty = updatedEntries.reduce((acc: number, curr: any) => acc + (Number(curr.quantity) || 0), 0);
          const totalCal = updatedEntries.reduce((acc: number, curr: any) => acc + (Number(curr.calories) || 0), 0);
          const totalP = updatedEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.proteinG) || 0), 0);
          const totalC = updatedEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.carbsG) || 0), 0);
          const totalF = updatedEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.fatG) || 0), 0);
          const totalFib = updatedEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.fiberG) || 0), 0);

          const newFoodName = updatedDoc.foodName || updatedDoc.food_name || updatedData.foodName || card.foodName;

          return {
            ...card,
            foodName: newFoodName,
            foodKey: `food_${(updatedDoc.foodMasterId || updatedDoc.food_id || newFoodName).toLowerCase()}`,
            totalQuantity: Number.isInteger(totalQty) ? totalQty : Math.round(totalQty * 10) / 10,
            totalCalories: Math.round(totalCal),
            unit: updatedDoc.unit || updatedDoc.quantity_unit || card.unit,
            entries: updatedEntries,
            macros: {
              proteinG: Math.round(totalP * 10) / 10,
              carbsG: Math.round(totalC * 10) / 10,
              fatG: Math.round(totalF * 10) / 10,
              fiberG: Math.round(totalFib * 10) / 10,
            },
          };
        });

        let updatedMsgText = msg.message;
        if (updatedDailySummary && updatedMsgText.includes("Today's total:")) {
          updatedMsgText = updatedMsgText.replace(
            /Today's total:\s*\d+\s*\/\s*\d+\s*kcal/,
            `Today's total: ${Math.round(updatedDailySummary.totalCalories)} / ${Math.round(updatedDailySummary.targetCalories)} kcal`
          );
        }

        return {
          ...msg,
          message: updatedMsgText,
          cardData: {
            ...msg.cardData,
            groupedFoodCards: updatedCards,
            dailyNutritionSummary: updatedDailySummary || msg.cardData.dailyNutritionSummary,
          },
        };
      });
    });

    setEditingEntry(null);
  };

  const handleDeleteFoodLog = async (entry: FoodLogEntryData) => {
    if (!window.confirm(`Are you sure you want to delete ${entry.foodName}?`)) {
      return;
    }

    try {
      const res = await apiClient.delete(`/food-logs/${entry.id}`);
      const respData = res.data;
      const updatedDailySummary = respData?.dailyNutritionSummary;

      // Update React state immediately across messages
      setMessages((prevMessages) => {
        return prevMessages.map((msg) => {
          if (!msg.cardData?.groupedFoodCards) return msg;

          const updatedCards = msg.cardData.groupedFoodCards
            .map((card: any) => {
              const remainingEntries = card.entries.filter((e: any) => e.id !== entry.id);
              if (remainingEntries.length === 0) return null;

              const totalQty = remainingEntries.reduce((acc: number, curr: any) => acc + (Number(curr.quantity) || 0), 0);
              const totalCal = remainingEntries.reduce((acc: number, curr: any) => acc + (Number(curr.calories) || 0), 0);
              const totalP = remainingEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.proteinG) || 0), 0);
              const totalC = remainingEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.carbsG) || 0), 0);
              const totalF = remainingEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.fatG) || 0), 0);
              const totalFib = remainingEntries.reduce((acc: number, curr: any) => acc + (Number(curr.macros?.fiberG) || 0), 0);

              return {
                ...card,
                entryCount: remainingEntries.length,
                totalQuantity: Number.isInteger(totalQty) ? totalQty : Math.round(totalQty * 10) / 10,
                totalCalories: Math.round(totalCal),
                entries: remainingEntries,
                macros: {
                  proteinG: Math.round(totalP * 10) / 10,
                  carbsG: Math.round(totalC * 10) / 10,
                  fatG: Math.round(totalF * 10) / 10,
                  fiberG: Math.round(totalFib * 10) / 10,
                },
              };
            })
            .filter(Boolean);

          let updatedMsgText = msg.message;
          if (updatedDailySummary && updatedMsgText.includes("Today's total:")) {
            updatedMsgText = updatedMsgText.replace(
              /Today's total:\s*\d+\s*\/\s*\d+\s*kcal/,
              `Today's total: ${Math.round(updatedDailySummary.totalCalories)} / ${Math.round(updatedDailySummary.targetCalories)} kcal`
            );
          }

          return {
            ...msg,
            message: updatedMsgText,
            cardData: {
              ...msg.cardData,
              groupedFoodCards: updatedCards,
              dailyNutritionSummary: updatedDailySummary || msg.cardData.dailyNutritionSummary,
            },
          };
        });
      });
    } catch (err: any) {
      console.error('Error deleting food log:', err);
      alert(err.response?.data?.detail || 'Failed to delete food log. Please try again.');
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    setError(null);
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '48px';
    }

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

      const rawData = res.data || {};
      const dataObj = rawData.data || {};
      const uiObj = rawData.ui || dataObj.ui || {};

      const newSessionId = rawData.sessionId || dataObj.sessionId;
      if (newSessionId && !currentSessionId) {
        setCurrentSessionId(newSessionId);
        setSessions((prev) => [
          { id: newSessionId, title: text.slice(0, 30) },
          ...prev,
        ]);
      }

      const foodCards =
        uiObj.groupedFoodCards ||
        dataObj.currentGroupedFoodCards ||
        dataObj.groupedFoodCards ||
        null;

      const dailySummary =
        uiObj.dailyNutritionSummary ||
        dataObj.dailyNutritionSummary ||
        null;

      const cards = uiObj.cards || dataObj.cards || null;

      const cardType =
        uiObj.type ||
        (foodCards && foodCards.length > 0 ? 'FOOD_LOG_CARDS' : rawData.cardType);

      const cardData =
        foodCards && foodCards.length > 0
          ? {
              groupedFoodCards: foodCards,
              dailyNutritionSummary: dailySummary,
              cards,
            }
          : uiObj.data || cards || dataObj;

      const botMsg: ChatMessageItem = {
        id: rawData.messageId || rawData.id || `bot-${Date.now()}`,
        sender: 'ASSISTANT',
        message:
          rawData.message ||
          rawData.replyText ||
          dataObj.replyText ||
          dataObj.message ||
          '',
        createdAt: new Date().toISOString(),
        cardType,
        cardData,
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
                  onEditFoodLog={(entry) => setEditingEntry(entry)}
                  onDeleteFoodLog={handleDeleteFoodLog}
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
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.nativeEvent.isComposing) return;
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              rows={1}
              placeholder="Log food, workouts, sleep, or water in English, Hindi, or Gujarati..."
              disabled={loading}
              className="flex-1 bg-slate-800 border border-slate-700/80 rounded-2xl px-5 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all disabled:opacity-50 resize-none max-h-36 min-h-[48px] leading-relaxed"
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

      {/* Edit Food Log Modal */}
      <EditFoodLogModal
        isOpen={Boolean(editingEntry)}
        entry={editingEntry}
        onClose={() => setEditingEntry(null)}
        onSave={handleSaveEditedLog}
      />
    </div>
  );
};
