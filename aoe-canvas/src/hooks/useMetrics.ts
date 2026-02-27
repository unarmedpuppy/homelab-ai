import { useQuery } from '@tanstack/react-query';
import { fetchRouterHealth, fetchRouterMetrics } from '../api/llmRouter';
import { fetchHarnessHealth } from '../api/agentHarness';

export function useHarnessHealth() {
  return useQuery({
    queryKey: ['harness-health'],
    queryFn: fetchHarnessHealth,
    refetchInterval: 10000,
    staleTime: 5000,
  });
}

export function useRouterHealth() {
  return useQuery({
    queryKey: ['router-health'],
    queryFn: fetchRouterHealth,
    refetchInterval: 10000,
    staleTime: 5000,
  });
}

export function useRouterMetrics() {
  return useQuery({
    queryKey: ['router-metrics'],
    queryFn: fetchRouterMetrics,
    refetchInterval: 30000,
    staleTime: 15000,
  });
}
