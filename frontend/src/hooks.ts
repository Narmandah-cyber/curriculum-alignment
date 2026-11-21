// Нийтлэг React hook-ууд. Хариуцагч: Б1.
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { ApiError } from "./api/client";

/** Өгөгдөл ачаалах: { data, error, status, loading, reload }. deps өөрчлөгдөхөд дахин ачаална.
 *  status — алдааны HTTP код (501 = backend-д хэрэгжээгүй endpoint). */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const run = useCallback(fn, deps);

  const reload = useCallback(() => {
    setLoading(true);
    return run()
      .then((d) => { setData(d); setError(null); setStatus(null); })
      .catch((e: Error) => { setError(e.message); setStatus(e instanceof ApiError ? e.status : null); })
      .finally(() => setLoading(false));
  }, [run]);

  useEffect(() => { void reload(); }, [reload]);
  return { data, error, status, loading, reload, setData };
}

/** Дээд мөрийн байршлын зам (breadcrumb). Хуудас бүр useCrumbs(["Миний хичээлүүд", "ӨС201"]) гэж дуудна. */
export const CrumbContext = createContext<(c: string[]) => void>(() => {});
export function useCrumbs(crumbs: string[]) {
  const set = useContext(CrumbContext);
  const key = crumbs.join("/");
  useEffect(() => set(crumbs), [key, set]);
}
