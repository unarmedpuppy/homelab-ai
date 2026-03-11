import { useState } from 'react';
import type { TraceSession } from '../types/traces';
import { SessionsList, SessionDetail } from '../components/sessions';

export function SessionsPage() {
  const [selectedSession, setSelectedSession] = useState<TraceSession | null>(null);

  if (selectedSession) {
    return (
      <SessionDetail
        session={selectedSession}
        onClose={() => setSelectedSession(null)}
      />
    );
  }

  return <SessionsList onSelect={setSelectedSession} />;
}

export default SessionsPage;
