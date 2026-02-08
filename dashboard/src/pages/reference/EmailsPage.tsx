import { useClipboard } from '../../hooks/useClipboard';

interface EmailRow {
  email: string;
  purpose: string;
}

const personalEmails: EmailRow[] = [
  { email: 'email@jenquist.com', purpose: 'Joshua + Abigail' },
  { email: 'joshua@jenquist.com', purpose: 'Joshua' },
  { email: 'abigail@jenquist.com', purpose: 'Abigail' },
  { email: 'ai@jenquist.com', purpose: 'Avery (AI assistant)' },
  { email: 'aijenquist@gmail.com', purpose: 'Avery (AI assistant)' },
];

const sharedEmails: EmailRow[] = [
  { email: 'home@jenquist.com', purpose: 'Home-related' },
  { email: 'orders@jenquist.com', purpose: 'Online orders & shipping' },
  { email: 'travel@jenquist.com', purpose: 'Travel bookings' },
  { email: 'health@jenquist.com', purpose: 'Health & medical' },
  { email: 'school@jenquist.com', purpose: 'School & education' },
  { email: 'subscriptions@jenquist.com', purpose: 'Subscriptions & memberships' },
  { email: 'maintenance@jenquist.com', purpose: 'Home maintenance' },
  { email: 'auto@jenquist.com', purpose: 'Vehicle-related' },
  { email: 'taxes@jenquist.com', purpose: 'Tax documents' },
  { email: 'legal@jenquist.com', purpose: 'Legal documents' },
  { email: 'realestate@jenquist.com', purpose: 'Real estate' },
  { email: 'donations@jenquist.com', purpose: 'Charitable donations' },
  { email: 'properties@jenquist.com', purpose: 'Property management' },
];

function CopyButton({ email, copiedId, onCopy }: { email: string; copiedId: string | null; onCopy: (text: string, id?: string) => void }) {
  const isCopied = copiedId === email;
  return (
    <button
      className={`clean-copy-btn ${isCopied ? 'clean-copy-btn--copied' : ''}`}
      onClick={() => onCopy(email, email)}
    >
      {isCopied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function EmailTable({ emails, copiedId, onCopy }: { emails: EmailRow[]; copiedId: string | null; onCopy: (text: string, id?: string) => void }) {
  return (
    <table className="clean-table">
      <thead>
        <tr>
          <th>Email</th>
          <th>Routes To</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {emails.map((row) => (
          <tr key={row.email}>
            <td style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.8125rem' }}>{row.email}</td>
            <td>{row.purpose}</td>
            <td style={{ textAlign: 'right' }}>
              <CopyButton email={row.email} copiedId={copiedId} onCopy={onCopy} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function EmailsPage() {
  const { copiedId, copy } = useClipboard();

  return (
    <>
      <div className="clean-page-header">
        <h1 className="clean-page-title">Email Addresses</h1>
        <p className="clean-page-subtitle">All @jenquist.com email aliases</p>
      </div>

      <div className="clean-section">
        <h2 className="clean-section-title">Personal</h2>
        <EmailTable emails={personalEmails} copiedId={copiedId} onCopy={copy} />
      </div>

      <div className="clean-section">
        <h2 className="clean-section-title">Shared Household</h2>
        <p style={{ fontSize: '0.875rem', color: 'var(--clean-text-secondary)', marginBottom: '1rem' }}>
          All shared emails route to Joshua, Abigail, and the AI inbox.
        </p>
        <EmailTable emails={sharedEmails} copiedId={copiedId} onCopy={copy} />
      </div>

      <div className="clean-section">
        <p style={{ fontSize: '0.875rem', color: 'var(--clean-text-muted)' }}>
          Catch-all: Any unrecognized @jenquist.com address goes to Joshua.
        </p>
      </div>
    </>
  );
}
