// Хичээлийн карт ба «Хичээл нэмэх» цонх (proto-02). Хариуцагч: Б6.
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { createCourse } from "../api/courses";
import type { Course } from "../api/types";
import { Alert, Button, Empty, Field, Modal, ProgressBar, Tag } from "./ui";

export function CourseCards({ courses }: { courses: Course[] }) {
  const nav = useNavigate();
  if (!courses.length) return <Empty>Хичээл бүртгэгдээгүй байна. «+ Хичээл нэмэх» товчоор эхлүүлнэ үү.</Empty>;
  return (
    <div className="grid-3">
      {courses.map((c) => {
        const s = c.summary;
        const pct = Math.round(s.coverage * 100);
        const v = c.active_version;
        return (
          <div key={c.id} className="card course-card">
            <div className="row">
              <Tag tone="blue">{c.code}</Tag>
              <span className="spacer" />
              {s.analyzed
                ? <Tag tone={pct >= 80 ? "green" : pct >= 50 ? "yellow" : "red"}>{pct}%</Tag>
                : <Tag>Шинжлээгүй</Tag>}
            </div>
            <h3>{c.name}</h3>
            <div className="muted small">
              {v ? `${v.clo_count} CLO · ${v.item_count} сургалтын элемент · ${v.academic_year}` : "Хувилбаргүй"}
            </div>
            <div className="muted small">Хамрах хүрээ</div>
            <ProgressBar value={s.analyzed ? pct : 0} />
            <div className="small muted">
              Түвшний зөрүү: <b style={{ color: "var(--yellow)" }}>{s.level_gaps}</b> ·
              Хамрагдаагүй CLO: <b style={{ color: "var(--red)" }}>{s.uncovered_clos}</b>
              {s.proposed > 0 && <> · Санал: <b style={{ color: "var(--primary)" }}>{s.proposed}</b></>}
            </div>
            <div><Button small onClick={() => nav(`/courses/${c.id}`)}>Нээх →</Button></div>
          </div>
        );
      })}
    </div>
  );
}

export function currentAcademicYear(d = new Date()) {
  const y = d.getMonth() >= 7 ? d.getFullYear() : d.getFullYear() - 1;   // 8-р сараас шинэ хичээлийн жил
  return `${y}-${y + 1}`;
}

export function AddCourseModal({ onClose, onCreated }: { onClose: () => void; onCreated: (c: Course) => void }) {
  const [form, setForm] = useState({ code: "", name: "", credits: 3, academic_year: currentAcademicYear() });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      onCreated(await createCourse(form));
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <Modal title="Хичээл нэмэх" subtitle="Анхны хувилбар (v1) идэвхтэй төлөвтэй үүснэ." onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" type="submit" form="course-form" disabled={busy}>Хадгалах</Button></>}>
      <form id="course-form" onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <div className="grid-2" style={{ gap: 12 }}>
          <Field label="Хичээлийн код"><input required maxLength={20} placeholder="ӨС201" value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value })} /></Field>
          <Field label="Кредит"><input type="number" min={1} max={10} required value={form.credits}
            onChange={(e) => setForm({ ...form, credits: Number(e.target.value) })} /></Field>
        </div>
        <Field label="Хичээлийн нэр"><input required maxLength={200} placeholder="Өгөгдлийн сан" value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
        <Field label="Хичээлийн жил" hint="Жишээ: 2026-2027"><input required pattern="\d{4}-\d{4}" value={form.academic_year}
          onChange={(e) => setForm({ ...form, academic_year: e.target.value })} /></Field>
        {error && <Alert>{error}</Alert>}
      </form>
    </Modal>
  );
}
