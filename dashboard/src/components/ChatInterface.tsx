import { useState, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { chatAPI, memoryAPI, providersAPI, imageAPI, ttsAPI, TTSError } from '../api/client';
import type { ChatMessage, ImageRef } from '../types/api';
import { Toast } from './Toast';
import { RetroButton } from './ui';

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

  // TTS state
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [ttsPlayingIdx, setTtsPlayingIdx] = useState<number | null>(null);
  const [ttsGeneratingIdx, setTtsGeneratingIdx] = useState<number | null>(null);
  
  const [toast, setToast] = useState<{message: string, type: 'error' | 'info' | 'success'} | null>(null);
  const [ttsAvailable, setTtsAvailable] = useState(false);

  useEffect(() => {
    ttsAPI.checkAvailable().then(setTtsAvailable);
  }, []);

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
            
            if (ttsEnabled) {
              handleTtsPlayback(finalContent, messages.length);
            }
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

  const handleTtsPlayback = async (text: string, messageIdx?: number) => {
    if (!ttsAvailable) return;
    
    try {
      setTtsGeneratingIdx(messageIdx ?? -1);
      const audioBlob = await ttsAPI.generateSpeech(text);
      setTtsGeneratingIdx(null);
      setTtsPlayingIdx(messageIdx ?? -1);
      await ttsAPI.playAudio(audioBlob);
      setTtsPlayingIdx(null);
    } catch (error) {
      console.error('TTS error:', error);
      setTtsGeneratingIdx(null);
      setTtsPlayingIdx(null);
      
      if (error instanceof TTSError) {
        setToast({ message: error.userMessage, type: 'error' });
      } else {
        setToast({ message: 'TTS playback failed', type: 'error' });
      }
    }
  };

  const handlePlayMessageTts = (messageIdx: number) => {
    const message = messages[messageIdx];
    if (message && message.role === 'assistant') {
      handleTtsPlayback(message.content, messageIdx);
    }
  };

  const isTtsBusy = ttsGeneratingIdx !== null || ttsPlayingIdx !== null;

  return (
    <div className="flex flex-col h-full bg-[var(--retro-bg-dark)]">
      {/* Header Panel */}
      <div className="border-b-2 border-[var(--retro-border)] p-3 sm:p-4 bg-[var(--retro-bg-medium)]">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <ProviderModelSelector
            providers={providersData?.providers || []}
            isLoading={isLoadingProviders}
            selectedProvider={selectedProvider}
            selectedModel={selectedModel}
            onProviderChange={setSelectedProvider}
            onModelChange={setSelectedModel}
            disabled={isStreaming}
          />

          <div className="flex items-center gap-2">
            {ttsAvailable && (
              <RetroButton
                variant={ttsEnabled ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setTtsEnabled(!ttsEnabled)}
                disabled={isTtsBusy}
                icon={<span>🔊</span>}
              >
                Auto
              </RetroButton>
            )}
            <RetroButton
              variant={showAdvanced ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
              icon={<span>⚙️</span>}
            >
              Advanced
            </RetroButton>
          </div>
        </div>

        {/* Advanced Settings Panel */}
        {showAdvanced && (
          <div className="mt-4 p-4 bg-[var(--retro-bg-card)] border border-[var(--retro-border)] rounded space-y-4">
            <div className="text-xs text-[var(--retro-text-secondary)] mb-3 font-semibold">
              Advanced Settings
            </div>

            {/* Temperature */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-[var(--retro-text-muted)]">Temperature</label>
                <span className="text-sm text-[var(--retro-accent-cyan)] font-mono">{temperature.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full h-2 bg-[var(--retro-bg-dark)] rounded appearance-none cursor-pointer accent-[var(--retro-accent-cyan)]"
              />
            </div>

            {/* Max Tokens */}
            <div>
              <label className="text-xs text-[var(--retro-text-muted)] block mb-2">Max Tokens (optional)</label>
              <input
                type="number"
                value={maxTokens || ''}
                onChange={(e) => setMaxTokens(e.target.value ? Number(e.target.value) : undefined)}
                placeholder="Unlimited"
                className="retro-input text-sm"
              />
            </div>

            {/* Top P */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-[var(--retro-text-muted)]">Top P</label>
                <span className="text-sm text-[var(--retro-accent-cyan)] font-mono">{topP.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(Number(e.target.value))}
                className="w-full h-2 bg-[var(--retro-bg-dark)] rounded appearance-none cursor-pointer accent-[var(--retro-accent-cyan)]"
              />
            </div>

            {/* Frequency Penalty */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-[var(--retro-text-muted)]">Frequency Penalty</label>
                <span className="text-sm text-[var(--retro-accent-cyan)] font-mono">{frequencyPenalty.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={frequencyPenalty}
                onChange={(e) => setFrequencyPenalty(Number(e.target.value))}
                className="w-full h-2 bg-[var(--retro-bg-dark)] rounded appearance-none cursor-pointer accent-[var(--retro-accent-cyan)]"
              />
            </div>

            {/* Presence Penalty */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs text-[var(--retro-text-muted)]">Presence Penalty</label>
                <span className="text-sm text-[var(--retro-accent-cyan)] font-mono">{presencePenalty.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={presencePenalty}
                onChange={(e) => setPresencePenalty(Number(e.target.value))}
                className="w-full h-2 bg-[var(--retro-bg-dark)] rounded appearance-none cursor-pointer accent-[var(--retro-accent-cyan)]"
              />
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4">
        {isLoadingConversation ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-[var(--retro-text-muted)] text-sm retro-animate-pulse">
              Loading conversation...
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-[var(--retro-text-muted)] text-sm">
              ▸ Start a new conversation
            </div>
          </div>
        ) : (
          messages.map((message, idx) => (
            <div key={idx} className="group">
              {/* Message Header */}
              <div className="flex items-center gap-3 mb-2">
                <div className={`text-xs font-semibold ${
                  message.role === 'user' ? 'text-[var(--retro-accent-blue)]' : 'text-[var(--retro-accent-green)]'
                }`}>
                  {message.role === 'user' ? 'You' : 'Assistant'}
                </div>
              </div>

              {/* Message Content - Retro styled bubble */}
              <div className={`p-3 sm:p-4 rounded border ${
                message.role === 'user'
                  ? 'bg-[var(--retro-bg-light)] border-[var(--retro-border)] ml-0 sm:ml-6'
                  : 'bg-[var(--retro-bg-medium)] border-[var(--retro-accent-green)] mr-0 sm:mr-6'
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
                          className="max-w-xs max-h-48 rounded border border-[var(--retro-border)] hover:border-[var(--retro-accent-cyan)] transition-colors"
                        />
                      </a>
                    ))}
                  </div>
                )}
                <MarkdownContent content={message.content} />

                {/* Metadata for all messages */}
                <div className="mt-3 pt-3 border-t border-[var(--retro-border)] flex flex-wrap items-center gap-3 sm:gap-4 text-xs text-[var(--retro-text-muted)]">
                  {message.role === 'user' ? (
                    <>
                      {message.tokens_prompt && (
                        <div className="font-mono">
                          <span className="text-[var(--retro-text-muted)]">tokens:</span>{' '}
                          <span className="text-[var(--retro-accent-cyan)]">{message.tokens_prompt.toLocaleString()}</span>
                        </div>
                      )}
                      {message.model_requested && (
                        <div className="font-mono">
                          <span className="text-[var(--retro-text-muted)]">routing:</span>{' '}
                          <span className="text-[var(--retro-accent-cyan)]">{message.model_requested}</span>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {ttsAvailable && (
                        <RetroButton
                          variant={ttsPlayingIdx === idx ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => handlePlayMessageTts(idx)}
                          disabled={isTtsBusy && ttsPlayingIdx !== idx && ttsGeneratingIdx !== idx}
                          loading={ttsGeneratingIdx === idx}
                          icon={<span>🔊</span>}
                        >
                          {ttsPlayingIdx === idx ? 'Playing...' : 'Play'}
                        </RetroButton>
                      )}
                      {message.provider && (
                        <div className="font-mono">
                          <span className="text-[var(--retro-text-muted)]">provider:</span>{' '}
                          <span className="text-[var(--retro-accent-cyan)]">{message.provider}</span>
                        </div>
                      )}
                      {message.model && (
                        <div className="font-mono">
                          <span className="text-[var(--retro-text-muted)]">model:</span>{' '}
                          <span className="text-[var(--retro-accent-cyan)]">{message.model}</span>
                        </div>
                      )}
                      {message.backend && (
                        <div className="font-mono">
                          <span className="text-[var(--retro-text-muted)]">backend:</span>{' '}
                          <span className="text-[var(--retro-accent-cyan)]">{message.backend}</span>
                        </div>
                      )}
                      {message.tokens && (
                        <div className="font-mono">
                          <span className="text-[var(--retro-text-muted)]">tokens:</span>{' '}
                          <span className="text-[var(--retro-accent-cyan)]">{message.tokens.toLocaleString()}</span>
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
              <div className="text-xs font-semibold text-[var(--retro-text-secondary)]">
                Assistant
              </div>
              <div className="text-xs text-[var(--retro-text-muted)]">
                streaming... <span className="text-[var(--retro-accent-cyan)]">{streamingTokenCount}</span> tokens
              </div>
            </div>

            {/* Message Content - Retro styled streaming bubble */}
            <div
              className="p-3 sm:p-4 rounded border bg-[var(--retro-bg-medium)] border-[var(--retro-border-active)] mr-0 sm:mr-6"
            >
              <MarkdownContent content={streamingContent} />
              <span className="inline-block w-2 h-4 bg-[var(--retro-accent-green)] ml-1 retro-animate-pulse"></span>
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && streamStatus.status && (
          <div className="flex items-center gap-3 mb-2">
            <div className="text-xs font-semibold text-[var(--retro-text-secondary)]">
              Assistant
            </div>
            <div className="flex items-center gap-2">
              {streamStatus.status !== 'error' && (
                <div className="w-2 h-2 bg-[var(--retro-accent-green)] rounded-full retro-animate-pulse"></div>
              )}
              <div className={`text-xs ${
                streamStatus.status === 'error' ? 'text-[var(--retro-accent-red)]' : 'text-[var(--retro-text-muted)]'
              }`}>
                {streamStatus.status === 'routing' && 'Selecting backend...'}
                {streamStatus.status === 'loading' && (
                  <span>
                    Warming up model...
                    {streamStatus.estimated_time && (
                      <span className="text-[var(--retro-text-muted)]"> (~{Math.round(streamStatus.estimated_time)}s)</span>
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
      <div className="border-t-2 border-[var(--retro-border)] p-3 sm:p-4 bg-[var(--retro-bg-medium)]">
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
            className="retro-input flex-1 text-sm resize-none min-h-[var(--retro-touch-target)]"
          />
          <RetroButton
            variant="primary"
            onClick={handleSendMessage}
            disabled={!input.trim() || isStreaming}
            loading={isStreaming}
            className="self-end"
          >
            {isStreaming ? '...' : '▸ Send'}
          </RetroButton>
        </div>
      </div>
      
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
