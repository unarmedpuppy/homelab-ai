import { useState } from 'react';
import { BuildingType, BUILDING_LABELS } from '../types/game';

interface BuildMenuProps {
  col: number;
  row: number;
  onPlace: (type: BuildingType, name: string) => void;
  onClose: () => void;
}

const BUILD_OPTIONS: Array<{ type: BuildingType; label: string; desc: string }> = [
  { type: 'barracks', label: 'Barracks', desc: 'Train and deploy agents' },
  { type: 'market', label: 'Market', desc: 'Resource and data ops' },
  { type: 'university', label: 'University', desc: 'Research and learning tasks' },
  { type: 'castle', label: 'Castle', desc: 'Critical infrastructure ops' },
];

export function BuildMenu({ col, row, onPlace, onClose }: BuildMenuProps) {
  const [name, setName] = useState('');
  const [selected, setSelected] = useState<BuildingType | null>(null);

  const handleBuild = () => {
    if (!selected) return;
    const finalName = name.trim() || selected;
    onPlace(selected, finalName);
    onClose();
  };

  return (
    <div
      className="absolute inset-0 flex items-center justify-center z-20"
      style={{ background: 'rgba(0,0,0,0.5)' }}
      onClick={onClose}
    >
      <div
        className="p-4 min-w-72"
        style={{
          background: '#1a1208',
          border: '2px solid #6b5320',
          fontFamily: 'Courier New',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-3">
          <span style={{ color: '#c8a84b', fontSize: '13px', fontWeight: 'bold' }}>
            BUILD AT [{col}, {row}]
          </span>
          <button
            onClick={onClose}
            style={{ color: '#888', cursor: 'pointer', background: 'none', border: 'none', fontSize: '14px' }}
          >
            &times;
          </button>
        </div>

        <div className="flex flex-col gap-1 mb-3">
          {BUILD_OPTIONS.map(opt => (
            <button
              key={opt.type}
              onClick={() => setSelected(opt.type)}
              style={{
                background: selected === opt.type ? 'rgba(200,168,75,0.2)' : 'rgba(42,31,10,0.6)',
                border: `1px solid ${selected === opt.type ? '#c8a84b' : '#6b5320'}`,
                color: selected === opt.type ? '#c8a84b' : '#d4c06a',
                padding: '6px 10px',
                cursor: 'pointer',
                textAlign: 'left',
                fontFamily: 'Courier New',
                fontSize: '11px',
              }}
            >
              <div style={{ fontWeight: 'bold' }}>[{BUILDING_LABELS[opt.type]}] {opt.label}</div>
              <div style={{ color: '#888', fontSize: '10px', marginTop: '2px' }}>{opt.desc}</div>
            </button>
          ))}
        </div>

        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name (optional)"
          style={{
            width: '100%',
            background: 'rgba(42,31,10,0.8)',
            border: '1px solid #6b5320',
            color: '#d4c06a',
            padding: '4px 8px',
            fontFamily: 'Courier New',
            fontSize: '11px',
            marginBottom: '8px',
            outline: 'none',
          }}
        />

        <div className="flex gap-2">
          <button
            onClick={handleBuild}
            disabled={!selected}
            style={{
              flex: 1,
              background: selected ? 'rgba(200,168,75,0.25)' : 'transparent',
              border: `1px solid ${selected ? '#c8a84b' : '#444'}`,
              color: selected ? '#c8a84b' : '#444',
              padding: '6px',
              cursor: selected ? 'pointer' : 'default',
              fontFamily: 'Courier New',
              fontSize: '11px',
            }}
          >
            BUILD
          </button>
          <button
            onClick={onClose}
            style={{
              flex: 1,
              background: 'transparent',
              border: '1px solid #6b5320',
              color: '#888',
              padding: '6px',
              cursor: 'pointer',
              fontFamily: 'Courier New',
              fontSize: '11px',
            }}
          >
            CANCEL
          </button>
        </div>
      </div>
    </div>
  );
}
