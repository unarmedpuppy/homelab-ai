'use client';

export default function LinkToGrafana() {
  const grafanaUrl = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3011';
  
  return (
    <a
      href={grafanaUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
    >
      <span className="mr-2">📊</span>
      View in Grafana
    </a>
  );
}

