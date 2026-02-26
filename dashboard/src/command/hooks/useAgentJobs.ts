import { useQuery } from '@tanstack/react-query';
import { fetchJobs } from '../api/agentHarness';
import { Job } from '../types/game';

export function useAgentJobs() {
  return useQuery<Job[]>({
    queryKey: ['agent-jobs'],
    queryFn: () => fetchJobs(50),
    refetchInterval: 2000,
    staleTime: 1000,
  });
}

export function useActiveJobs() {
  const { data: jobs = [] } = useAgentJobs();
  return jobs.filter(j => j.status === 'running' || j.status === 'pending');
}
