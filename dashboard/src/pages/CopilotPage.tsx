import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { cn } from '../lib/utils';
import {
  Send,
  Plus,
  Trash2,
  MessageSquare,
  Loader2,
  ExternalLink,
  Bot,
  User,
} from 'lucide-react';

interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

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
  const queryClient = useQueryClient();
  const [activeConv, setActiveConv] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: conversations } = useQuery<Conversation[]>({
    queryKey: ['copilot-conversations'],
    queryFn: async () => (await apiClient.get('/copilot/conversations')).data,
  });

  const { data: activeConversation, refetch: refetchConv } = useQuery({
    queryKey: ['copilot-conversation', activeConv],
    queryFn: async () => (await apiClient.get(`/copilot/conversations/${activeConv}`)).data,
    enabled: !!activeConv,
  });

  useEffect(() => {
    if (activeConversation?.messages) {
      setLocalMessages(activeConversation.messages);
    }
  }, [activeConversation]);

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

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/copilot/conversations/${id}`);
    },
    onSuccess: () => {
      if (activeConv) {
        setActiveConv(null);
        setLocalMessages([]);
      }
      queryClient.invalidateQueries({ queryKey: ['copilot-conversations'] });
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

  const handleNewChat = () => {
    setActiveConv(null);
    setLocalMessages([]);
    inputRef.current?.focus();
  };

  const handleSelectConv = (id: string) => {
    setActiveConv(id);
    refetchConv();
  };

  return (
    <div className="min-h-full flex">
      {/* Conversations sidebar */}
      <div className="w-64 border-r border-border bg-card flex flex-col shrink-0">
        <div className="p-3 border-b border-border">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations?.length === 0 && (
            <p className="text-xs text-muted-foreground text-center pt-4">No conversations yet</p>
          )}
          {conversations?.map((conv) => (
            <button
              key={conv.id}
              onClick={() => handleSelectConv(conv.id)}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left transition-colors group',
                activeConv === conv.id
                  ? 'bg-sidebar-active text-sidebar-active-fg'
                  : 'text-sidebar-foreground hover:bg-sidebar-hover hover:text-foreground'
              )}
            >
              <MessageSquare className="w-4 h-4 shrink-0" />
              <span className="flex-1 truncate">{conv.title || 'Chat'}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteMutation.mutate(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col bg-background">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {localMessages.length === 0 && !streaming && (
            <div className="flex flex-col items-center justify-center h-full text-center px-6">
              <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <Bot className="w-7 h-7 text-primary" />
              </div>
              <h2 className="text-lg font-semibold text-foreground mb-1">HR Copilot</h2>
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
            <div key={msg.id} className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
              )}
              <div className={cn('max-w-[70%] space-y-2', msg.role === 'user' && 'items-end')}>
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
                        <ExternalLink className="w-3 h-3 shrink-0 mt-0.5 text-primary" />
                        <span className="line-clamp-2">{src.title || src.snippet || src.source || 'Source'}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}

          {streaming && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
                <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border p-4 bg-card">
          <div className="flex items-center gap-2 max-w-4xl mx-auto">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
              placeholder="Ask about HR policies, attendance data..."
              disabled={streaming}
              className="flex-1 px-4 py-2.5 bg-background border border-border rounded-xl text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || streaming}
              className="w-10 h-10 flex items-center justify-center rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
