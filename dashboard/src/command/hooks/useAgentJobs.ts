import { useQuery } from "@tanstack/react-query";
import { fetchJobs } from "../api/agentHarness";
import type { Job } from "../types/game";

const ACTIVE_POLL_MS = 2000;   // poll fast when jobs are running
const IDLE_POLL_MS = 30000;    // poll slow when nothing is active

export function useAgentJobs() {
  return useQuery<Job[]>({
    queryKey: ["agent-jobs"],
    queryFn: () => fetchJobs(50),
    refetchInterval: (query) => {
      const jobs = (query.state.data as Job[]) ?? [];
      const hasActive = jobs.some(
        (j) => j.status === "running" || j.status === "pending"
      );
      return hasActive ? ACTIVE_POLL_MS : IDLE_POLL_MS;
    },
    staleTime: 1000,
  });
}

export function useActiveJobs() {
  const { data: jobs = [] } = useAgentJobs();
  return jobs.filter((j) => j.status === "running" || j.status === "pending");
}
