// Boundary: ХөтөлбөрийнШинжилгээДэлгэц (proto-07; UC8, ФШ-17, 18, 23). Хариуцагч: Б8
// Өгөгдөл: А9 (шинжилгээ, матриц, дутуу ур чадвар), А7 (зарлалын багц), А4 (PLO). Хэрэгжээгүй хэсэг Pending-ээр харагдана.
import { useEffect, useRef, useState } from "react";
import { getRun } from "../api/courses";
import { getMissingSkills, getProgramMatrix, listBatches, listPlos, runProgramAnalysis } from "../api/program";
import type { AnalysisRun } from "../api/types";
import { useAuth } from "../auth";
import { NewProgramModal, PloModal, ProgramPicker, useSelectedProgram } from "../components/ProgramPicker";
import { Alert, Button, Empty, LoadError, Loading, PageHeader, ProgressBar, StatCard } from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";


export default function ProgramAnalysisPage() {
  const { hasRole } = useAuth();
  const { programs, program, select, error, loading, reload } = useSelectedProgram();
  const pid = program?.id;
  const batches = useAsync(() => (pid ? listBatches(pid) : Promise.resolve([])), [pid]);
  const plos = useAsync(() => (pid ? listPlos(pid) : Promise.resolve([])), [pid]);
  const matrix = useAsync(() => (pid ? getProgramMatrix(pid, "plo-cs2023") : Promise.resolve(null)), [pid]);
  const runId = matrix.data?.run?.id;
  const missing = useAsync(() => (runId ? getMissingSkills(runId) : Promise.resolve(null)), [runId]);
  const [batchId, setBatchId] = useState<number | null>(null);
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [ploOpen, setPloOpen] = useState(false);
  const [newProgram, setNewProgram] = useState(false);
  const timer = useRef<number>();
  useCrumbs(["Хөтөлбөр", program?.name ?? "…"]);

  useEffect(() => { setBatchId(batches.data?.[0]?.id ?? null); }, [batches.data]);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  async function start() {
    if (!pid || !batchId) return;
    setMsg(null);
    try {
      const r = await runProgramAnalysis(pid, batchId);
      setRun(r);
      const tick = async () => {
        try {
          const cur = await getRun(r.id);
          setRun(cur);
          if (cur.status === "running") timer.current = window.setTimeout(tick, 1000);
          else { void matrix.reload(); }
        } catch { void matrix.reload(); setRun(null); }
      };
      timer.current = window.setTimeout(tick, 800);
    } catch (e) { setMsg((e as Error).message); }
  }

  if (error) return <Alert>{error}</Alert>;
  if (loading && !programs.length) return <Loading />;
  if (!program) {
    return (
      <>
        <PageHeader title="Хөтөлбөрийн шинжилгээ" actions={hasRole("coordinator", "admin") && <Button kind="primary" onClick={() => setNewProgram(true)}>+ Хөтөлбөр нэмэх</Button>} />
        <Empty>Хөтөлбөр бүртгэгдээгүй.</Empty>
        {newProgram && <NewProgramModal onClose={() => setNewProgram(false)} onCreated={(p) => { setNewProgram(false); void reload().then(() => select(p.id)); }} />}
      </>
    );
  }

  const m = matrix.data;
  const ms = missing.data;
  const maxCount = Math.max(1, ...(ms?.skills ?? []).map((s) => s.count));
  const ploText = new Map((plos.data ?? []).map((p) => [p.code, p.text]));

  return (
    <>
      <PageHeader title="Хөтөлбөрийн шинжилгээ" subtitle="PLO ↔ CS2023 мэдлэгийн чиглэл · PLO ↔ ажлын зарлалын ур чадвар"
        actions={<>
          <ProgramPicker programs={programs} program={program} onSelect={select} />
          <Button onClick={() => setPloOpen(true)}>PLO ({plos.data?.length ?? 0})</Button>
          {batches.data && batches.data.length > 0 && (
            <select style={{ width: "auto" }} aria-label="Зарлалын багц" value={batchId ?? ""} onChange={(e) => setBatchId(Number(e.target.value))}>
              {batches.data.map((b) => <option key={b.id} value={b.id}>Зарлалын багц: {b.name} ({b.posting_count})</option>)}
            </select>
          )}
          <Button kind="primary" onClick={start} disabled={!batchId || run?.status === "running"}>▶ Шинжилгээ ажиллуулах</Button>
        </>} />
      {msg && <div style={{ marginBottom: 14 }}><Alert>{msg}</Alert></div>}
      {batches.status === 501 && <div style={{ marginBottom: 14 }}><LoadError error={batches.error} status={501} task="А7" what="Зарлалын багцууд" /></div>}
      {batches.data && !batches.data.length && !batches.error && <div style={{ marginBottom: 14 }}><Alert tone="blue">Зарлалын багц алга. «Ажлын зарлал» цэсээр багц оруулна уу.</Alert></div>}
      {run?.status === "running" && <div style={{ marginBottom: 14 }}><ProgressBar value={run.progress} /></div>}

      <div className="grid-4">
        <StatCard label="Хамрагдсан CS2023 чиглэл" value={m ? `${m.covered_cols ?? new Set(m.cells.map((c) => c.col_id)).size} / ${m.cols.length}` : "—"} />
        <StatCard label="Ялгасан ур чадвар" value={ms?.extracted_skills ?? "—"} />
        <StatCard label="Зах зээлийн ур чадварын хамрах хүрээ" value={ms ? `${Math.round(ms.market_coverage * 100)}%` : "—"} tone="green" />
        <StatCard label="Хөтөлбөрт дутуу ур чадвар" value={ms?.skills.length ?? "—"} tone="orange" />
      </div>

      <div className="split" style={{ gridTemplateColumns: "minmax(0, 1fr) 440px" }}>
        <div className="card card-col">
          <h3>PLO × CS2023 мэдлэгийн чиглэл</h3>
          <LoadError error={matrix.error} status={matrix.status} task="А9" what="PLO × CS2023 матриц" />
          {matrix.loading && !m && !matrix.error && <Loading />}
          {m && (!m.rows.length || !m.cols.length ? <Empty>Шинжилгээ хийгдээгүй эсвэл PLO, CS2023 өгөгдөл алга.</Empty> : (
            <>
              <div className="matrix-wrap">
                <table className="heat">
                  <thead><tr><th />{m.cols.map((c) => <th key={c.id} className="muted" title={c.name}>{c.code}</th>)}</tr></thead>
                  <tbody>
                    {m.rows.map((r) => (
                      <tr key={r.id}>
                        <th className="row-h" title={r.name}>{r.code}</th>
                        {m.cols.map((c) => {
                          const x = m.cells.find((k) => k.row_id === r.id && k.col_id === c.id && k.status !== "rejected");
                          return <td key={c.id}><div className={`hc ${x?.strength ?? ""}`} title={x ? `${x.score.toFixed(2)}` : ""}>{x ? <span className={`dot ${x.strength}`} /> : "–"}</div></td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="muted small" style={{ display: "grid", gap: 4 }}>
                {m.rows.map((r) => <span key={r.id}>{r.code} — {r.name || ploText.get(r.code)}</span>)}
              </div>
              <span className="muted small row" style={{ gap: 6 }}><span className="dot direct legend-dot" /> Шууд · <span className="dot partial legend-dot" /> Хэсэгчлэн · – Холбоогүй</span>
            </>
          ))}
        </div>

        <div className="card card-col">
          <div className="card-head" style={{ margin: 0 }}><h3>Хөтөлбөрт дутуу ур чадвар</h3><span className="muted small">давтамжаар</span></div>
          {!runId && !matrix.error && <Empty>Шинжилгээ хийгдсэний дараа харагдана.</Empty>}
          {matrix.status === 501 && <Empty>Хөтөлбөрийн шинжилгээ (А9) хэрэгжсэний дараа харагдана.</Empty>}
          <LoadError error={missing.error} status={missing.status} task="А9" what="Дутуу ур чадвар" />
          {ms && (ms.skills.length ? ms.skills.map((s) => (
            <div key={s.skill} className="skill">
              <div className="row"><span style={{ fontWeight: 500, fontSize: 13 }}>{s.skill}</span><span className="spacer" /><span className="muted small">{s.count} зарлал</span></div>
              <div className="bar"><div style={{ width: `${(s.count / maxCount) * 100}%` }} /></div>
            </div>
          )) : <Empty>Дутуу ур чадвар илрээгүй.</Empty>)}
          {ms && <p className="muted small" style={{ margin: 0 }}>Доод хэмжээ: {Math.round(ms.min_frequency * ms.total_postings)} зарлал. Ямар ч PLO-той баталгаажсан холбоосгүй ур чадварууд.</p>}
        </div>
      </div>
      {ploOpen && <PloModal program={program} onClose={() => { setPloOpen(false); void plos.reload(); }} />}
    </>
  );
}
