// Нэвтэрсэн хэрэглэгчийн контекст (ФШ-01, ФБШ-04). Хариуцагч: Б1.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { auth } from "./api/client";
import { me } from "./api/courses";
import type { Role, User } from "./api/types";

interface AuthState { user: User | null; loading: boolean; hasRole: (...r: Role[]) => boolean; logout: () => void; }

const Ctx = createContext<AuthState>({ user: null, loading: true, hasRole: () => false, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!auth.token) { setLoading(false); return; }
    me().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  const value: AuthState = {
    user,
    loading,
    hasRole: (...roles) => !!user && roles.some((r) => user.roles.includes(r)),
    logout: () => { auth.clear(); location.assign("/login"); },
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export const useAuth = () => useContext(Ctx);

export const ROLE_NAMES: Record<Role, string> = { teacher: "Багш", coordinator: "Хөтөлбөрийн хариуцагч", admin: "Админ" };
