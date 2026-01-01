import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { chatAPI, memoryAPI, providersAPI, imageAPI } from '../api/client';
import type { ChatMessage, ImageRef } from '../types/api';

function extractTitleFromFirstLine(text: string, maxLength: number = 50): string {
  const firstLine = text.split(/\r?\n/)[0].trim();
  
  if (firstLine.length <= maxLength) {
    return firstLine;
  }
  
  const truncated = firstLine.slice(0, maxLength);
  const lastSpaceIndex = truncated.lastIndexOf(' ');
  
  if (lastSpaceIndex > maxLength * 0.6) {
    return truncated.slice(0, lastSpaceIndex) + '...';
  }
  
  return truncated + '...';
}
import ImageUpload from './ImageUpload';
import MarkdownContent from './MarkdownContent';
import ProviderModelSelector from './ProviderModelSelector';

interface MessageWithMetadata extends ChatMessage {
  model?: string;
  model_requested?: string;
  backend?: string;
  tokens?: number;
  tokens_prompt?: number;
  provider?: string;
  image_refs?: ImageRef[];
}

interface ChatInterfaceProps {
  conversationId: string | null;
}

export default function ChatInterface({ conversationId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<MessageWithMetadata[]>([]);
  const [input, setInput] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const queryClient = useQueryClient();

  // Advanced settings
  const [temperature, setTemperature] = useState(1.0);
  const [maxTokens, setMaxTokens] = useState<number | undefined>(undefined);
  const [topP, setTopP] = useState(1.0);
  const [frequencyPenalty, setFrequencyPenalty] = useState(0.0);
  const [presencePenalty, setPresencePenalty] = useState(0.0);

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamingTokenCount, setStreamingTokenCount] = useState(0);
  const [streamStatus, setStreamStatus] = useState<{
    status: 'routing' | 'loading' | 'generating' | 'streaming' | 'done' | 'error' | null;
    message?: string;
    estimated_time?: number;
  }>({ status: null });

  // Image upload state
  const [pendingImages, setPendingImages] = useState<File[]>([]);

  // Active conversation ID (captured from first response or passed from props)
  const [activeConversationId, setActiveConversationId] = useState<string | null>(conversationId);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const firstMessageRef = useRef<string | null>(null);

  // Update activeConversationId when conversationId prop changes (e.g., selecting from sidebar)
  useEffect(() => {
    setActiveConversationId(conversationId);
  }, [conversationId]);

  // Fetch providers for dynamic model selection
  const { data: providersData, isLoading: isLoadingProviders } = useQuery({
    queryKey: ['admin-providers'],
    queryFn: () => providersAPI.listAdmin(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getModelForAPI = (): string => {
    if (!selectedProvider || !selectedModel) return 'auto';
    return `${selectedProvider}/${selectedModel}`;
  };

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-scroll during streaming
  useEffect(() => {
    if (isStreaming && streamingContent) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [streamingContent, isStreaming]);

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
      const chatMessages: MessageWithMetadata[] = loadedConversation.messages.map(msg => ({
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        model: msg.model_used,
        backend: msg.backend,
        tokens: msg.tokens_completion,
      }));
      setMessages(chatMessages);
      firstMessageRef.current = null;
    } else if (!conversationId) {
      setMessages([]);
      firstMessageRef.current = null;
    }
  }, [loadedConversation, conversationId]);

  const handleSendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    const imagesToUpload = [...pendingImages];

    // Reset streaming state
    setStreamingContent('');
    setStreamingTokenCount(0);
    setStreamStatus({ status: null });
    setIsStreaming(true);
    setInput('');
    setPendingImages([]);

    // Upload images if any
    let uploadedImageRefs: ImageRef[] = [];
    if (imagesToUpload.length > 0) {
      setStreamStatus({ status: 'routing', message: 'Uploading images...' });
      
      // Generate IDs for upload - use conversation ID or temp, and a temporary message ID
      const convId = conversationId || `temp-${Date.now()}`;
      const msgId = `msg-${Date.now()}`;
      
      try {
        uploadedImageRefs = await Promise.all(
          imagesToUpload.map(file => imageAPI.upload(file, convId, msgId))
        );
      } catch (error) {
        console.error('Image upload failed:', error);
        setStreamStatus({
          status: 'error',
          message: error instanceof Error ? error.message : 'Failed to upload images'
        });
        setTimeout(() => {
          setIsStreaming(false);
          setStreamStatus({ status: null });
        }, 2000);
        return;
      }
    }

    const isNewConversation = !activeConversationId && !conversationId;
    if (isNewConversation && messages.length === 0) {
      firstMessageRef.current = userMessage;
    }

    // Add user message to UI with uploaded images and routing info
    const modelRequested = getModelForAPI();
    const userMessageWithImages: MessageWithMetadata = {
      role: 'user',
      content: userMessage,
      image_refs: uploadedImageRefs.length > 0 ? uploadedImageRefs : undefined,
      model_requested: modelRequested,
    };
    setMessages(prev => [...prev, userMessageWithImages]);

    // Prepare messages for API
    const apiMessages: ChatMessage[] = [
      ...messages.map(m => ({ role: m.role, content: m.content })),
      { role: 'user', content: userMessage, image_refs: uploadedImageRefs.length > 0 ? uploadedImageRefs : undefined },
    ];

    try {
      const stream = chatAPI.sendMessageStream({
        model: getModelForAPI(),
        messages: apiMessages,
        conversationId: activeConversationId || conversationId || undefined,
        temperature,
        max_tokens: maxTokens,
        top_p: topP,
        frequency_penalty: frequencyPenalty,
        presence_penalty: presencePenalty,
      });

      for await (const event of stream) {
        switch (event.status) {
          case 'routing':
            setStreamStatus({
              status: 'routing',
              message: event.message || 'Selecting backend...'
            });
            break;

          case 'loading':
            setStreamStatus({
              status: 'loading',
              message: event.message || 'Warming up model...',
              estimated_time: event.estimated_time
            });
            break;

          case 'generating':
            setStreamStatus({
              status: 'generating',
              message: event.message || 'Generating response...'
            });
            break;

          case 'streaming':
            setStreamStatus({
              status: 'streaming',
              message: 'Streaming response...'
            });
            if (event.delta) {
              setStreamingContent(prev => prev + event.delta);
              setStreamingTokenCount(prev => prev + 1);
            }
            break;

          case 'done':
            const finalContent = event.content || streamingContent;
            setMessages(prev => {
              const updated = [...prev];
              let lastUserIndex = -1;
              for (let i = updated.length - 1; i >= 0; i--) {
                if (updated[i].role === 'user') {
                  lastUserIndex = i;
                  break;
                }
              }
              if (lastUserIndex !== -1 && event.usage?.prompt_tokens) {
                updated[lastUserIndex] = {
                  ...updated[lastUserIndex],
                  tokens_prompt: event.usage.prompt_tokens,
                };
              }
              return [
                ...updated,
                {
                  role: 'assistant',
                  content: finalContent,
                  model: event.model,
                  tokens: event.usage?.completion_tokens,
                  provider: event.provider_name,
                },
              ];
            });
            
            if (event.conversation_id && !activeConversationId) {
              setActiveConversationId(event.conversation_id);
              
              if (firstMessageRef.current) {
                const autoTitle = extractTitleFromFirstLine(firstMessageRef.current);
                memoryAPI.updateConversation(event.conversation_id, { title: autoTitle })
                  .then(() => queryClient.invalidateQueries({ queryKey: ['conversations'] }))
                  .catch(console.error);
                firstMessageRef.current = null;
              }
            }
            
            setIsStreaming(false);
            setStreamingContent('');
            setStreamingTokenCount(0);
            setStreamStatus({ status: null });
            break;

          case 'error':
            console.error('Stream error:', event.error_detail);
            setStreamStatus({
              status: 'error',
              message: event.error_detail || 'An error occurred'
            });
            setTimeout(() => {
              setIsStreaming(false);
              setStreamingContent('');
              setStreamingTokenCount(0);
              setStreamStatus({ status: null });
              // Remove the user message that failed
              setMessages(prev => prev.slice(0, -1));
            }, 2000);
            break;
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      setStreamStatus({
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
      setTimeout(() => {
        setIsStreaming(false);
        setStreamingContent('');
        setStreamingTokenCount(0);
        setStreamStatus({ status: null });
        // Remove the user message that failed
        setMessages(prev => prev.slice(0, -1));
      }, 2000);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-black">
      <div className="border-b border-gray-800 p-4 bg-gray-900">
        <div className="flex items-center justify-between">
          <ProviderModelSelector
            providers={providersData?.providers || []}
            isLoading={isLoadingProviders}
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            onProviderChange={setSelectedProvider}
            onModelChange={setSelectedModel}
            disabled={isStreaming}
          />

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
                {message.image_refs && message.image_refs.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {message.image_refs.map((img, imgIdx) => (
                      <a
                        key={imgIdx}
                        href={imageAPI.getUrl(img)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block"
                      >
                        <img
                          src={imageAPI.getUrl(img)}
                          alt={img.filename}
                          className="max-w-xs max-h-48 rounded border border-gray-700 hover:border-blue-500 transition-colors"
                        />
                      </a>
                    ))}
                  </div>
                )}
                <MarkdownContent content={message.content} />

                {/* Metadata for all messages */}
                <div className="mt-3 pt-3 border-t border-gray-800 flex flex-wrap gap-4 text-xs text-gray-500">
                  {message.role === 'user' ? (
                    <>
                      {message.tokens_prompt && (
                        <div>
                          <span className="text-gray-600">tokens:</span> {message.tokens_prompt.toLocaleString()}
                        </div>
                      )}
                      {message.model_requested && (
                        <div>
                          <span className="text-gray-600">routing:</span> {message.model_requested}
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {message.provider && (
                        <div>
                          <span className="text-gray-600">provider:</span> {message.provider}
                        </div>
                      )}
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
                    </>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Streaming message indicator */}
        {isStreaming && streamingContent && (
          <div className="group">
            {/* Message Header */}
            <div className="flex items-center gap-3 mb-2">
              <div className="text-xs font-mono uppercase text-green-400">
                ◂ ASSISTANT
              </div>
              <div className="text-xs text-gray-500">
                streaming... {streamingTokenCount} tokens
              </div>
            </div>

            {/* Message Content */}
            <div className="p-4 rounded border bg-gray-900 border-green-900/30 mr-6">
              <MarkdownContent content={streamingContent} />
              <span className="inline-block w-2 h-4 bg-green-400 ml-1 animate-pulse"></span>
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && streamStatus.status && (
          <div className="flex items-center gap-3 mb-2">
            <div className="text-xs font-mono uppercase text-green-400">
              ◂ ASSISTANT
            </div>
            <div className="flex items-center gap-2">
              {streamStatus.status !== 'error' && (
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              )}
              <div className={`text-xs ${
                streamStatus.status === 'error' ? 'text-red-400' : 'text-gray-500'
              }`}>
                {streamStatus.status === 'routing' && 'Selecting backend...'}
                {streamStatus.status === 'loading' && (
                  <span>
                    Warming up model...
                    {streamStatus.estimated_time && (
                      <span className="text-gray-600"> (~{Math.round(streamStatus.estimated_time)}s)</span>
                    )}
                  </span>
                )}
                {streamStatus.status === 'generating' && 'Generating response...'}
                {streamStatus.status === 'error' && streamStatus.message}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-800 p-4 bg-gray-900">
        <div className="mb-3">
          <ImageUpload
            onImagesSelected={(files) => setPendingImages(prev => [...prev, ...files])}
            onImageRemove={(index) => setPendingImages(prev => prev.filter((_, i) => i !== index))}
            pendingImages={pendingImages}
            uploadedImages={[]}
            disabled={isStreaming}
          />
        </div>
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
            disabled={!input.trim() || isStreaming}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors uppercase tracking-wider text-sm"
          >
            {isStreaming ? '...' : '▸ Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
