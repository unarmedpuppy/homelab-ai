import { useMemo, useState, useRef, useEffect } from 'react';
import type { AdminProvider, ProviderModel } from '../types/api';

interface ProviderModelSelectorProps {
  providers: AdminProvider[];
  isLoading: boolean;
  selectedProvider: string | null;
  selectedModel: string | null;
  onProviderChange: (providerId: string | null) => void;
  onModelChange: (modelId: string | null) => void;
  disabled?: boolean;
}

const getStatusIndicator = (provider: AdminProvider): string => {
  if (!provider.enabled) return '⚫';
  if (provider.health.is_healthy) return '🟢';
  if (provider.health.consecutive_failures < 3) return '🟡';
  return '🔴';
};

const formatConcurrency = (provider: AdminProvider): { text: string; color: string } => {
  const { current_requests, max_concurrent } = provider.load;
  const utilization = (current_requests / max_concurrent) * 100;
  
  if (current_requests === 0) {
    return { text: 'Available', color: 'text-green-400' };
  } else if (utilization < 50) {
    return { text: `${current_requests}/${max_concurrent} active`, color: 'text-green-400' };
  } else if (utilization < 80) {
    return { text: `${current_requests}/${max_concurrent} active`, color: 'text-yellow-400' };
  } else {
    return { text: `${current_requests}/${max_concurrent} busy`, color: 'text-red-400' };
  }
};

const formatContextWindow = (model: ProviderModel): string => {
  if (!model.context_window) return '';
  const k = Math.round(model.context_window / 1024);
  return `${k}K ctx`;
};

interface CustomDropdownProps {
  value: string | null;
  placeholder: string;
  options: Array<{
    value: string;
    label: string;
    disabled?: boolean;
    icon?: string;
    subtitle?: string;
    statusColor?: string;
  }>;
  onChange: (value: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

function CustomDropdown({ 
  value, 
  placeholder, 
  options, 
  onChange, 
  disabled = false, 
  isLoading = false 
}: CustomDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return;
      
      if (event.key === 'Escape') {
        setIsOpen(false);
        return;
      }

      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        const currentIndex = options.findIndex(opt => opt.value === value);
        const nextIndex = event.key === 'ArrowDown' 
          ? (currentIndex + 1) % options.length 
          : (currentIndex - 1 + options.length) % options.length;
        
        const nextOption = options[nextIndex];
        if (nextOption && !nextOption.disabled) {
          onChange(nextOption.value);
        }
      }

      if (event.key === 'Enter' && value) {
        event.preventDefault();
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, value, options, onChange]);

  const selectedOption = options.find(opt => opt.value === value);
  const displayText = selectedOption ? selectedOption.label : placeholder;

  return (
    <div ref={dropdownRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && !isLoading && setIsOpen(!isOpen)}
        disabled={disabled || isLoading}
        className={`
          flex items-center justify-between w-full px-3 py-2 text-sm
          bg-gray-800 border border-gray-700 rounded-lg
          text-white transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
          hover:border-gray-600 hover:bg-gray-750
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        `}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {selectedOption?.icon && <span className="text-sm">{selectedOption.icon}</span>}
          <span className="truncate">{displayText}</span>
          {selectedOption?.subtitle && (
            <span className={`text-xs ${selectedOption.statusColor || 'text-gray-400'} truncate`}>
              • {selectedOption.subtitle}
            </span>
          )}
        </div>
        <svg 
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-60 overflow-auto">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                if (!option.disabled) {
                  onChange(option.value);
                  setIsOpen(false);
                }
              }}
              disabled={option.disabled}
              className={`
                w-full px-3 py-2 text-left text-sm transition-colors duration-150
                flex items-center gap-2 hover:bg-gray-700
                ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${option.value === value ? 'bg-gray-700 text-blue-400' : 'text-white'}
              `}
            >
              {option.icon && <span className="text-sm">{option.icon}</span>}
              <div className="flex-1 min-w-0">
                <div className="truncate">{option.label}</div>
                {option.subtitle && (
                  <div className={`text-xs ${option.statusColor || 'text-gray-400'} truncate`}>
                    {option.subtitle}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProviderModelSelector({
  providers,
  isLoading,
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  disabled = false,
}: ProviderModelSelectorProps) {
  const availableModels = useMemo(() => {
    if (!selectedProvider) return [];
    const provider = providers.find(p => p.id === selectedProvider);
    return provider?.models || [];
  }, [providers, selectedProvider]);

  const currentProvider = useMemo(() => {
    if (!selectedProvider) return null;
    return providers.find(p => p.id === selectedProvider) || null;
  }, [providers, selectedProvider]);

  const sortedProviders = useMemo(() => {
    return [...providers].sort((a, b) => {
      if (a.enabled !== b.enabled) return a.enabled ? -1 : 1;
      if (a.health.is_healthy !== b.health.is_healthy) {
        return a.health.is_healthy ? -1 : 1;
      }
      return a.priority - b.priority;
    });
  }, [providers]);

  const handleProviderChange = (value: string) => {
    if (value === 'auto') {
      onProviderChange(null);
      onModelChange(null);
    } else {
      onProviderChange(value);
      const provider = providers.find(p => p.id === value);
      const defaultModel = provider?.models.find(m => m.is_default) || provider?.models[0];
      onModelChange(defaultModel?.id || null);
    }
  };

  const handleModelChange = (value: string) => {
    onModelChange(value || null);
  };

  const providerOptions = useMemo(() => {
  const options: Array<{
    value: string;
    label: string;
    disabled?: boolean;
    icon?: string;
    subtitle?: string;
    statusColor?: string;
  }> = [
    {
      value: 'auto',
      label: 'Auto (Intelligent Routing)',
      icon: '🤖',
      subtitle: 'Router selects optimal provider'
    }
  ];

  if (isLoading) {
    options.push({
      value: 'loading',
      label: 'Loading providers...',
      disabled: true
    });
  } else {
    sortedProviders.forEach(provider => {
      const concurrency = formatConcurrency(provider);
      const statusText = !provider.health.is_healthy ? 'offline' : concurrency.text;
      
      options.push({
        value: provider.id,
        label: provider.name,
        icon: getStatusIndicator(provider),
        subtitle: statusText,
        statusColor: concurrency.color,
        disabled: !provider.enabled || !provider.health.is_healthy
      });
    });
  }

  return options;
}, [sortedProviders, isLoading]);

const modelOptions = useMemo(() => {
  const options: Array<{
    value: string;
    label: string;
    disabled?: boolean;
    icon?: string;
    subtitle?: string;
    statusColor?: string;
  }> = [];

  if (availableModels.length === 0) {
    options.push({
      value: 'no-models',
      label: 'No models available',
      disabled: true
    });
  } else {
    availableModels.forEach(model => {
      const capabilities = [];
      if (model.is_default) capabilities.push('⭐ default');
      if (model.capabilities?.vision) capabilities.push('👁️ vision');
      const contextInfo = formatContextWindow(model);
      if (contextInfo) capabilities.push(contextInfo);
      
      options.push({
        value: model.id,
        label: model.name,
        subtitle: capabilities.length > 0 ? capabilities.join(' • ') : undefined
      });
    });
  }

  return options;
}, [availableModels]);

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 min-w-0">
        <label className="text-xs uppercase tracking-wider text-gray-500 whitespace-nowrap">
          Provider:
        </label>
        <CustomDropdown
          value={selectedProvider || 'auto'}
          placeholder="Select provider"
          options={providerOptions}
          onChange={handleProviderChange}
          disabled={disabled}
          isLoading={isLoading}
        />
      </div>

      {selectedProvider && currentProvider && (
        <div className="flex items-center gap-2 min-w-0">
          <label className="text-xs uppercase tracking-wider text-gray-500 whitespace-nowrap">
            Model:
          </label>
          <CustomDropdown
            value={selectedModel || ''}
            placeholder="Select model"
            options={modelOptions}
            onChange={handleModelChange}
            disabled={disabled || isLoading || availableModels.length === 0}
          />
        </div>
      )}

      {!selectedProvider && (
        <div className="text-xs text-gray-500 hidden md:block">
          Router will select optimal provider automatically
        </div>
      )}
    </div>
  );
}
