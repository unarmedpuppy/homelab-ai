import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { summaryAPI } from '../api/client';
import type { DailySummary } from '../types/api';

function formatDate(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
}

function formatTime(isoStr: string): string {
  return new Date(isoStr).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function Skeleton() {
  return (
    <div style={{ paddingTop: '0.5rem' }}>
      {[60, 30, 100, 85, 92, 70, 88].map((w, i) => (
        <div
          key={i}
          style={{
            height: i < 2 ? (i === 0 ? '1.5rem' : '1rem') : '0.875rem',
            width: `${w}%`,
            background: 'var(--clean-bg-hover)',
            borderRadius: 'var(--clean-radius-sm)',
            marginBottom: i === 0 ? '0.5rem' : i === 1 ? '2rem' : '0.625rem',
          }}
        />
      ))}
    </div>
  );
}

export default function SummaryPage() {
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    summaryAPI
      .getLatest()
      .then(setSummary)
      .catch((err) => {
        if (err?.response?.status === 404) {
          setSummary(null);
        } else {
          setError('Could not load summary.');
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Skeleton />;

  if (error) {
    return (
      <p style={{ color: 'var(--clean-text-muted)', textAlign: 'center', paddingTop: '3rem' }}>
        {error}
      </p>
    );
  }

  if (!summary) {
    return (
      <p style={{ color: 'var(--clean-text-muted)', textAlign: 'center', paddingTop: '3rem' }}>
        No summary posted yet today.
      </p>
    );
  }

  return (
    <>
      <div className="clean-page-header">
        <h1 className="clean-page-title">{formatDate(summary.date)}</h1>
        <p className="clean-page-subtitle">Updated at {formatTime(summary.updated_at)}</p>
      </div>
      <div className="clean-summary-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary.content}</ReactMarkdown>
      </div>
    </>
  );
}
