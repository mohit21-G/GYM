import React from 'react';
import { Bot, User } from 'lucide-react';
import { format } from 'date-fns';
import { StructuredCard } from './Cards';
import { FoodLogEntryData } from '../food/FoodLogEntry';
import { HydrationEntryItem } from '../hydration/DailyHydrationSummary';
import { ActivityEntryData } from '../activity/EditActivityLogModal';

export interface ChatMessageItem {
  id?: string;
  sender: 'USER' | 'ASSISTANT';
  message: string;
  createdAt?: string | Date;
  cardType?: string;
  cardData?: any;
}

interface MessageBubbleProps {
  msg: ChatMessageItem;
  onSelectOption?: (text: string) => void;
  onEditFoodLog?: (entry: FoodLogEntryData) => void;
  onDeleteFoodLog?: (entry: FoodLogEntryData) => void;
  onEditHydrationLog?: (entry: HydrationEntryItem) => void;
  onDeleteHydrationLog?: (entry: HydrationEntryItem) => void;
  onEditActivityLog?: (entry: ActivityEntryData) => void;
  onDeleteActivityLog?: (entry: ActivityEntryData) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  msg,
  onSelectOption,
  onEditFoodLog,
  onDeleteFoodLog,
  onEditHydrationLog,
  onDeleteHydrationLog,
  onEditActivityLog,
  onDeleteActivityLog,
}) => {
  const isUser = msg.sender === 'USER';
  const timestamp = msg.createdAt ? format(new Date(msg.createdAt), 'h:mm a') : '';

  const renderFormattedMessage = (content: string) => {
    if (!content) return null;

    const rawLines = content.split('\n');
    const renderedElements: React.ReactNode[] = [];
    let currentBulletGroup: React.ReactNode[] = [];

    const flushBullets = () => {
      if (currentBulletGroup.length > 0) {
        renderedElements.push(
          <ul key={`list-${renderedElements.length}`} className="my-2 space-y-1.5 pl-1">
            {currentBulletGroup}
          </ul>
        );
        currentBulletGroup = [];
      }
    };

    const formatInlineText = (text: string): React.ReactNode => {
      const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
      return parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
          return (
            <strong
              key={index}
              className={isUser ? 'font-semibold text-white' : 'font-semibold text-emerald-400'}
            >
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith('*') && part.endsWith('*') && part.length > 2 && !part.startsWith('**')) {
          return (
            <em key={index} className="italic text-slate-300">
              {part.slice(1, -1)}
            </em>
          );
        }
        return part;
      });
    };

    rawLines.forEach((line, index) => {
      const trimmed = line.trim();

      if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
        const bulletContent = trimmed.slice(2);
        currentBulletGroup.push(
          <li key={`bullet-${index}`} className="flex items-start space-x-2 text-sm leading-snug">
            <span
              className={
                isUser
                  ? 'text-emerald-200 font-bold select-none'
                  : 'text-emerald-400 font-bold select-none'
              }
            >
              •
            </span>
            <span className="flex-1">{formatInlineText(bulletContent)}</span>
          </li>
        );
      } else {
        flushBullets();
        if (!trimmed) {
          renderedElements.push(<div key={`space-${index}`} className="h-2" />);
        } else {
          renderedElements.push(
            <div key={`line-${index}`} className="text-sm leading-relaxed">
              {formatInlineText(line)}
            </div>
          );
        }
      }
    });

    flushBullets();
    return <div className="space-y-0.5 whitespace-pre-wrap">{renderedElements}</div>;
  };

  const hasCards = !isUser && Boolean(msg.cardData);

  return (
    <div
      className={`flex items-start space-x-3 ${
        isUser
          ? 'ml-auto flex-row-reverse space-x-reverse max-w-xl'
          : hasCards
          ? 'w-full max-w-2xl'
          : 'max-w-xl'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md ${
          isUser
            ? 'bg-slate-700 text-slate-200'
            : 'bg-gradient-to-tr from-emerald-500 to-teal-400 text-white shadow-emerald-500/20'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Content */}
      <div
        className={`relative rounded-2xl px-4 py-3 shadow-md ${
          isUser
            ? 'bg-emerald-600 text-white rounded-tr-sm max-w-xl'
            : hasCards
            ? 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-tl-sm w-full max-w-2xl min-w-0 box-border'
            : 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-tl-sm max-w-xl'
        }`}
      >
        {renderFormattedMessage(msg.message)}

        {/* Structured card if provided */}
        {!isUser && msg.cardData && (
          <StructuredCard
            cardType={msg.cardType}
            data={msg.cardData}
            onSelectOption={onSelectOption}
            onEditEntry={onEditFoodLog}
            onDeleteEntry={onDeleteFoodLog}
            onEditHydrationEntry={onEditHydrationLog}
            onDeleteHydrationEntry={onDeleteHydrationLog}
            onEditActivityEntry={onEditActivityLog}
            onDeleteActivityEntry={onDeleteActivityLog}
          />
        )}

        {timestamp && (
          <div
            className={`text-[10px] mt-1 text-right ${
              isUser ? 'text-emerald-200/80' : 'text-slate-400'
            }`}
          >
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
};
