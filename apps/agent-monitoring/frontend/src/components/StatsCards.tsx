'use client';

import { SystemStats } from '@/types';

interface StatsCardsProps {
  stats: SystemStats;
}

export default function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Total Agents',
      value: stats.totalAgents,
      color: 'bg-blue-500',
      icon: '👥',
    },
    {
      title: 'Active Agents',
      value: stats.activeAgents,
      color: 'bg-green-500',
      icon: '✅',
    },
    {
      title: 'Idle Agents',
      value: stats.idleAgents,
      color: 'bg-gray-500',
      icon: '😴',
    },
    {
      title: 'Blocked Agents',
      value: stats.blockedAgents,
      color: 'bg-red-500',
      icon: '🚫',
    },
    {
      title: 'Total Actions',
      value: stats.totalActions,
      color: 'bg-purple-500',
      icon: '⚡',
    },
    {
      title: 'Actions (24h)',
      value: stats.actionsLast24h,
      color: 'bg-orange-500',
      icon: '📊',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white rounded-lg shadow-md p-6 border-l-4"
          style={{ borderLeftColor: card.color }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">{card.title}</p>
              <p className="text-3xl font-bold text-gray-900">{card.value}</p>
            </div>
            <span className="text-4xl">{card.icon}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

