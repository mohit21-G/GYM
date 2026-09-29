import React from 'react';
import { Bot, User } from 'lucide-react';
import { format } from 'date-fns';
import { StructuredCard } from './Cards';

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
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  msg,
  onSelectOption,
}) => {
  const isUser = msg.sender === 'USER';
  const timestamp = msg.createdAt ? format(new Date(msg.createdAt), 'h:mm a') : '';

  return (
    <div
      className={`flex items-start space-x-3 max-w-3xl ${
        isUser ? 'ml-auto flex-row-reverse space-x-reverse' : ''
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
        className={`relative rounded-2xl px-4 py-3 shadow-md max-w-xl ${
          isUser
            ? 'bg-emerald-600 text-white rounded-tr-sm'
            : 'bg-slate-800 text-slate-100 border border-slate-700/60 rounded-tl-sm'
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.message}</p>

        {/* Structured card if provided */}
        {!isUser && msg.cardData && (
          <StructuredCard
            cardType={msg.cardType}
            data={msg.cardData}
            onSelectOption={onSelectOption}
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
