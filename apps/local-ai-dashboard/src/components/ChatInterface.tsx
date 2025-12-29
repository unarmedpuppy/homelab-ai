import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { chatAPI, memoryAPI } from '../api/client';
import type { ChatMessage } from '../types/api';

interface MessageWithMetadata extends ChatMessage {
  model?: string;
  backend?: string;
  tokens?: number;
}

interface ChatInterfaceProps {
  conversationId: string | null;
}

const MODEL_OPTIONS = [
  { value: 'auto', label: 'Auto (Intelligent Routing)' },
  { value: 'small', label: 'Small (3070)' },
  { value: 'fast', label: 'Fast (3070)' },
  { value: 'big', label: 'Big (3090)' },
  { value: 'medium', label: 'Medium (3090)' },
  { value: '3090', label: '3090 GPU' },
  { value: 'gaming-pc', label: 'Gaming PC' },
  { value: 'glm', label: 'GLM-4.7' },
  { value: 'claude', label: 'Claude (OpenCode)' },
];

export default function ChatInterface({ conversationId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<MessageWithMetadata[]>([]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('auto');
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Advanced settings
  const [temperature, setTemperature] = useState(1.0);
  const [maxTokens, setMaxTokens] = useState<number | undefined>(undefined);
  const [topP, setTopP] = useState(1.0);
  const [frequencyPenalty, setFrequencyPenalty] = useState(0.0);
  const [presencePenalty, setPresencePenalty] = useState(0.0);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load conversation when conversationId changes
  const { data: loadedConversation, isLoading: isLoadingConversation } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => memoryAPI.getConversation(conversationId!),
    enabled: !!conversationId,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (loadedConversation?.messages) {
      // Convert loaded messages to chat format
      const chatMessages: MessageWithMetadata[] = loadedConversation.messages.map(msg => ({
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        model: msg.model_used,
        backend: msg.backend,
        tokens: msg.tokens_completion,
      }));
      setMessages(chatMessages);
    } else if (!conversationId) {
      // New chat - clear messages
      setMessages([]);
    }
  }, [loadedConversation, conversationId]);

  const sendMessageMutation = useMutation({
    mutationFn: async () => {
      // messages already includes the userMessage from optimistic update in handleSendMessage
      const newMessages: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }));

      return chatAPI.sendMessage({
        model: selectedModel,
        messages: newMessages,
        conversationId: conversationId || undefined,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
        frequency_penalty: frequencyPenalty,
        presence_penalty: presencePenalty,
      });
    },
    onSuccess: (response) => {
      const assistantMessage = response.choices[0].message;
      // Add assistant response to existing messages
      setMessages(prev => [
        ...prev,
        {
          role: assistantMessage.role,
          content: assistantMessage.content,
          model: response.model,
          tokens: response.usage?.completion_tokens,
        },
      ]);
    },
    onError: (error) => {
      // Log error for debugging
      console.error('Chat API error:', error);
      // Remove the user message that failed to send
      setMessages(prev => prev.slice(0, -1));
    },
  });

  const handleSendMessage = () => {
    if (!input.trim() || sendMessageMutation.isPending) return;

    const userMessage = input.trim();

    // Immediately add user message to UI and clear input
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');

    // Send to API (messages state already includes the new user message)
    sendMessageMutation.mutate();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-black">
      {/* Header */}
      <div className="border-b border-gray-800 p-4 bg-gray-900">
        <div className="flex items-center justify-between">
          {/* Model Selector */}
          <div className="flex items-center gap-4">
            <label className="text-xs uppercase tracking-wider text-gray-500">
              Model:
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:border-blue-500 focus:outline-none"
            >
              {MODEL_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Settings Toggle */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
              showAdvanced
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            ⚙️ Advanced
          </button>
        </div>

        {/* Advanced Settings Panel */}
        {showAdvanced && (
          <div className="mt-4 p-4 bg-gray-800 border border-gray-700 rounded space-y-4">
            <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">
              Advanced Settings
            </div>

            {/* Temperature */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500">Temperature</label>
                <span className="text-sm text-white">{temperature.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            {/* Max Tokens */}
            <div>
              <label className="text-xs text-gray-500 block mb-2">Max Tokens (optional)</label>
              <input
                type="number"
                value={maxTokens || ''}
                onChange={(e) => setMaxTokens(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Unlimited"
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Top P */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500">Top P</label>
                <span className="text-sm text-white">{topP.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            {/* Frequency Penalty */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500">Frequency Penalty</label>
                <span className="text-sm text-white">{frequencyPenalty.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={frequencyPenalty}
                onChange={(e) => setFrequencyPenalty(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            {/* Presence Penalty */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-gray-500">Presence Penalty</label>
                <span className="text-sm text-white">{presencePenalty.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={presencePenalty}
                onChange={(e) => setPresencePenalty(Number(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {isLoadingConversation ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500 text-sm">Loading conversation...</div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500 text-sm">
              ▸ Start a new conversation
            </div>
          </div>
        ) : (
          messages.map((message, idx) => (
            <div key={idx} className="group">
              {/* Message Header */}
              <div className="flex items-center gap-3 mb-2">
                <div className={`text-xs font-mono uppercase ${
                  message.role === 'user' ? 'text-blue-400' : 'text-green-400'
                }`}>
                  {message.role === 'user' ? '▸ USER' : '◂ ASSISTANT'}
                </div>
              </div>

              {/* Message Content */}
              <div className={`p-4 rounded border ${
                message.role === 'user'
                  ? 'bg-gray-900 border-blue-900/30 ml-6'
                  : 'bg-gray-900 border-green-900/30 mr-6'
              }`}>
                <div className="text-gray-300 whitespace-pre-wrap text-sm">
                  {message.content}
                </div>

                {/* Metadata (only for assistant messages) */}
                {message.role === 'assistant' && (message.model || message.backend || message.tokens) && (
                  <div className="mt-3 pt-3 border-t border-gray-800 flex flex-wrap gap-4 text-xs text-gray-500">
                    {message.model && (
                      <div>
                        <span className="text-gray-600">model:</span> {message.model}
                      </div>
                    )}
                    {message.backend && (
                      <div>
                        <span className="text-gray-600">backend:</span> {message.backend}
                      </div>
                    )}
                    {message.tokens && (
                      <div>
                        <span className="text-gray-600">tokens:</span> {message.tokens.toLocaleString()}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading indicator */}
        {sendMessageMutation.isPending && (
          <div className="flex items-center gap-3 mb-2">
            <div className="text-xs font-mono uppercase text-green-400">
              ◂ ASSISTANT
            </div>
            <div className="text-xs text-gray-500">typing...</div>
          </div>
        )}

        {/* Error display */}
        {sendMessageMutation.isError && (
          <div className="bg-gray-800 border border-red-800 rounded p-4">
            <div className="text-xs uppercase tracking-wider text-red-400 mb-2">Error</div>
            <div className="text-red-300 text-sm">
              {String(sendMessageMutation.error)}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-800 p-4 bg-gray-900">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Shift+Enter for new line)"
            rows={3}
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded text-white placeholder-gray-600 focus:border-blue-500 focus:outline-none text-sm resize-none"
          />
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || sendMessageMutation.isPending}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors uppercase tracking-wider text-sm"
          >
            {sendMessageMutation.isPending ? '...' : '▸ Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
