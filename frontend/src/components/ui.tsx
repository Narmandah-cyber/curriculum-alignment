// Figma-гийн компонентууд: Button (Type), Tag (Tone), Bloom level (Level 1–6)
import type { ButtonHTMLAttributes, ReactNode } from "react";

type BtnType = "primary" | "secondary" | "success" | "danger";
export function Button({ kind = "secondary", ...p }: { kind?: BtnType } & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={`btn ${kind === "secondary" ? "" : kind}`} {...p} />;
}

type Tone = "blue" | "green" | "yellow" | "red" | "neutral";
export function Tag({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`tag ${tone === "neutral" ? "" : tone}`}>{children}</span>;
}

// TODO(Б1): өнгийг Figma-гийн "Bloom level" компонентоос баталгаажуулах
const BLOOM_COLORS = ["#868e96", "#1c7ed6", "#0ca678", "#f59f00", "#e8590c", "#7048e8"];
export const BLOOM_NAMES = ["Санах", "Ойлгох", "Хэрэглэх", "Шинжлэх", "Үнэлэх", "Бүтээх"];
export function BloomLevel({ level }: { level: number }) {
  return <span className="bloom" title={BLOOM_NAMES[level - 1]} style={{ background: BLOOM_COLORS[level - 1] }}>{level}</span>;
}

export function Todo({ task, children }: { task: string; children?: ReactNode }) {
  return <div className="todo">Хэрэгжүүлэх: <b>{task}</b> {children}</div>;
}
