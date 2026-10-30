import { createContext, useContext, useEffect, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Me } from "./types";

/** The signed-in BMS user. Sign-in itself happens on the BMS login page, not here. */
type AuthState = {
  me: Me | null;
  loading: boolean;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const query = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const me = await api<Me | { user: null }>("/auth/me/");
      return me.user ? (me as Me) : null;
    },
    staleTime: 60_000,
    retry: false,
  });

  const value: AuthState = { me: query.data ?? null, loading: query.isLoading };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

function goToLogin() {
  const next = window.location.pathname + window.location.search;
  window.location.assign(`/login/?next=${encodeURIComponent(next)}`);
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { me, loading } = useAuth();
  const signedOut = !loading && !me;
  useEffect(() => {
    if (signedOut) goToLogin();
  }, [signedOut]);
  if (!me) return <div className="center-screen"><div className="spinner" /></div>;
  return <>{children}</>;
}
