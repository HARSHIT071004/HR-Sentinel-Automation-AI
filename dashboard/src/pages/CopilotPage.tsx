import { useState, useRef, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import apiClient from '../api/client';
import { cn } from '../lib/utils';
import {
  Send,
  Loader2,
  FileText,
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: string;
  content: string;
  sources: { title?: string; snippet?: string; source?: string }[] | null;
  created_at: string;
}

interface ChatResponse {
  conversation_id: string;
  response: string;
  sources: { title?: string; snippet?: string; source?: string }[];
}

export default function CopilotPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle ?new=1 for new chat from Layout button
  useEffect(() => {
    if (searchParams.get('new') === '1') {
      setActiveConv(null);
      setLocalMessages([]);
      searchParams.delete('new');
      setSearchParams(searchParams, { replace: true });
      inputRef.current?.focus();
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [localMessages]);

  const sendMutation = useMutation({
    mutationFn: async (message: string) => {
      const res = await apiClient.post<ChatResponse>('/copilot/chat', {
        message,
        conversation_id: activeConv,
      });
      return res.data;
    },
    onMutate: () => setStreaming(true),
    onSuccess: (data) => {
      setLocalMessages((prev) => [
        ...prev,
        {
          id: data.conversation_id + '-resp',
          role: 'assistant',
          content: data.response,
          sources: data.sources || null,
          created_at: new Date().toISOString(),
        },
      ]);
      setActiveConv(data.conversation_id);
      queryClient.invalidateQueries({ queryKey: ['copilot-conversations'] });
    },
    onSettled: () => {
      setStreaming(false);
    },
  });

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || streaming) return;
    setInput('');
    setLocalMessages((prev) => [
      ...prev,
      {
        id: 'user-' + Date.now(),
        role: 'user',
        content: msg,
        sources: null,
        created_at: new Date().toISOString(),
      },
    ]);
    sendMutation.mutate(msg);
  };

  return (
    <div className="min-h-full flex flex-col bg-background">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {localMessages.length === 0 && !streaming && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <h2 className="text-lg font-semibold text-foreground mb-1">How can I help you?</h2>
            <p className="text-sm text-muted-foreground max-w-md">
              Ask me anything about HR policies, attendance data, or workforce insights.
            </p>
            <div className="mt-6 grid grid-cols-1 gap-2 w-full max-w-sm">
              {[
                'What is the attendance policy?',
                'Show me late arrival trends',
                'Summarize leave policy',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="text-left px-4 py-2.5 rounded-lg bg-card border border-border text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {localMessages.map((msg) => (
          <div key={msg.id} className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div className={cn('max-w-[70%] space-y-2')}>
              <div
                className={cn(
                  'rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-sm'
                    : 'bg-card border border-border rounded-tl-sm text-foreground/90'
                )}
              >
                {msg.content}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium px-1">
                    Sources
                  </p>
                  {msg.sources.map((src, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-1.5 px-3 py-1.5 rounded-lg bg-muted/50 border border-border text-xs text-muted-foreground"
                    >
                      <FileText className="w-3 h-3 shrink-0 mt-0.5 text-primary" />
                      <span className="line-clamp-2">{src.title || src.snippet || src.source || 'Source'}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {streaming && (
          <div className="flex justify-start">
            <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 shrink-0">
        <div className="max-w-3xl mx-auto border border-border rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden">
          <textarea
            ref={inputRef as any}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ask about HR policies, attendance data..."
            disabled={streaming}
            rows={2}
            className="w-full px-5 pt-4 pb-2 bg-transparent text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none disabled:opacity-50"
            style={{ fieldSizing: 'content' } as any}
          />
          <div className="flex items-center justify-end px-3 pb-3">
            <button
              onClick={handleSend}
              disabled={!input.trim() || streaming}
              className="w-9 h-9 flex items-center justify-center rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
