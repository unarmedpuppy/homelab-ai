interface AgePanelProps {
  visible: boolean;
  onClose: () => void;
}

export function AgePanel({ visible, onClose }: AgePanelProps) {
  if (!visible) return null;
  return (
    <div
      className="absolute top-10 right-4 w-48 z-10 p-3"
      style={{ background: '#1a1208', border: '2px solid #6b5320', fontFamily: 'Courier New' }}
    >
      <div className="flex justify-between items-center mb-2">
        <span style={{ color: '#c8a84b', fontSize: '12px', fontWeight: 'bold' }}>AGE ADVANCEMENT</span>
        <button onClick={onClose} style={{ color: '#888', background: 'none', border: 'none', cursor: 'pointer' }}>&times;</button>
      </div>
      {['Dark Age', 'Feudal Age', 'Castle Age', 'Imperial Age'].map((age, i) => (
        <div
          key={age}
          className="flex items-center gap-2 py-1"
          style={{
            borderBottom: '1px solid #3a2a10',
            color: i === 3 ? '#c8a84b' : '#555',
            fontSize: '11px',
          }}
        >
          <span>{i === 3 ? '\u25cf' : '\u25cb'}</span>
          <span>{age}</span>
          {i === 3 && <span style={{ marginLeft: 'auto', color: '#888', fontSize: '9px' }}>CURRENT</span>}
        </div>
      ))}
      <div style={{ color: '#666', fontSize: '9px', marginTop: '8px' }}>
        Age advancement unlocks richer orchestration modes.
      </div>
    </div>
  );
}
