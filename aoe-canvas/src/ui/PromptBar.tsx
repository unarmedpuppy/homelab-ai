import { useState, useRef } from 'react';

interface PromptBarProps {
  onSubmit: (prompt: string, count: number) => void;
  disabled?: boolean;
}

export function PromptBar({ onSubmit, disabled }: PromptBarProps) {
  const [value, setValue] = useState('');
  const [villagerCount, setVillagerCount] = useState(1);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) return;
    onSubmit(value.trim(), villagerCount);
    setValue('');
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="absolute bottom-0 left-0 right-0 flex items-center gap-2 px-3 py-1.5"
      style={{
        background: 'rgba(26,18,8,0.98)',
        borderTop: '1px solid #6b5320',
        fontFamily: 'Courier New',
      }}
    >
      <span style={{ color: '#6b5320', fontSize: '12px' }}>&gt;</span>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        placeholder="Type a goal and press Enter to dispatch..."
        className="flex-1 bg-transparent outline-none"
        style={{
          color: '#d4c06a',
          fontSize: '12px',
          caretColor: '#c8a84b',
        }}
      />
      {/* Villager count selector */}
      <div className="flex items-center gap-1">
        <span style={{ color: '#888', fontSize: '10px' }}>V&times;</span>
        <select
          value={villagerCount}
          onChange={(e) => setVillagerCount(Number(e.target.value))}
          style={{
            background: 'rgba(42,31,10,0.9)',
            border: '1px solid #6b5320',
            color: '#c8a84b',
            fontSize: '10px',
            padding: '1px 4px',
            fontFamily: 'Courier New',
          }}
        >
          {[1, 2, 3, 5].map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        style={{
          background: value.trim() ? 'rgba(200,168,75,0.2)' : 'transparent',
          border: '1px solid #6b5320',
          color: value.trim() ? '#c8a84b' : '#444',
          fontSize: '10px',
          padding: '2px 8px',
          cursor: value.trim() ? 'pointer' : 'default',
          fontFamily: 'Courier New',
        }}
      >
        SEND
      </button>
    </form>
  );
}
