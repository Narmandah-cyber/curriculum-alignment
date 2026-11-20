// Boundary: ШинжилгээЦонх (proto-04; UC3, ФШ-10, 26, ФБШ-02, 06). Хариуцагч: Б6
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { getMatrix, getRun, runCourseAnalysis } from "../api/courses";
import type { Course, CourseRun, Method } from "../api/types";
import { Alert, Button, Modal, ProgressBar, Tag, Toggle } from "../components/ui";

const METHODS: { id: Method; name: string; desc: string; recommended?: boolean }[] = [
  { id: "rule", name: "Дүрэмд суурилсан", desc: "Түлхүүр үг, Блумын үйл үгийн толь. Хурдан, тайлбарлахад хялбар." },
  { id: "embedding", name: "Embedding", desc: "Олон хэлт загвараар утгын ижил төстэй байдлыг тооцно." },
  { id: "hybrid", name: "Хосолсон", desc: "Дүрэм ба embedding-ийн оноог нэгтгэнэ.", recommended: true },
];

/** Явцыг асуух: GET /runs/{id} (А11); хэрэгжээгүй (501) бол матрицын сүүлийн шинжилгээгээр. */
async function poll(run: CourseRun, versionId: number): Promise<CourseRun> {
  try {
    return await getRun(run.id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 501) {
      const m = await getMatrix(versionId);
      return m.run && m.run.id === run.id ? m.run : run;
    }
    throw e;
  }
}

export default function AnalysisDialog({ course, onClose, onDone }:
  { course: Course; onClose: () => void; onDone?: () => void }) {
  const nav = useNavigate();
  const v = course.active_version;
  const [method, setMethod] = useState<Method>("hybrid");
  const [llm, setLlm] = useState(false);
  const [run, setRun] = useState<CourseRun | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number>();

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const pairs = (v?.clo_count ?? 0) * (v?.item_count ?? 0);
  const running = run?.status === "running";

  async function start() {
    if (!v) return;
    setError(null);
    try {
      const r = await runCourseAnalysis(course.id, method, llm);
      setRun(r);
      setNotice(r.notice);
      const tick = async () => {
        try {
          const cur = await poll(r, v.id);
          setRun(cur);
          if (cur.status === "running") timer.current = window.setTimeout(tick, 800);
          else if (cur.status === "done") {
            onDone?.();
            if (cur.method !== method) setNotice("Embedding загвар бэлэн биш тул дүрэмд суурилсан аргаар шинжлэв.");
            else timer.current = window.setTimeout(() => nav(`/matrix?course=${course.id}`), 600);
          } else setError("Шинжилгээ амжилтгүй боллоо. Өгөгдлөө шалгаад дахин оролдоно уу.");
        } catch (e) { setError((e as Error).message); }
      };
      timer.current = window.setTimeout(tick, 400);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <Modal title="Шинжилгээ ажиллуулах" width={560} onClose={onClose}
      subtitle={`${v?.clo_count ?? 0} CLO × ${v?.item_count ?? 0} сургалтын элемент = ${pairs} хос шинжлэгдэнэ`}
      footer={<>
        <Button onClick={onClose}>{run?.status === "done" ? "Хаах" : "Цуцлах"}</Button>
        {run?.status === "done"
          ? <Button kind="primary" onClick={() => nav(`/matrix?course=${course.id}`)}>Матриц харах →</Button>
          : <Button kind="primary" onClick={start} disabled={running || pairs === 0}>Эхлүүлэх</Button>}
      </>}>
      <div className="field-label">Шинжилгээний арга</div>
      {METHODS.map((m) => (
        <label key={m.id} className={`option ${method === m.id ? "selected" : ""}`}>
          <input type="radio" name="method" checked={method === m.id} disabled={running} onChange={() => setMethod(m.id)} />
          <span><b>{m.name} {m.recommended && <Tag tone="blue">Санал болгох</Tag>}</b><span className="muted small">{m.desc}</span></span>
        </label>
      ))}
      <div className="option" style={{ cursor: "default", alignItems: "center" }}>
        <span style={{ flex: 1 }}><b>LLM тайлбар нэмэх</b><span className="muted small">Сонголттой. Интернэт байхгүй үед алгасна.</span></span>
        <Toggle checked={llm} onChange={setLlm} label="LLM тайлбар" />
      </div>
      {pairs === 0 && <Alert tone="yellow">Дор хаяж нэг CLO болон нэг сургалтын элемент бүртгэнэ үү.</Alert>}
      {run && (
        <div style={{ display: "grid", gap: 8 }}>
          <span className="muted small">
            Явц: {Math.round((run.progress / 100) * pairs)} / {pairs} хос
            {run.status === "done" && " — дууслаа"}
          </span>
          <ProgressBar value={run.progress} />
        </div>
      )}
      {notice && <Alert tone="yellow">{notice}</Alert>}
      {error && <Alert>{error}</Alert>}
    </Modal>
  );
}
