import React, { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../config/api';
import { MessageBubble, ChatMessageItem } from '../components/chat/MessageBubble';
import { TypingIndicator } from '../components/chat/TypingIndicator';
import { EditFoodLogModal } from '../components/food/EditFoodLogModal';
import { FoodLogEntryData } from '../components/food/FoodLogEntry';
import { EditHydrationLogModal } from '../components/hydration/EditHydrationLogModal';
import { HydrationEntryItem } from '../components/hydration/DailyHydrationSummary';
import { EditActivityLogModal, ActivityEntryData } from '../components/activity/EditActivityLogModal';
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
  Edit2,
  Trash2,
  Check,
  X,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Title auto-generation from first user message
// ---------------------------------------------------------------------------
function deriveTitleFromMessage(text: string): string {
  const lower = text.toLowerCase();
  const hasFood =
    /\b(ate|had|eat|khai|khadhi|khadha|roti|rotli|dal|rice|paneer|egg|chicken|banana|poha|upma|thepla|bhakri|chaas|doodh)\b/.test(lower);
  const hasWorkout =
    /\b(walk|run|gym|workout|kasrat|exercise|cycling|pushup|squat|jogging|hiit|cardio)\b/.test(lower);
  const hasHydration =
    /\b(water|pani|hydrat|drink|chaas|juice|smoothie)\b/.test(lower);
  const hasWeight = /\b(weight|vajan|kg|kilo)\b/.test(lower);
  const hasSleep = /\b(sleep|slept|neend|oongh)\b/.test(lower);

  if (hasFood && hasWorkout) return 'Food & Workout';
  if (hasFood && hasHydration) return 'Food & Hydration';
  if (hasFood) return 'Food Log';
  if (hasWorkout) return 'Workout';
  if (hasHydration) return 'Hydration';
  if (hasWeight) return 'Weight Log';
  if (hasSleep) return 'Sleep Log';
  return 'Fitness Chat';
}

// ---------------------------------------------------------------------------
// Today's date in "YYYY-MM-DD" using Asia/Kolkata timezone (matches backend)
// ---------------------------------------------------------------------------
function getTodayIST(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
}

// ---------------------------------------------------------------------------
// Session shape returned by GET /chat/sessions
// ---------------------------------------------------------------------------
interface SessionItem {
  id: string;
  title: string;
  logDate?: string;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// ChatPage
// ---------------------------------------------------------------------------
export const ChatPage: React.FC = () => {
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  // Track which session ids have already had their title auto-patched
  const titledSessionsRef = useRef<Set<string>>(new Set());
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [sessionSwitching, setSessionSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingEntry, setEditingEntry] = useState<FoodLogEntryData | null>(null);
  const [editingHydrationEntry, setEditingHydrationEntry] = useState<HydrationEntryItem | null>(null);
  const [editingActivityEntry, setEditingActivityEntry] = useState<ActivityEntryData | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Track the most-recently opened session so we can detect day-boundary changes
  const currentDayRef = useRef<string>(getTodayIST());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 136;
      if (scrollHeight > maxHeight) {
        textareaRef.current.style.height = `${maxHeight}px`;
        textareaRef.current.style.overflowY = 'auto';
      } else {
        textareaRef.current.style.height = `${Math.max(48, scrollHeight)}px`;
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
  }, [inputValue]);

  // ── helpers ────────────────────────────────────────────────────────────────

  /** Parse raw message docs from GET /chat/sessions/:id/messages into ChatMessageItem[]. */
  const parseMessages = (rawMessages: any[]): ChatMessageItem[] =>
    rawMessages.map((m: any) => {
      let cardData: any = null;
      if (m.rawEntities) {
        try {
          cardData = typeof m.rawEntities === 'string'
            ? JSON.parse(m.rawEntities)
            : m.rawEntities;
        } catch { /* ignore */ }
      }
      const isFoodCards = cardData?.groupedFoodCards || cardData?.ui?.groupedFoodCards;

      let resolvedCardType: string | undefined = undefined;
      let resolvedCardData: any = cardData;

      if (isFoodCards) {
        resolvedCardType = 'FOOD_LOG_CARDS';
        resolvedCardData = {
          groupedFoodCards: cardData.groupedFoodCards ?? cardData.ui?.groupedFoodCards,
          dailyNutritionSummary: cardData.dailyNutritionSummary ?? cardData.ui?.dailyNutritionSummary,
          cards: cardData.cards,
        };
      } else if (cardData?.cards && Array.isArray(cardData.cards)) {
        resolvedCardType = 'LOG_RESULT';
        resolvedCardData = cardData.cards;
      } else if (cardData?.ui?.data) {
        resolvedCardType = cardData.ui.type || 'LOG_RESULT';
        resolvedCardData = cardData.ui.data;
      } else if (cardData?.data) {
        resolvedCardType = 'LOG_RESULT';
        resolvedCardData = cardData.data;
      } else if (m.detectedIntent?.includes('SUMMARY')) {
        resolvedCardType = 'SUMMARY';
        resolvedCardData = cardData;
      } else if (m.detectedIntent?.startsWith('CREATE_')) {
        resolvedCardType = 'LOG_RESULT';
        resolvedCardData = cardData;
      }

      return {
        id: m.id,
        sender: m.sender,
        message: m.message,
        createdAt: m.createdAt,
        cardType: resolvedCardType,
        cardData: resolvedCardData,
      };
    });

  /** Load messages for a specific session and switch the active session.
   *
   * `sessionSwitching` is set for the duration of the fetch so the render
   * logic can show a spinner instead of the "New Chat" starter-suggestions
   * empty state. Without this flag, clearing `messages` to `[]` before the
   * fetch resolves makes an *existing* conversation flash the brand-new-chat
   * placeholder for ~1-2s on every session switch, which is confusing because
   * it looks like the conversation was wiped. */
  const loadSession = useCallback(async (sessionId: string) => {
    // Immediately clear messages so we never show a previous session's data
    setMessages([]);
    setCurrentSessionId(sessionId);
    setError(null);
    setSessionSwitching(true);
    try {
      const res = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
      const raw = Array.isArray(res.data)
        ? res.data
        : res.data?.items ?? res.data?.data ?? [];
      setMessages(parseMessages(raw));
    } catch (err) {
      console.error('loadSession error', err);
    } finally {
      setSessionSwitching(false);
    }
  }, []);

  /**
   * On mount: fetch the session list.
   * Then open today's session via GET /chat/today — this guarantees one
   * session per calendar day (Asia/Kolkata) and auto-creates one when needed.
   * If today already has a session, it is returned without creating a duplicate.
   */
  useEffect(() => {
    (async () => {
      try {
        setInitialLoading(true);

        // 1 + 2. Load the sidebar session list AND today's session in parallel.
        // These two calls are independent, so running them concurrently removes
        // one full network round-trip from the initial load (noticeable on a
        // cloud MongoDB where each request carries real latency).
        const [listRes, todayRes] = await Promise.all([
          apiClient.get('/chat/sessions'),
          apiClient.get('/chat/today'),
        ]);

        const list: SessionItem[] = Array.isArray(listRes.data)
          ? listRes.data
          : listRes.data?.items ?? listRes.data?.data ?? [];
        setSessions(list);

        const todaySessionId: string = todayRes.data.id;
        const todayTitle: string = todayRes.data.title;
        currentDayRef.current = getTodayIST();

        // Add to sidebar list if it wasn't already present (just created)
        if (todayRes.data.created) {
          setSessions((prev) => {
            if (prev.some((s) => s.id === todaySessionId)) return prev;
            return [
              {
                id: todaySessionId,
                title: todayTitle,
                logDate: todayRes.data.log_date,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              },
              ...prev,
            ];
          });
        }

        await loadSession(todaySessionId);
      } catch (err: any) {
        setError('Failed to load chat history. Please try again.');
      } finally {
        setInitialLoading(false);
      }
    })();
  }, [loadSession]);

  /**
   * Create a completely new, blank conversation and persist it immediately
   * via POST /chat/message with an empty sentinel, OR — better — by calling
   * a real create-session approach.
   *
   * We achieve persistence by posting a "new-session" marker message to
   * /chat/message with no sessionId, which creates a DB session, then
   * discarding the assistant reply and just opening the empty session.
   *
   * Actually the cleanest approach: we generate a UUID client-side, set it as
   * currentSessionId, and let the first real user message create the session
   * on the backend (which accepts any sessionId via get_or_create_session).
   * We store a pending entry in the sidebar immediately and replace its title
   * once the first message goes through.
   */
  const createNewChat = async () => {
    // Generate a stable ID now so the session survives a refresh once the
    // first message is sent (backend creates it via get_or_create_session).
    const newId = crypto.randomUUID();
    const pendingSession: SessionItem = {
      id: newId,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Immediately clear messages and switch to the new blank session
    setMessages([]);
    setCurrentSessionId(newId);
    setError(null);

    // Add to sidebar top so user sees it straight away
    setSessions((prev) => [pendingSession, ...prev.filter((s) => s.id !== newId)]);
  };

  // ── Session Management (Rename / Delete) ──────────────────────────────────
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editTitleValue, setEditTitleValue] = useState<string>('');

  const startRename = (session: SessionItem, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitleValue(session.title || '');
  };

  const saveRename = async (sessionId: string, e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.stopPropagation();
    const cleanTitle = editTitleValue.trim();
    if (!cleanTitle) {
      setEditingSessionId(null);
      return;
    }
    try {
      await apiClient.patch(`/chat/sessions/${sessionId}/title`, { title: cleanTitle });
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: cleanTitle, updatedAt: new Date().toISOString() } : s))
      );
      titledSessionsRef.current.add(sessionId);
    } catch (err) {
      console.error('Failed to rename session', err);
    } finally {
      setEditingSessionId(null);
    }
  };

  const cancelRename = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setEditingSessionId(null);
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
      return;
    }
    try {
      await apiClient.delete(`/chat/sessions/${sessionId}`);
      const updatedList = sessions.filter((s) => s.id !== sessionId);
      setSessions(updatedList);

      if (currentSessionId === sessionId) {
        if (updatedList.length > 0) {
          await loadSession(updatedList[0].id);
        } else {
          await createNewChat();
        }
      }
    } catch (err: any) {
      console.error('Failed to delete session', err);
      alert(err.response?.data?.detail || 'Failed to delete conversation.');
    }
  };

  // ── edit / delete food log ─────────────────────────────────────────────────

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

    setMessages((prevMessages) =>
      prevMessages.map((msg) => {
        if (!msg.cardData?.groupedFoodCards) return msg;

        const updatedCards = msg.cardData.groupedFoodCards.map((card: any) => {
          const entryExists = card.entries?.some((e: any) => e.id === editingEntry.id);
          if (!entryExists) return card;

          const updatedEntries = card.entries.map((e: any) => {
            if (e.id !== editingEntry.id) return e;
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
          });

          const totalQty  = updatedEntries.reduce((a: number, c: any) => a + (Number(c.quantity) || 0), 0);
          const totalCal  = updatedEntries.reduce((a: number, c: any) => a + (Number(c.calories) || 0), 0);
          const totalP    = updatedEntries.reduce((a: number, c: any) => a + (Number(c.macros?.proteinG) || 0), 0);
          const totalC    = updatedEntries.reduce((a: number, c: any) => a + (Number(c.macros?.carbsG) || 0), 0);
          const totalF    = updatedEntries.reduce((a: number, c: any) => a + (Number(c.macros?.fatG) || 0), 0);
          const totalFib  = updatedEntries.reduce((a: number, c: any) => a + (Number(c.macros?.fiberG) || 0), 0);
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
              carbsG:   Math.round(totalC * 10) / 10,
              fatG:     Math.round(totalF * 10) / 10,
              fiberG:   Math.round(totalFib * 10) / 10,
            },
          };
        });

        let updatedMsgText = msg.message;
        if (updatedDailySummary && updatedMsgText.includes("Today's total:")) {
          updatedMsgText = updatedMsgText.replace(
            /Today's total:\s*\d+\s*\/\s*\d+\s*kcal/,
            `Today's total: ${Math.round(updatedDailySummary.totalCalories)} / ${Math.round(updatedDailySummary.targetCalories)} kcal`,
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
      }),
    );
    setEditingEntry(null);
  };

  const handleDeleteFoodLog = async (entry: FoodLogEntryData) => {
    if (!window.confirm(`Are you sure you want to delete ${entry.foodName}?`)) return;

    try {
      const res = await apiClient.delete(`/food-logs/${entry.id}`);
      const respData = res.data;
      const updatedDailySummary = respData?.dailyNutritionSummary;

      setMessages((prevMessages) =>
        prevMessages.map((msg) => {
          if (!msg.cardData?.groupedFoodCards) return msg;

          const updatedCards = msg.cardData.groupedFoodCards
            .map((card: any) => {
              const remaining = card.entries.filter((e: any) => e.id !== entry.id);
              if (remaining.length === 0) return null;

              const totalQty = remaining.reduce((a: number, c: any) => a + (Number(c.quantity) || 0), 0);
              const totalCal = remaining.reduce((a: number, c: any) => a + (Number(c.calories) || 0), 0);
              const totalP   = remaining.reduce((a: number, c: any) => a + (Number(c.macros?.proteinG) || 0), 0);
              const totalC   = remaining.reduce((a: number, c: any) => a + (Number(c.macros?.carbsG) || 0), 0);
              const totalF   = remaining.reduce((a: number, c: any) => a + (Number(c.macros?.fatG) || 0), 0);
              const totalFib = remaining.reduce((a: number, c: any) => a + (Number(c.macros?.fiberG) || 0), 0);

              return {
                ...card,
                entryCount: remaining.length,
                totalQuantity: Number.isInteger(totalQty) ? totalQty : Math.round(totalQty * 10) / 10,
                totalCalories: Math.round(totalCal),
                entries: remaining,
                macros: {
                  proteinG: Math.round(totalP * 10) / 10,
                  carbsG:   Math.round(totalC * 10) / 10,
                  fatG:     Math.round(totalF * 10) / 10,
                  fiberG:   Math.round(totalFib * 10) / 10,
                },
              };
            })
            .filter(Boolean);

          let updatedMsgText = msg.message;
          if (updatedDailySummary && updatedMsgText.includes("Today's total:")) {
            updatedMsgText = updatedMsgText.replace(
              /Today's total:\s*\d+\s*\/\s*\d+\s*kcal/,
              `Today's total: ${Math.round(updatedDailySummary.totalCalories)} / ${Math.round(updatedDailySummary.targetCalories)} kcal`,
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
        }),
      );
    } catch (err: any) {
      console.error('Error deleting food log:', err);
      alert(err.response?.data?.detail || 'Failed to delete food log. Please try again.');
    }
  };

  // ── edit / delete hydration log ─────────────────────────────────────────────
  // Hydration entries live either directly at `cardData.entries` (single
  // CREATE_HYDRATION_LOG card) or inside `cardData.cards[i].entries` for a
  // HYDRATION-type card embedded in a multi-log response. This helper rewrites
  // every entries array in a message's cardData that contains a matching id.

  const patchHydrationEntriesInCardData = (
    cardData: any,
    entryId: string,
    updater: (entry: any) => any | null,
  ) => {
    if (!cardData) return cardData;

    const applyToList = (list: any[]) =>
      list
        .map((e: any) => (e.id === entryId ? updater(e) : e))
        .filter((e: any) => e !== null);

    let changed = false;
    let next = cardData;

    if (Array.isArray(cardData.entries) && cardData.entries.some((e: any) => e.id === entryId)) {
      changed = true;
      next = { ...next, entries: applyToList(cardData.entries) };
    }

    if (Array.isArray(cardData.cards)) {
      const newCards = cardData.cards.map((card: any) => {
        if (card?.type === 'HYDRATION' && Array.isArray(card.entries) && card.entries.some((e: any) => e.id === entryId)) {
          changed = true;
          return { ...card, entries: applyToList(card.entries) };
        }
        return card;
      });
      if (changed) next = { ...next, cards: newCards };
    }

    return changed ? next : cardData;
  };

  const handleSaveEditedHydrationLog = async (updatedData: {
    amountMl: number;
    beverageName: string;
    quantity?: number;
    loggedAt?: string;
  }) => {
    if (!editingHydrationEntry?.id) return;

    const res = await apiClient.patch(`/hydration-logs/${editingHydrationEntry.id}`, {
      amountMl: updatedData.amountMl,
      beverageName: updatedData.beverageName,
      quantity: updatedData.quantity,
      loggedAt: updatedData.loggedAt,
    });
    const updatedEntry = res.data?.entry || res.data;

    setMessages((prevMessages) =>
      prevMessages.map((msg) => {
        const newCardData = patchHydrationEntriesInCardData(
          msg.cardData,
          editingHydrationEntry.id!,
          (e) => ({
            ...e,
            amountMl: updatedEntry.amountMl ?? updatedData.amountMl,
            beverageName: updatedEntry.beverageName ?? updatedData.beverageName,
            quantity: updatedEntry.quantity ?? updatedData.quantity ?? null,
            calories: updatedEntry.calories ?? null,
            proteinG: updatedEntry.proteinG ?? null,
            carbsG: updatedEntry.carbsG ?? null,
            fatG: updatedEntry.fatG ?? null,
            fiberG: updatedEntry.fiberG ?? null,
            time: updatedEntry.timeFormatted || e.time,
          }),
        );
        if (newCardData === msg.cardData) return msg;
        return { ...msg, cardData: newCardData };
      }),
    );
  };

  const handleDeleteHydrationLog = async (entry: HydrationEntryItem) => {
    if (!entry.id) return;
    if (!window.confirm('Are you sure you want to delete this hydration entry?')) return;

    try {
      await apiClient.delete(`/hydration-logs/${entry.id}`);
      setMessages((prevMessages) =>
        prevMessages.map((msg) => {
          const newCardData = patchHydrationEntriesInCardData(msg.cardData, entry.id!, () => null);
          if (newCardData === msg.cardData) return msg;
          return { ...msg, cardData: newCardData };
        }),
      );
    } catch (err: any) {
      console.error('Error deleting hydration log:', err);
      alert(err.response?.data?.detail || 'Failed to delete hydration log. Please try again.');
    }
  };

  // ── edit / delete activity log ──────────────────────────────────────────────
  // Activity cards carry their own `id` directly on the card object (no nested
  // entries array), either as `cardData` itself (type === 'ACTIVITY') or as an
  // item inside `cardData.cards`.

  const patchActivityCardInCardData = (
    cardData: any,
    entryId: string,
    updater: (card: any) => any | null,
  ) => {
    if (!cardData) return cardData;
    let changed = false;
    let next = cardData;

    if (cardData.type === 'ACTIVITY' && cardData.id === entryId) {
      const rebuilt = updater(cardData);
      return rebuilt ?? cardData;
    }

    if (Array.isArray(cardData.cards)) {
      const newCards = cardData.cards
        .map((card: any) => {
          if (card?.type === 'ACTIVITY' && card.id === entryId) {
            changed = true;
            return updater(card);
          }
          return card;
        })
        .filter((c: any) => c !== null);
      if (changed) next = { ...next, cards: newCards };
    }

    return changed ? next : cardData;
  };

  const handleSaveEditedActivityLog = async (updatedData: {
    activity: string;
    durationMinutes?: number;
    reps?: number;
    sets?: number;
    intensity?: string;
  }) => {
    if (!editingActivityEntry?.id) return;

    const res = await apiClient.patch(`/activity-logs/${editingActivityEntry.id}`, updatedData);
    const updatedEntry = res.data?.entry || res.data;

    setMessages((prevMessages) =>
      prevMessages.map((msg) => {
        const newCardData = patchActivityCardInCardData(
          msg.cardData,
          editingActivityEntry.id!,
          (card) => ({
            ...card,
            title: updatedEntry.activityName || updatedEntry.activity || card.title,
            subtitle: `${updatedEntry.durationMinutes ? `${updatedEntry.durationMinutes} min` : card.subtitle} · MET ${updatedEntry.metValue ?? card.metValue}`,
            metric: `${Math.round(updatedEntry.caloriesBurned ?? card.caloriesBurned ?? 0)} kcal burned`,
            durationMinutes: updatedEntry.durationMinutes,
            reps: updatedEntry.reps,
            sets: updatedEntry.sets,
            caloriesBurned: updatedEntry.caloriesBurned,
            metValue: updatedEntry.metValue,
            intensity: updatedEntry.intensity,
          }),
        );
        if (newCardData === msg.cardData) return msg;
        return { ...msg, cardData: newCardData };
      }),
    );
  };

  const handleDeleteActivityLog = async (entry: ActivityEntryData) => {
    if (!entry.id) return;
    if (!window.confirm('Are you sure you want to delete this activity log?')) return;

    try {
      await apiClient.delete(`/activity-logs/${entry.id}`);
      setMessages((prevMessages) =>
        prevMessages.map((msg) => {
          const newCardData = patchActivityCardInCardData(msg.cardData, entry.id, () => null);
          if (newCardData === msg.cardData) return msg;
          return { ...msg, cardData: newCardData };
        }),
      );
    } catch (err: any) {
      console.error('Error deleting activity log:', err);
      alert(err.response?.data?.detail || 'Failed to delete activity log. Please try again.');
    }
  };

  // ── send message ───────────────────────────────────────────────────────────

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || loading) return;

    // ── Day-boundary check ───────────────────────────────────────────────────
    // If the local IST date has changed since we last opened a session,
    // silently open/create today's session before sending the message.
    const today = getTodayIST();
    if (today !== currentDayRef.current) {
      currentDayRef.current = today;
      try {
        const todayRes = await apiClient.get('/chat/today');
        const newSessionId: string = todayRes.data.id;
        const newTitle: string = todayRes.data.title;

        if (todayRes.data.created) {
          setSessions((prev) => {
            if (prev.some((s) => s.id === newSessionId)) return prev;
            return [
              {
                id: newSessionId,
                title: newTitle,
                logDate: todayRes.data.log_date,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              },
              ...prev,
            ];
          });
        }

        // Switch to the new session silently (no loadSession — keep blank)
        setMessages([]);
        setCurrentSessionId(newSessionId);
      } catch { /* non-fatal — continue with current session */ }
    }
    // ────────────────────────────────────────────────────────────────────────

    setError(null);
    setInputValue('');
    if (textareaRef.current) textareaRef.current.style.height = '48px';

    const userMsg: ChatMessageItem = {
      sender: 'USER',
      message: text,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    // Capture the session id that will be used for this message; use the
    // ref-value inside the closure to avoid stale state after the day-boundary
    // switch above.
    const sessionIdForRequest = currentSessionId;

    try {
      const res = await apiClient.post('/chat/message', {
        sessionId: sessionIdForRequest || undefined,
        message: text,
      });

      const rawData  = res.data || {};
      const dataObj  = rawData.data || {};
      const uiObj    = rawData.ui || dataObj.ui || {};

      const newSessionId: string | undefined = rawData.sessionId || dataObj.sessionId;

      // ── Session Title and Creation Sync ─────────────────────────────────
      const backendTitle = rawData.sessionTitle;
      const autoTitle = backendTitle || deriveTitleFromMessage(text);

      if (newSessionId && newSessionId !== sessionIdForRequest) {
        // Backend created a brand-new session
        setCurrentSessionId(newSessionId);

        setSessions((prev) => {
          const withoutPending = prev.filter(
            (s) => s.id !== sessionIdForRequest && s.id !== newSessionId,
          );
          return [
            {
              id: newSessionId,
              title: autoTitle,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            },
            ...withoutPending,
          ];
        });

        titledSessionsRef.current.add(newSessionId);
      } else if (newSessionId) {
        if (backendTitle) {
          setSessions((prev) =>
            prev.map((s) =>
              s.id === newSessionId ? { ...s, title: backendTitle, updatedAt: new Date().toISOString() } : s,
            ),
          );
        } else if (!titledSessionsRef.current.has(newSessionId)) {
          titledSessionsRef.current.add(newSessionId);
          apiClient
            .patch(`/chat/sessions/${newSessionId}/title`, { title: autoTitle })
            .catch(() => { /* non-fatal */ });

          setSessions((prev) =>
            prev.map((s) =>
              s.id === newSessionId ? { ...s, title: autoTitle, updatedAt: new Date().toISOString() } : s,
            ),
          );
        }
      }
      // ──────────────────────────────────────────────────────────────────────

      const foodCards =
        uiObj.groupedFoodCards ||
        dataObj.currentGroupedFoodCards ||
        dataObj.groupedFoodCards ||
        null;

      const dailySummary =
        uiObj.dailyNutritionSummary || dataObj.dailyNutritionSummary || null;

      const cards = uiObj.cards || dataObj.cards || null;

      const cardType =
        uiObj.type ||
        (foodCards && foodCards.length > 0 ? 'FOOD_LOG_CARDS' : rawData.cardType);

      const cardData =
        foodCards && foodCards.length > 0
          ? { groupedFoodCards: foodCards, dailyNutritionSummary: dailySummary, cards }
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

  // ── starter suggestions ────────────────────────────────────────────────────

  const starterSuggestions = [
    { label: 'Gujarati Meal', text: 'Savare 2 roti ane daal khadhi',     icon: Utensils },
    { label: 'Hindi Workout', text: 'Aaj maine 45 minute cardio kiya',   icon: Flame    },
    { label: 'Hydration',     text: 'Drank 500ml water just now',         icon: Droplets },
    { label: 'Weight Log',    text: 'My weight is 72.5 kg today',         icon: Scale    },
    { label: 'Daily Summary', text: 'What are my total calories today?',  icon: Sparkles },
  ];

  // ── render ─────────────────────────────────────────────────────────────────

  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden bg-slate-950">
      {/* Sidebar */}
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
          {sessions.map((s) => {
            const isSelected = currentSessionId === s.id;
            const isEditing = editingSessionId === s.id;

            if (isEditing) {
              return (
                <div
                  key={s.id}
                  className="w-full px-2 py-1.5 rounded-xl bg-slate-800 border border-emerald-500/40 flex items-center space-x-1.5"
                >
                  <input
                    type="text"
                    value={editTitleValue}
                    onChange={(e) => setEditTitleValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveRename(s.id, e);
                      if (e.key === 'Escape') cancelRename();
                    }}
                    autoFocus
                    className="flex-1 bg-slate-900 text-xs text-white px-2 py-1 rounded-lg border border-slate-700 focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    onClick={(e) => saveRename(s.id, e)}
                    className="p-1 hover:bg-emerald-500/20 text-emerald-400 rounded-lg transition-colors cursor-pointer"
                    title="Save title"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={cancelRename}
                    className="p-1 hover:bg-slate-700 text-slate-400 rounded-lg transition-colors cursor-pointer"
                    title="Cancel"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            }

            return (
              <div
                key={s.id}
                onClick={() => loadSession(s.id)}
                className={`group w-full px-3 py-2.5 rounded-xl text-xs flex items-center justify-between transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-slate-800 text-emerald-400 font-medium border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate flex-1 mr-1">
                  <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{s.title || 'Conversation'}</span>
                </div>
                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button
                    onClick={(e) => startRename(s, e)}
                    className="p-1 hover:bg-slate-700 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
                    title="Rename chat"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="p-1 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-lg transition-colors"
                    title="Delete chat"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
          {sessions.length === 0 && (
            <p className="text-xs text-slate-500 px-3 py-2">No past conversations</p>
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full bg-slate-900/40 relative">
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {error && (
            <div className="max-w-xl mx-auto p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center space-x-3 text-xs text-rose-300">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <div className="flex-1">{error}</div>
              <button onClick={() => setError(null)} className="hover:underline text-rose-200 font-semibold">
                Dismiss
              </button>
            </div>
          )}

          {initialLoading || sessionSwitching ? (
            <div className="h-full flex items-center justify-center">
              <div className="flex items-center space-x-2 text-slate-400 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                <span>{initialLoading ? 'Loading assistant...' : 'Loading conversation...'}</span>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4 max-w-xl mx-auto">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/25 mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">How can I help you today?</h3>
              <p className="text-sm text-slate-400 mb-8 max-w-md">
                Log your meals, workouts, water, weight, or sleep using natural language in
                English, Hindi, Gujarati, or Hinglish.
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
                          <span className="font-semibold text-slate-200">{item.label}: </span>
                          <span className="text-slate-400 group-hover:text-slate-300">"{item.text}"</span>
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
                  onEditHydrationLog={(entry) => setEditingHydrationEntry(entry)}
                  onDeleteHydrationLog={handleDeleteHydrationLog}
                  onEditActivityLog={(entry) => setEditingActivityEntry(entry)}
                  onDeleteActivityLog={handleDeleteActivityLog}
                />
              ))}
              {loading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/90 backdrop-blur-md">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
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

      <EditFoodLogModal
        isOpen={Boolean(editingEntry)}
        entry={editingEntry}
        onClose={() => setEditingEntry(null)}
        onSave={handleSaveEditedLog}
      />

      <EditHydrationLogModal
        isOpen={Boolean(editingHydrationEntry)}
        entry={editingHydrationEntry}
        onClose={() => setEditingHydrationEntry(null)}
        onSave={handleSaveEditedHydrationLog}
      />

      <EditActivityLogModal
        isOpen={Boolean(editingActivityEntry)}
        entry={editingActivityEntry}
        onClose={() => setEditingActivityEntry(null)}
        onSave={handleSaveEditedActivityLog}
      />
    </div>
  );
};
