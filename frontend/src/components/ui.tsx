// Figma-гийн компонентууд: Button (Type), Tag (Tone), Bloom level (Level 1–6) ба нийтлэг бүрэлдэхүүн. Хариуцагч: Б1.
import { useEffect, type ButtonHTMLAttributes, type ReactNode } from "react";
import type { ItemType, LevelGap, LinkStatus, Strength } from "../api/types";

type BtnType = "primary" | "secondary" | "success" | "danger" | "ghost";
export function Button({ kind = "secondary", small, className = "", ...p }:
  { kind?: BtnType; small?: boolean } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`btn ${kind === "secondary" ? "" : kind} ${small ? "sm" : ""} ${className}`} {...p} />;
}

type Tone = "blue" | "green" | "yellow" | "red" | "neutral" | "purple";
export function Tag({ tone = "neutral", children, title }: { tone?: Tone; children: ReactNode; title?: string }) {
  return <span className={`tag ${tone === "neutral" ? "" : tone}`} title={title}>{children}</span>;
}

// Prototype-ийн «Bloom level» компонентын өнгө (proto-03-ийн доод тайлбар)
export const BLOOM_COLORS = ["#868e96", "#1c7ed6", "#0ca678", "#f59f00", "#e8590c", "#ae3ec9"];
export const BLOOM_NAMES = ["Санах", "Ойлгох", "Хэрэглэх", "Задлан шинжлэх", "Үнэлэх", "Бүтээх"];

export function BloomLevel({ level, title }: { level: number | null | undefined; title?: string }) {
  if (!level) return <span className="bloom empty" title="Тодорхойлоогүй">–</span>;
  return (
    <span className="bloom" title={title ?? `${level}. ${BLOOM_NAMES[level - 1]}`} style={{ background: BLOOM_COLORS[level - 1] }}>
      {level}
    </span>
  );
}

export function BloomLegend() {
  return (
    <div className="legend">
      <span>Блумын түвшин:</span>
      {BLOOM_NAMES.map((n, i) => (
        <span key={n} className="legend-item"><BloomLevel level={i + 1} /> {n}</span>
      ))}
    </div>
  );
}

export const ITEM_TYPE_NAMES: Record<ItemType, string> = {
  lecture: "Лекц", lab: "Лаборатори", assignment: "Бие даалт", exam: "Шалгалт",
};

export const GAP: Record<LevelGap, { label: string; tone: Tone }> = {
  match: { label: "Нийцсэн", tone: "green" },
  below: { label: "Доогуур", tone: "red" },
  above: { label: "Дээгүүр", tone: "blue" },
};
export const STRENGTH: Record<Strength, string> = { direct: "Шууд", partial: "Хэсэгчлэн" };
export const LINK_STATUS: Record<LinkStatus, { label: string; tone: Tone }> = {
  proposed: { label: "Санал", tone: "yellow" },
  confirmed: { label: "Баталгаажсан", tone: "green" },
  rejected: { label: "Татгалзсан", tone: "red" },
};

export function LevelSourceTag({ source, reason }: { source: string | null; reason?: string | null }) {
  if (!source) return <span className="muted">—</span>;
  return source === "manual"
    ? <Tag tone="blue" title={reason ?? undefined}>Гараар</Tag>
    : <Tag tone="green" title={reason ?? undefined}>Автомат</Tag>;
}

export function StatCard({ label, value, tone }: { label: string; value: ReactNode; tone?: "blue" | "red" | "yellow" | "green" }) {
  return (
    <div className="card stat">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${tone ?? ""}`}>{value}</div>
    </div>
  );
}

export function ProgressBar({ value }: { value: number }) {
  return <div className="progress"><div style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>;
}

export function Toggle({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label?: string }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label}
      className={`toggle ${checked ? "on" : ""}`} onClick={() => onChange(!checked)}>
      <span />
    </button>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p className="subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}

export function Modal({ title, subtitle, onClose, children, footer, width = 560 }:
  { title: string; subtitle?: ReactNode; onClose: () => void; children: ReactNode; footer?: ReactNode; width?: number }) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} style={{ width }}>
        <h2>{title}</h2>
        {subtitle && <p className="subtitle">{subtitle}</p>}
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: ReactNode }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

export function Alert({ tone = "red", children }: { tone?: "red" | "yellow" | "blue" | "green"; children: ReactNode }) {
  return <div className={`alert ${tone}`}>{children}</div>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Loading() {
  return <div className="empty">Ачаалж байна…</div>;
}

/** Огноо: 2026.11.02 (прототипийн формат) */
export function fmtDate(s: string | null | undefined) {
  if (!s) return "—";
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? "—" : `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export function Todo({ task, children }: { task: string; children?: ReactNode }) {
  return <div className="todo">Хэрэгжүүлэх: <b>{task}</b> {children}</div>;
}
