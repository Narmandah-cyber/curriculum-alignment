// Хичээлийн талын API (docs/API.md: courses, analysis, links). Хариуцагч: Б2, Б3, Б5, Б7.
import { api } from "./client";
import type {
  Clo, CloIn, Course, CourseIn, CourseRun, Gaps, ImportResult, Item, ItemIn, ManualLinkIn, Matrix, Method,
  Strength, User, Version, VersionCompare,
} from "./types";

const json = (body: unknown) => JSON.stringify(body);

export const me = () => api<User>("/auth/me");

// Хичээл
export const listCourses = (mine = true) => api<Course[]>(`/courses?mine=${mine}`);
export const getCourse = (id: number) => api<Course>(`/courses/${id}`);
export const createCourse = (body: CourseIn) => api<Course>("/courses", { method: "POST", body: json(body) });
export const updateCourse = (id: number, body: Partial<CourseIn>) =>
  api<Course>(`/courses/${id}`, { method: "PATCH", body: json(body) });
export const deleteCourse = (id: number) => api<void>(`/courses/${id}`, { method: "DELETE" });

// Хувилбар (UC12)
export const listVersions = (courseId: number) => api<Version[]>(`/courses/${courseId}/versions`);
export const renewCourse = (courseId: number, academic_year: string) =>
  api<Version>(`/courses/${courseId}/versions`, { method: "POST", body: json({ academic_year }) });
export const compareVersions = (v1: number, v2: number) => api<VersionCompare>(`/versions/compare?v1=${v1}&v2=${v2}`);

// CLO
export const listClos = (versionId: number) => api<Clo[]>(`/versions/${versionId}/clos`);
export const addClo = (versionId: number, body: CloIn) =>
  api<Clo>(`/versions/${versionId}/clos`, { method: "POST", body: json(body) });
export const updateClo = (id: number, body: Partial<CloIn>) =>
  api<Clo>(`/clos/${id}`, { method: "PATCH", body: json(body) });
export const deleteClo = (id: number) => api<void>(`/clos/${id}`, { method: "DELETE" });

// Сургалтын элемент
export const listItems = (versionId: number) => api<Item[]>(`/versions/${versionId}/items`);
export const addItem = (versionId: number, body: ItemIn) =>
  api<Item>(`/versions/${versionId}/items`, { method: "POST", body: json(body) });
export const updateItem = (id: number, body: Partial<ItemIn>) =>
  api<Item>(`/items/${id}`, { method: "PATCH", body: json(body) });
export const deleteItem = (id: number) => api<void>(`/items/${id}`, { method: "DELETE" });

// CSV импорт (ФШ-06)
export function importCsv(versionId: number, kind: "clo" | "item", file: File) {
  const form = new FormData();
  form.append("file", file);
  return api<ImportResult>(`/versions/${versionId}/import?kind=${kind}`, { method: "POST", body: form });
}

// Шинжилгээ (UC3, UC5)
export const runCourseAnalysis = (courseId: number, method: Method, llm: boolean) =>
  api<CourseRun>(`/courses/${courseId}/analysis`, { method: "POST", body: json({ method, llm }) });
export const getRun = (runId: number) => api<CourseRun>(`/runs/${runId}`);
export const getMatrix = (versionId: number) => api<Matrix>(`/versions/${versionId}/matrix`);
export const getGaps = (versionId: number) => api<Gaps>(`/versions/${versionId}/gaps`);

// Холбоос (UC4) — А10
export const confirmLink = (id: number) => api<unknown>(`/links/${id}/confirm`, { method: "POST" });
export const changeStrength = (id: number, strength: Strength) =>
  api<unknown>(`/links/${id}/strength`, { method: "POST", body: json({ strength }) });
export const rejectLink = (id: number) => api<unknown>(`/links/${id}/reject`, { method: "POST" });
export const createLink = (body: ManualLinkIn) => api<unknown>("/links", { method: "POST", body: json(body) });

// Тайлан (UC9) — А12
export const createReport = (runId: number, format: "pdf" | "csv") =>
  api<{ id: number }>(`/runs/${runId}/reports?format=${format}`, { method: "POST" });
