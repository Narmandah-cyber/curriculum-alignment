// Хөтөлбөр сонгох (?program=ID), хөтөлбөр үүсгэх, PLO удирдах цонх (UC6). Хариуцагч: Б8.
import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { listCourses } from "../api/courses";
import { addPlo, attachCourse, createProgram, listPlos, listPrograms } from "../api/program";
import type { Course, Program } from "../api/types";
import { useAsync } from "../hooks";
import { Alert, BloomLevel, Button, Empty, Field, LoadError, Modal } from "./ui";

export function useSelectedProgram() {
  const [params, setParams] = useSearchParams();
  const programs = useAsync(() => listPrograms(), []);
  const id = Number(params.get("program")) || null;
  const list = programs.data ?? [];
  const program = list.find((p) => p.id === id) ?? null;

  useEffect(() => {
    if (!id && list.length) setParams((p) => { p.set("program", String(list[0].id)); return p; }, { replace: true });
  }, [id, list, setParams]);

  const select = (pid: number) => setParams((p) => { p.set("program", String(pid)); return p; });
  return { programs: list, program, loading: programs.loading, error: programs.error, select, reload: programs.reload };
}

export function ProgramPicker({ programs, program, onSelect }:
  { programs: Program[]; program: Program | null; onSelect: (id: number) => void }) {
  if (programs.length <= 1) return null;
  return (
    <select style={{ width: "auto", minWidth: 240 }} aria-label="Хөтөлбөр" value={program?.id ?? ""}
      onChange={(e) => onSelect(Number(e.target.value))}>
      {programs.map((p) => <option key={p.id} value={p.id}>{p.name} ({p.major_code})</option>)}
    </select>
  );
}

export function NewProgramModal({ onClose, onCreated }: { onClose: () => void; onCreated: (p: Program) => void }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  async function submit(e: FormEvent) {
    e.preventDefault();
    try { onCreated(await createProgram({ name: name.trim(), major_code: code.trim() })); }
    catch (err) { setError((err as Error).message); }
  }
  return (
    <Modal title="Хөтөлбөр нэмэх" onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" type="submit" form="program-form">Хадгалах</Button></>}>
      <form id="program-form" onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <Field label="Хөтөлбөрийн нэр"><input required placeholder="Програм хангамжийн инженерчлэл" value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Field label="Мэргэжлийн индекс"><input required placeholder="D061301" value={code} onChange={(e) => setCode(e.target.value)} /></Field>
        {error && <Alert>{error}</Alert>}
      </form>
    </Modal>
  );
}

/** PLO жагсаах, нэмэх (UC6, ФШ-03) ба хичээл хамааруулах (А4 attach_course; ФШ-14-ийн нөхцөл). */
export function PloModal({ program, onClose }: { program: Program; onClose: () => void }) {
  const plos = useAsync(() => listPlos(program.id), [program.id]);
  const courses = useAsync(() => listCourses(false), []);
  const [code, setCode] = useState("");
  const [text, setText] = useState("");
  const [courseId, setCourseId] = useState<number | null>(null);
  const [msg, setMsg] = useState<{ tone: "red" | "green"; text: string } | null>(null);

  async function add(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      await addPlo(program.id, { code: code.trim(), text: text.trim() });
      setCode(""); setText("");
      await plos.reload();
    } catch (err) { setMsg({ tone: "red", text: (err as Error).message }); }
  }

  async function attach() {
    if (!courseId) return;
    setMsg(null);
    try {
      await attachCourse(program.id, courseId);
      setMsg({ tone: "green", text: "Хичээлийг хөтөлбөрт хамааруулав. Хичээлийн шинжилгээг дахин ажиллуулахад CLO–PLO санал гарна." });
    } catch (err) { setMsg({ tone: "red", text: (err as Error).message }); }
  }

  const list = plos.data ?? [];
  const cs: Course[] = courses.data ?? [];
  return (
    <Modal title={`${program.name} — PLO`} width={680} onClose={onClose}
      subtitle="Хөтөлбөрийн суралцахуйн үр дүн (UC6). PLO-г шинжилгээ ажиллуулахаас өмнө бүртгэнэ."
      footer={<Button onClick={onClose}>Хаах</Button>}>
      <LoadError error={plos.error} status={plos.status} task="А4" what="PLO жагсаалт" />
      {!list.length ? <Empty>PLO бүртгэгдээгүй.</Empty> : (
        <table>
          <thead><tr><th>Код</th><th>Текст</th><th>Блум</th></tr></thead>
          <tbody>{list.map((p) => (
            <tr key={p.id}><td className="nowrap"><b>{p.code}</b></td><td>{p.text}</td><td><BloomLevel level={p.bloom_level} /></td></tr>
          ))}</tbody>
        </table>
      )}
      <form onSubmit={add} className="row" style={{ alignItems: "flex-end" }}>
        <Field label="Код"><input required maxLength={10} placeholder="PLO5" value={code} onChange={(e) => setCode(e.target.value)} style={{ width: 100 }} /></Field>
        <div style={{ flex: 1 }}><Field label="Текст"><input required placeholder="Програм хангамжийн системийг зохиомжлох" value={text} onChange={(e) => setText(e.target.value)} /></Field></div>
        <Button type="submit">+ Нэмэх</Button>
      </form>
      <div className="field-label" style={{ marginTop: 8 }}>Хичээл хамааруулах</div>
      <div className="row">
        <select value={courseId ?? ""} onChange={(e) => setCourseId(Number(e.target.value) || null)}>
          <option value="">Хичээл сонгох…</option>
          {cs.map((c) => <option key={c.id} value={c.id}>{c.code} · {c.name}</option>)}
        </select>
        <Button onClick={attach} disabled={!courseId}>Хамааруулах</Button>
      </div>
      {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
    </Modal>
  );
}
