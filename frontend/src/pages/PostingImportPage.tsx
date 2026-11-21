// Boundary: ЗарлалОруулахДэлгэц (proto-08; UC7, ФШ-08, 15, ФБШ-05). Хариуцагч: Б8
// Файлыг илгээхээс өмнө браузерт урьдчилан шалгана (мөрийн тоо, алдаатай мөр). Хадгалах, ур чадвар ялгах нь А7.
import { useEffect, useState } from "react";
import { importBatch, listBatches, listPostings } from "../api/program";
import type { PostingBatch } from "../api/types";
import { useAuth } from "../auth";
import { NewProgramModal, ProgramPicker, useSelectedProgram } from "../components/ProgramPicker";
import { Alert, Button, Empty, Field, fmtDate, LoadError, Loading, PageHeader, Tag } from "../components/ui";
import { checkCsv } from "../csv";
import { useAsync, useCrumbs } from "../hooks";

const REQUIRED = ["title", "text"];
const STATUS = {
  processed: { label: "Боловсруулсан", tone: "green" as const },
  no_skills: { label: "Ур чадвар илрээгүй", tone: "yellow" as const },
  pending: { label: "Хүлээгдэж буй", tone: "neutral" as const },
};

function defaultName(d = new Date()) {
  return `${d.getFullYear()} Q${Math.floor(d.getMonth() / 3) + 1} — МТ салбар`;
}

export default function PostingImportPage() {
  const { hasRole } = useAuth();
  const { programs, program, select, error, loading, reload } = useSelectedProgram();
  const pid = program?.id;
  const batches = useAsync(() => (pid ? listBatches(pid) : Promise.resolve([] as PostingBatch[])), [pid]);
  const [batchId, setBatchId] = useState<number | null>(null);
  const postings = useAsync(() => (batchId ? listPostings(batchId) : Promise.resolve(null)), [batchId]);
  const [file, setFile] = useState<File | null>(null);
  const [check, setCheck] = useState<ReturnType<typeof checkCsv> | null>(null);
  const [name, setName] = useState(defaultName());
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ tone: "red" | "green" | "yellow"; text: string } | null>(null);
  const [newProgram, setNewProgram] = useState(false);
  useCrumbs(["Ажлын зарлал", "Багц оруулах"]);

  useEffect(() => { if (!batchId && batches.data?.length) setBatchId(batches.data[0].id); }, [batches.data, batchId]);

  async function pick(f: File | null) {
    setFile(f);
    setMsg(null);
    setCheck(f ? checkCsv(await f.text(), REQUIRED) : null);
  }

  async function upload() {
    if (!pid || !file) return;
    setBusy(true);
    setMsg(null);
    try {
      const b = await importBatch(pid, name.trim(), file);
      setMsg({ tone: b.errors?.length ? "yellow" : "green",
        text: `${b.posting_count} зарлал хадгалагдлаа${b.errors?.length ? `, ${b.errors.length} мөр алгассан` : ""}. Хувь хүний мэдээлэл арилгагдсан.` });
      await batches.reload();
      setBatchId(b.id);
      setFile(null);
      setCheck(null);
    } catch (e) { setMsg({ tone: "red", text: (e as Error).message }); }
    setBusy(false);
  }

  if (error) return <Alert>{error}</Alert>;
  if (loading && !programs.length) return <Loading />;
  if (!program) {
    return (
      <>
        <PageHeader title="Ажлын зарлалын багц оруулах" actions={hasRole("coordinator", "admin") && <Button kind="primary" onClick={() => setNewProgram(true)}>+ Хөтөлбөр нэмэх</Button>} />
        <Empty>Зарлалыг хөтөлбөрт хамааруулж оруулна. Эхлээд хөтөлбөр бүртгэнэ үү.</Empty>
        {newProgram && <NewProgramModal onClose={() => setNewProgram(false)} onCreated={(p) => { setNewProgram(false); void reload().then(() => select(p.id)); }} />}
      </>
    );
  }

  const list = postings.data ?? [];
  const batch = batches.data?.find((b) => b.id === batchId);
  const canUpload = !!file && !!check && !check.missing.length && check.rows > check.errors.length && !!name.trim();

  return (
    <>
      <PageHeader title="Ажлын зарлалын багц оруулах"
        subtitle="CSV баганууд: гарчиг, текст, огноо, эх сурвалж. Хувь хүний мэдээлэл автоматаар арилгагдана."
        actions={<ProgramPicker programs={programs} program={program} onSelect={select} />} />
      {msg && <div style={{ marginBottom: 14 }}><Alert tone={msg.tone}>{msg.text}</Alert></div>}

      <div className="split" style={{ gridTemplateColumns: "minmax(0, 1fr) 360px", marginBottom: 20 }}>
        <label className={`dropzone ${over ? "over" : ""}`} style={{ minHeight: 170, display: "grid", placeItems: "center", alignContent: "center", gap: 8 }}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); void pick(e.dataTransfer.files[0] ?? null); }}>
          <input type="file" accept=".csv,text/csv" hidden onChange={(e) => void pick(e.target.files?.[0] ?? null)} />
          <b style={{ color: "var(--text)", fontSize: 15 }}>CSV файлаа энд чирж оруулна уу</b>
          <span className="small">эсвэл</span>
          <span className="btn">Файл сонгох</span>
        </label>
        <div className="card card-col" style={{ gap: 10 }}>
          <Field label="Багцын нэр"><input value={name} onChange={(e) => setName(e.target.value)} /></Field>
          {file && check && (
            <span className="muted" style={{ fontSize: 13 }}>
              {file.name} · {check.rows} мөр{check.errors.length > 0 && ` · ${check.errors.length} мөр алдаатай`}
            </span>
          )}
          {check?.missing.length ? <Alert>Дутуу багана: {check.missing.join(", ")}. Заавал: title, text (нэмэлт: posted_date, source).</Alert> : null}
          {check && check.errors.length > 0 && (
            <details className="small"><summary>Алдаатай мөрүүд</summary>
              {check.errors.slice(0, 20).map((e) => <div key={e.row}>Мөр {e.row}: {e.reason}</div>)}
            </details>
          )}
          <Button kind="primary" disabled={!canUpload || busy} onClick={upload}>{busy ? "Боловсруулж байна…" : "Ур чадвар ялгах"}</Button>
          {!file && <span className="muted small">Загвар: data/samples/job_postings.csv</span>}
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Урьдчилан харах — ялгасан ур чадварууд</h3>
          <div className="row">
            {batches.data && batches.data.length > 1 && (
              <select style={{ width: "auto" }} aria-label="Багц" value={batchId ?? ""} onChange={(e) => setBatchId(Number(e.target.value))}>
                {batches.data.map((b) => <option key={b.id} value={b.id}>{b.name} · {fmtDate(b.created_at)}</option>)}
              </select>
            )}
            {batch && <span className="muted small">{list.length} / {batch.posting_count}</span>}
          </div>
        </div>
        <LoadError error={batches.error} status={batches.status} task="А7" what="Зарлалын багцууд" />
        <LoadError error={postings.error} status={postings.status} task="А7" what="Зарлал ба ур чадвар" />
        {batches.data && !batches.data.length && !batches.error && <Empty>Багц оруулаагүй байна.</Empty>}
        {list.length > 0 && (
          <table>
            <thead><tr><th style={{ width: 280 }}>Гарчиг</th><th style={{ width: 110 }}>Огноо</th><th>Ялгасан ур чадвар</th><th style={{ width: 140 }}>Төлөв</th></tr></thead>
            <tbody>
              {list.map((p) => (
                <tr key={p.id}>
                  <td><b>{p.title}</b></td>
                  <td>{p.posted_date ? fmtDate(p.posted_date) : "—"}</td>
                  <td><div className="chips">{p.skills?.length ? p.skills.map((s) => <Tag key={s} tone="blue">{s}</Tag>) : <span className="muted">—</span>}</div></td>
                  <td><Tag tone={STATUS[p.status]?.tone ?? "neutral"}>{STATUS[p.status]?.label ?? p.status}</Tag></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
