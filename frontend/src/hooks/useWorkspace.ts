import { useCallback, useEffect, useState } from 'react';
import { DEMO_PATIENT_ID, fetchWorkspace, type WorkspacePayload } from '../lib/api';

export function useWorkspace(patientId: number = DEMO_PATIENT_ID) {
  const [workspace, setWorkspace] = useState<WorkspacePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await fetchWorkspace(patientId);
      setWorkspace(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workspace.');
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { workspace, loading, error, refresh, patientId };
}
