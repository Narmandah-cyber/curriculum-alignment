// backend/app/schemas.py-тэй ижил байлгана. Схем өөрчлөгдвөл энд мөн засна.
export type Role = "teacher" | "coordinator" | "admin";
export interface User { id: number; full_name: string; email: string; is_active: boolean; roles: Role[]; }
export interface Program { id: number; name: string; major_code: string; coordinator_id: number | null; }
export interface Plo { id: number; program_id: number; code: string; text: string; bloom_level: number | null; }
export type LinkStatus = "proposed" | "confirmed" | "rejected";
export type LevelGap = "match" | "below" | "above";
export interface AnalysisRun { id: number; scope: "course" | "program"; method: string; status: string; progress: number; }
