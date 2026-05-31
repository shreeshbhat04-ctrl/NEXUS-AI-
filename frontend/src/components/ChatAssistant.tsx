import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { MessageCircle, X, Send, Loader2 } from 'lucide-react';
import { confirmAction, sendTextMessage, type ActionOption, type ConversationResponse } from '../lib/api';
import { Pill } from './ui';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  routeType?: string;
  actionId?: number;
  intent?: string;
  question?: string;
  options?: ActionOption[];
  allowCustomInput?: boolean;
}

interface ChatAssistantProps {
  patientId: number;
}

export const ChatAssistant: React.FC<ChatAssistantProps> = ({ patientId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({});
  const [confirmingActionId, setConfirmingActionId] = useState<number | null>(null);
  const [resolvedActions, setResolvedActions] = useState<Record<number, boolean>>({});
  
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isProcessing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsProcessing(true);

    try {
      const response: ConversationResponse = await sendTextMessage(patientId, userMessage.content);
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        model: response.primary_model,
        routeType: response.route_type,
        actionId: response.action_id,
        intent: response.intent,
        question: response.question,
        options: response.options,
        allowCustomInput: response.allow_custom_input,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: err instanceof Error ? err.message : 'I apologize, something went wrong with the connection.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleActionConfirm = async (message: Message, selectedOption?: string, useCustom: boolean = false) => {
    if (!message.actionId || confirmingActionId === message.actionId) return;
    const customInput = (customInputs[message.id] || '').trim();
    if (useCustom && !customInput) return;

    setConfirmingActionId(message.actionId);
    try {
      const result = await confirmAction(
        message.actionId,
        selectedOption,
        useCustom ? customInput : undefined,
      );
      setResolvedActions((prev) => ({ ...prev, [message.actionId as number]: true }));
      const resultMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content:
          (result.result?.message as string | undefined) ||
          `Action ${result.status}.`,
      };
      setMessages((prev) => [...prev, resultMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: 'assistant',
        content: err instanceof Error ? err.message : 'Failed to confirm this action.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setConfirmingActionId(null);
    }
  };

  return (
    <div className="fixed bottom-6 right-28 z-[100] flex flex-col items-end gap-4">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95, transformOrigin: 'bottom right' }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="w-[360px] md:w-[400px] overflow-hidden rounded-[1.75rem] border border-white/10 bg-surface/95 shadow-[0_24px_54px_-12px_rgba(60,64,67,0.15)] backdrop-blur-2xl flex flex-col max-h-[600px] h-[70vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/5 bg-white/5 px-6 py-4">
              <div>
                <h3 className="font-serif text-[1.1rem] font-medium text-primary">Copilot Chat</h3>
                <p className="text-[0.8rem] text-on-surface/50">Ask about care, symptoms, or routines</p>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full bg-white/10 p-2 text-on-surface/50 transition-colors hover:bg-white/20 hover:text-on-surface"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center text-on-surface/40">
                  <MessageCircle className="mb-3 h-8 w-8 opacity-50" />
                  <p className="text-[0.95rem]">How can I help you today?</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                    {msg.role === 'assistant' && msg.model && (
                      <div className="mb-1.5 ml-1">
                        <Pill tone={msg.routeType === 'medical_text' ? 'terracotta' : 'sage'}>
                          {msg.model.split('/')[1] || msg.model}
                        </Pill>
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-[1.25rem] px-4 py-3 text-[0.95rem] leading-7 ${
                        msg.role === 'user'
                          ? 'bg-primary text-surface rounded-tr-sm'
                          : 'bg-surface-container-low text-on-surface/85 rounded-tl-sm'
                      }`}
                    >
                      {msg.content}
                    </div>
                    {msg.role === 'assistant' &&
                      msg.actionId &&
                      !resolvedActions[msg.actionId] &&
                      msg.options &&
                      msg.options.length > 0 && (
                        <div className="mt-2 w-full max-w-[85%] rounded-2xl border border-outline-variant/20 bg-surface-container-lowest p-3">
                          <p className="mb-2 text-[0.75rem] font-semibold uppercase tracking-wide text-on-surface/50">
                            Confirm Action
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {msg.options.map((option) => (
                              <button
                                key={`${msg.id}-${option.value}`}
                                onClick={() => handleActionConfirm(msg, option.value)}
                                disabled={confirmingActionId === msg.actionId}
                                className="rounded-xl bg-primary-container px-3 py-2 text-left text-[0.82rem] text-on-primary-container transition-colors hover:bg-primary/20 disabled:opacity-60"
                              >
                                {option.label}
                              </button>
                            ))}
                          </div>
                          {msg.allowCustomInput && (
                            <div className="mt-3 flex items-center gap-2">
                              <input
                                type="text"
                                value={customInputs[msg.id] || ''}
                                onChange={(e) =>
                                  setCustomInputs((prev) => ({ ...prev, [msg.id]: e.target.value }))
                                }
                                placeholder="Custom input"
                                className="input-shell h-10 flex-1"
                              />
                              <button
                                onClick={() => handleActionConfirm(msg, undefined, true)}
                                disabled={confirmingActionId === msg.actionId}
                                className="rounded-xl bg-secondary-container px-3 py-2 text-[0.8rem] text-on-secondary-container disabled:opacity-60"
                              >
                                {confirmingActionId === msg.actionId ? 'Sending...' : 'Send'}
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                  </div>
                ))
              )}
              {isProcessing && (
                <div className="flex items-center gap-2 text-on-surface/50 pt-2 pb-1">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-[0.85rem]">Thinking...</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input Form */}
            <div className="border-t border-white/5 bg-white/5 p-4">
              <form onSubmit={handleSubmit} className="flex items-center gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Type a message..."
                  className="input-shell flex-1"
                  disabled={isProcessing}
                />
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isProcessing}
                  className="flex h-[3.15rem] w-[3.15rem] flex-shrink-0 items-center justify-center rounded-[1rem] bg-secondary-container text-on-secondary-container transition-transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100"
                >
                  <Send className="h-5 w-5" />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`relative flex h-16 w-16 items-center justify-center rounded-full shadow-xl transition-all duration-300 ${
            isOpen
              ? 'bg-surface-container-high text-on-surface'
              : 'bg-gradient-to-tr from-secondary to-tertiary text-white hover:scale-105'
          }`}
        >
          {isOpen ? <X className="h-7 w-7" /> : <MessageCircle className="h-7 w-7" />}
        </button>
      </div>
    </div>
  );
};
