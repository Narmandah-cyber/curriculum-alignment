// Хөтөлбөрийн талын API (Б8-ийн дэлгэцүүд). Endpoint-ууд нь А3, А4, А5, А7, А9-ийнх (docs/API.md).
import { api } from "./client";
import type {
  AnalysisRun, BloomVerb, Cs2023Unit, MissingSkills, Plo, PloIn, Posting, PostingBatch, Program, ProgramMatrix, Role,
  Setting, User, UserIn,
} from "./types";

const json = (body: unknown) => JSON.stringify(body);

// Хөтөлбөр, PLO (UC6, А4)
export const listPrograms = () => api<Program[]>("/programs");
export const createProgram = (body: { name: string; major_code: string }) =>
  api<Program>("/programs", { method: "POST", body: json(body) });
export const listPlos = (programId: number) => api<Plo[]>(`/programs/${programId}/plos`);
export const addPlo = (programId: number, body: PloIn) =>
  api<Plo>(`/programs/${programId}/plos`, { method: "POST", body: json(body) });
export const attachCourse = (programId: number, courseId: number) =>
  api<unknown>(`/programs/${programId}/courses/${courseId}`, { method: "POST" });

// Ажлын зарлал (UC7, А7)
export const listBatches = (programId: number) => api<PostingBatch[]>(`/programs/${programId}/batches`);
export function importBatch(programId: number, name: string, file: File) {
  const form = new FormData();
  form.append("name", name);
  form.append("file", file);
  return api<PostingBatch>(`/programs/${programId}/batches`, { method: "POST", body: form });
}
export const listPostings = (batchId: number) => api<Posting[]>(`/batches/${batchId}/postings`);

// Хөтөлбөрийн шинжилгээ (UC8, А9)
export const runProgramAnalysis = (programId: number, batch_id: number, min_frequency?: number) =>
  api<AnalysisRun>(`/programs/${programId}/analysis`, { method: "POST", body: json({ batch_id, min_frequency }) });
export const getProgramMatrix = (programId: number, kind: "plo-cs2023" | "plo-course" = "plo-cs2023") =>
  api<ProgramMatrix>(`/programs/${programId}/matrix?kind=${kind}`);
export const getMissingSkills = (runId: number) => api<MissingSkills>(`/runs/${runId}/missing-skills`);

// Хэрэглэгч (UC10, А3)
export const listUsers = () => api<User[]>("/users");
export const createUser = (body: UserIn) => api<User>("/users", { method: "POST", body: json(body) });
export const updateUser = (id: number, body: Partial<Pick<User, "full_name" | "email" | "is_active">>) =>
  api<User>(`/users/${id}`, { method: "PATCH", body: json(body) });
export const grantRole = (id: number, role: Role) => api<unknown>(`/users/${id}/roles/${role}`, { method: "POST" });
export const revokeRole = (id: number, role: Role) => api<unknown>(`/users/${id}/roles/${role}`, { method: "DELETE" });

// Тохиргоо, жишиг өгөгдөл (UC11, А3, А5)
export const listSettings = () => api<Setting[]>("/settings");
export const setSetting = (key: string, value: string) =>
  api<Setting>(`/settings/${encodeURIComponent(key)}`, { method: "PUT", body: json({ value }) });
export const listBloomVerbs = () => api<BloomVerb[]>("/bloom-verbs");
export const addBloomVerb = (verb: string, level: number) =>
  api<BloomVerb>("/bloom-verbs", { method: "POST", body: json({ verb, level }) });
export const deleteBloomVerb = (id: number) => api<void>(`/bloom-verbs/${id}`, { method: "DELETE" });
export const listCs2023 = () => api<Cs2023Unit[]>("/cs2023");
