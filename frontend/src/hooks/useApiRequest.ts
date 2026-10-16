/**
 * hooks/useApiRequest.ts
 *
 * Generic hook for managing loading/error/data state for async API calls.
 *
 * Returns: { data, isLoading, error, execute }
 * - data: the resolved value on success
 * - isLoading: true while the request is in-flight
 * - error: ApiError if the request failed, null otherwise
 * - execute: function that triggers the request
 *
 * Usage:
 *   const { data: user, isLoading, error, execute: fetchUser } = useApiRequest(getCurrentUser);
 *   useEffect(() => { fetchUser(); }, [fetchUser]);
 */

import { useCallback, useState } from "react";
import type { ApiError } from "@/types/api";

interface ApiRequestState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
}

interface UseApiRequestResult<T, Args extends unknown[]> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
}

export function useApiRequest<T, Args extends unknown[]>(
  requestFn: (...args: Args) => Promise<T>
): UseApiRequestResult<T, Args> {
  const [state, setState] = useState<ApiRequestState<T>>({
    data: null,
    isLoading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: Args): Promise<T | null> => {
      setState({ data: null, isLoading: true, error: null });
      try {
        const data = await requestFn(...args);
        setState({ data, isLoading: false, error: null });
        return data;
      } catch (err) {
        const apiError = err as ApiError;
        setState({ data: null, isLoading: false, error: apiError });
        return null;
      }
    },
    [requestFn]
  );

  const reset = useCallback(() => {
    setState({ data: null, isLoading: false, error: null });
  }, []);

  return {
    data: state.data,
    isLoading: state.isLoading,
    error: state.error,
    execute,
    reset,
  };
}
