// Хамрах хүрээ, түвшний зөрүү дэлгэцэд хичээл ба хувилбар сонгох (?course=ID&version=ID). Хариуцагч: Б7.
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { listCourses, listVersions } from "../api/courses";
import type { Course, Version } from "../api/types";
import { useAuth } from "../auth";
import { useAsync } from "../hooks";

export function useSelectedCourse() {
  const [params, setParams] = useSearchParams();
  const { hasRole } = useAuth();
  const viewer = hasRole("coordinator", "admin");
  const courses = useAsync(() => listCourses(!viewer), [viewer]);
  const id = Number(params.get("course")) || null;
  const list = courses.data ?? [];
  const course = list.find((c) => c.id === id) ?? null;
  const versions = useAsync(() => (course ? listVersions(course.id) : Promise.resolve([] as Version[])), [course?.id]);

  useEffect(() => {
    if (!id && list.length) setParams((p) => { p.set("course", String(list[0].id)); return p; }, { replace: true });
  }, [id, list, setParams]);

  // ?version=ID байхгүй бол идэвхтэй хувилбар (ФШ-07: түүх хувилбарыг мөн харж болно)
  const vParam = Number(params.get("version")) || null;
  const version = (versions.data ?? []).find((v) => v.id === vParam) ?? course?.active_version ?? null;

  const select = (cid: number) =>
    setParams((p) => { p.set("course", String(cid)); p.delete("link"); p.delete("version"); return p; });
  const selectVersion = (vid: number) =>
    setParams((p) => {
      if (vid === course?.active_version?.id) p.delete("version"); else p.set("version", String(vid));
      p.delete("link");
      return p;
    });
  return {
    courses: list, course, loading: courses.loading, error: courses.error, select, params,
    versions: versions.data ?? [], version, selectVersion, reloadCourses: courses.reload,
  };
}

export function CoursePicker({ courses, course, onSelect }:
  { courses: Course[]; course: Course | null; onSelect: (id: number) => void }) {
  if (courses.length <= 1) return null;
  return (
    <select style={{ width: "auto", minWidth: 220 }} value={course?.id ?? ""} onChange={(e) => onSelect(Number(e.target.value))}>
      {courses.map((c) => <option key={c.id} value={c.id}>{c.code} · {c.name}</option>)}
    </select>
  );
}

/** Хувилбар сонгогч (ФШ-07). Нэг л хувилбартай бол харагдахгүй. */
export function VersionPicker({ versions, version, onSelect }:
  { versions: Version[]; version: Version | null; onSelect: (id: number) => void }) {
  if (versions.length <= 1) return null;
  return (
    <select style={{ width: "auto" }} aria-label="Хувилбар" value={version?.id ?? ""} onChange={(e) => onSelect(Number(e.target.value))}>
      {versions.map((v) => (
        <option key={v.id} value={v.id}>v{v.version_no} · {v.academic_year}{v.status === "active" ? " (идэвхтэй)" : " (түүх)"}</option>
      ))}
    </select>
  );
}

/** Түүх хувилбар харж байгааг сануулах мөр. */
export function HistoryBanner({ version, onActive }: { version: Version | null; onActive: () => void }) {
  if (!version || version.status === "active") return null;
  return (
    <div className="alert yellow" style={{ marginBottom: 16, display: "flex", gap: 12, alignItems: "center" }}>
      <span style={{ flex: 1 }}>🔒 v{version.version_no} ({version.academic_year}) — <b>түүх хувилбар</b>. Зөвхөн харах горим, засах боломжгүй.</span>
      <button className="btn sm" onClick={onActive}>Идэвхтэй хувилбар руу</button>
    </div>
  );
}
