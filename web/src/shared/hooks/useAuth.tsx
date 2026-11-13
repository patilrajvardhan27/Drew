import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, type UserData } from "../api/client";

interface Auth {
  user: UserData | null;
  ready: boolean;
  signIn: (mode: "login" | "register", email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<Auth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserData | null>(null);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(
    () =>
      api
        .me()
        .then(setUser)
        .catch(() => setUser(null))
        .finally(() => setReady(true)),
    [],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signIn = useCallback(async (mode: "login" | "register", email: string, password: string) => {
    setUser(await (mode === "login" ? api.login : api.register)(email, password));
  }, []);

  const signOut = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, ready, signIn, signOut, refresh }), [user, ready, signIn, signOut, refresh]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): Auth {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("useAuth needs an AuthProvider");
  return auth;
}
