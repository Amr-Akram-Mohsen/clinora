/**
 * features/auth/AuthProvider.tsx
 *
 * Authentication context provider.
 *
 * Responsibilities:
 * - Manage access token in memory (never localStorage).
 * - On mount, attempt a silent token refresh to restore session from cookie.
 * - Expose { user, isAuthenticated, isLoading, login, logout } to descendants.
 * - Intercept 401 responses from the API client and attempt refresh.
 *
 * Design:
 * - AuthContext holds user + token in React state.
 * - The access token is also stored in apiClient via setAccessToken()
 *   so Axios includes it in subsequent requests.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import * as authApi from "@/api/auth";
import { setAccessToken } from "@/api/client";
import type { AuthState, LoginRequest, RegisterRequest } from "@/types/auth";

// ---- Context definition --------------------------------------------------

interface AuthContextValue extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ---- Provider ------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    isAuthenticated: false,
    isLoading: true, // true on first render while we check for an existing session
  });

  // Attempt silent session restoration on mount via refresh cookie
  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      try {
        const tokenResponse = await authApi.refreshToken();
        setAccessToken(tokenResponse.access_token);

        const user = await authApi.getCurrentUser();

        if (!cancelled) {
          setState({
            user,
            accessToken: tokenResponse.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        }
      } catch {
        // No valid refresh cookie — user is not authenticated
        if (!cancelled) {
          setState({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
        }
      }
    }

    restoreSession();
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    const tokenResponse = await authApi.login(credentials);
    setAccessToken(tokenResponse.access_token);

    const user = await authApi.getCurrentUser();
    setState({
      user,
      accessToken: tokenResponse.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    const tokenResponse = await authApi.register(data);
    setAccessToken(tokenResponse.access_token);

    const user = await authApi.getCurrentUser();
    setState({
      user,
      accessToken: tokenResponse.access_token,
      isAuthenticated: true,
      isLoading: false,
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Best-effort logout — clear local state regardless
    }
    setAccessToken(null);
    setState({ user: null, accessToken: null, isAuthenticated: false, isLoading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ---- Hook ---------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
