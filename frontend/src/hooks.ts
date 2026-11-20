// Нийтлэг React hook-ууд. Хариуцагч: Б1.
import { createContext, useCallback, useContext, useEffect, useState } from "react";

/** Өгөгдөл ачаалах: { data, error, loading, reload }. deps өөрчлөгдөхөд дахин ачаална. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const run = useCallback(fn, deps);

  const reload = useCallback(() => {
    setLoading(true);
    return run()
      .then((d) => { setData(d); setError(null); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [run]);

  useEffect(() => { void reload(); }, [reload]);
  return { data, error, loading, reload, setData };
}

/** Дээд мөрийн байршлын зам (breadcrumb). Хуудас бүр useCrumbs(["Миний хичээлүүд", "ӨС201"]) гэж дуудна. */
export const CrumbContext = createContext<(c: string[]) => void>(() => {});
export function useCrumbs(crumbs: string[]) {
  const set = useContext(CrumbContext);
  const key = crumbs.join("/");
  useEffect(() => set(crumbs), [key, set]);
}
