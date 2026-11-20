// Хамрах хүрээ, түвшний зөрүү дэлгэцэд хичээл сонгох (?course=ID). Хариуцагч: Б7.
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { listCourses } from "../api/courses";
import type { Course } from "../api/types";
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

  useEffect(() => {
    if (!id && list.length) setParams((p) => { p.set("course", String(list[0].id)); return p; }, { replace: true });
  }, [id, list, setParams]);

  const select = (cid: number) => setParams((p) => { p.set("course", String(cid)); p.delete("link"); return p; });
  return { courses: list, course, loading: courses.loading, error: courses.error, select, params, reloadCourses: courses.reload };
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
