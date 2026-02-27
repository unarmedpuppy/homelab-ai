import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchMapState, saveMapState } from '../api/agentHarness';
import type { MapState } from '../types/game';

export function useMapState() {
  return useQuery<MapState | null>({
    queryKey: ['map-state'],
    queryFn: fetchMapState,
    staleTime: 60000,
  });
}

export function useSaveMapState() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (state: MapState) => saveMapState(state),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['map-state'] }),
  });
}
