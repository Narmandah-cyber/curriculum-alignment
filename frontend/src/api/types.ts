// backend/app/schemas.py-тэй ижил байлгана. Схем өөрчлөгдвөл энд мөн засна.
export type Role = "teacher" | "coordinator" | "admin";
export interface User { id: number; full_name: string; email: string; is_active: boolean; roles: Role[]; }
export interface Program { id: number; name: string; major_code: string; coordinator_id: number | null; }
export interface Plo { id: number; program_id: number; code: string; text: string; bloom_level: number | null; }
export type LinkStatus = "proposed" | "confirmed" | "rejected";
export type LevelGap = "match" | "below" | "above";
export type Strength = "direct" | "partial";
export type Method = "rule" | "embedding" | "hybrid";
export type ItemType = "lecture" | "lab" | "assignment" | "exam";
export type LevelSource = "auto" | "manual";
export type RunStatus = "running" | "done" | "failed";

export interface AnalysisRun {
  id: number; scope: "course" | "program"; method: string; status: RunStatus; progress: number;
  started_at: string | null;
}

// --- Хичээл (Б2, Б3) ---
export interface Version {
  id: number; course_id: number; version_no: number; academic_year: string; status: "active" | "history";
  previous_version_id: number | null; created_at: string | null; clo_count: number; item_count: number;
}
export interface CourseSummary {
  analyzed: boolean; coverage: number; proposed: number; uncovered_clos: number; level_gaps: number;
}
export interface Course {
  id: number; code: string; name: string; credits: number; teacher_id: number | null;
  active_version: Version | null; summary: CourseSummary;
}
export interface CourseIn { code: string; name: string; credits: number; academic_year: string; }

export interface Clo {
  id: number; version_id: number; code: string; text: string;
  bloom_level: number | null; level_source: LevelSource | null; level_reason: string | null;
}
export interface CloIn { code: string; text: string; bloom_level?: number | null; }

export interface Item {
  id: number; version_id: number; type: ItemType; title: string; text: string; question_text: string | null;
  bloom_level: number | null; level_source: LevelSource | null; level_reason: string | null;
}
export interface ItemIn { type: ItemType; title: string; text: string; question_text?: string | null; bloom_level?: number | null; }

export interface ImportResult { imported: number; errors: { row: number; reason: string }[]; }

export interface VersionChange {
  change: "added" | "modified" | "removed"; kind: "clo" | "item"; key: string;
  old_text: string | null; new_text: string | null;
}
export interface VersionCompare {
  v1: Version; v2: Version; added: number; modified: number; removed: number; changes: VersionChange[];
}

// --- Шинжилгээ (Б5) ---
export interface CourseRun extends AnalysisRun {
  version_id: number | null; threshold: number; finished_at: string | null; notice: string | null;
}
export interface MatrixCell {
  link_id: number; clo_id: number; item_id: number; score: number; strength: Strength; status: LinkStatus;
  level_gap: LevelGap; method: Method; matched_terms: string[]; llm_explanation: string | null;
}
export interface Matrix {
  version: Version; clos: Clo[]; items: Item[]; cells: MatrixCell[]; run: CourseRun | null;
  proposed: number; confirmed: number;
}
export interface GapLink { link_id: number; clo: Clo; item: Item; level_gap: LevelGap; status: LinkStatus; score: number; }
export interface UncoveredClo extends Clo { has_proposed: boolean; }
export interface Gaps {
  match: number; below: number; above: number; unaligned: number;
  level_gaps: GapLink[]; uncovered_clos: UncoveredClo[]; unaligned_items: Item[];
}

// --- Холбоос (А10-ийн endpoint; оролтыг docs/API.md-д санал болгосон) ---
export interface ManualLinkIn {
  source_type: "clo" | "plo"; source_id: number; target_type: "item" | "plo" | "cs2023" | "skill";
  target_id: number; strength: Strength;
}

// --- CLO–PLO санал (ФШ-14) ---
export interface CloPloCell {
  link_id: number; clo_id: number; plo_id: number; score: number; strength: Strength; status: LinkStatus;
  level_gap: LevelGap; method: Method; matched_terms: string[];
}
export interface CloPlo {
  version: Version; programs: Program[]; plos: Plo[]; clos: Clo[]; cells: CloPloCell[]; proposed: number; confirmed: number;
}
