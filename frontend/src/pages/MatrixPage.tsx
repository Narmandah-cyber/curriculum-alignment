// Boundary: МатрицДэлгэц (proto-05; UC4, UC5, ФШ-14, 19, 22, 24). Хариуцагч: Б7
// Хоёр харагдац: CLO × сургалтын элемент (ФШ-22), CLO × PLO (ФШ-14). ?version=ID — түүх хувилбар (ФШ-07).
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { confirmLink, createLink, createReport, getCloPlo, getMatrix, rejectLink } from "../api/courses";
import type { Clo, LevelGap, LinkStatus, Method, Strength } from "../api/types";
import { CoursePicker, HistoryBanner, useSelectedCourse, VersionPicker } from "../components/CoursePicker";
import { StrengthModal } from "../components/LinkModals";
import {
  Alert, BloomLevel, Button, Empty, fmtDate, GAP, ITEM_TYPE_NAMES, LINK_STATUS, Loading, Modal, PageHeader, STRENGTH, Tag,
} from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

const METHOD_NAMES: Record<string, string> = { rule: "Дүрэмд суурилсан", embedding: "Embedding", hybrid: "Хосолсон" };
type Filter = "all" | "proposed" | "confirmed";
type View = "item" | "plo";

/** Матрицын багана (сургалтын элемент эсвэл PLO)-г нэг хэлбэрт оруулна. */
interface Col { id: number; title: string; kind: string; text: string; bloom_level: number | null; }
interface Cell {
  link_id: number; clo_id: number; col_id: number; score: number; strength: Strength; status: LinkStatus;
  level_gap: LevelGap; method: Method; matched_terms: string[]; llm_explanation?: string | null;
}
interface Data { clos: Clo[]; cols: Col[]; cells: Cell[]; proposed: number; confirmed: number; note?: string; }

const fmtScore = (s: number) => s.toFixed(2).replace(/^0/, "");

export default function MatrixPage() {
  const { courses, course, select, params, error: cErr, loading: cLoading, versions, version, selectVersion } = useSelectedCourse();
  const vid = version?.id;
  const [view, setView] = useState<View>("item");
  const m = useAsync(() => (vid ? getMatrix(vid) : Promise.resolve(null)), [vid]);
  const cp = useAsync(() => (vid && view === "plo" ? getCloPlo(vid) : Promise.resolve(null)), [vid, view]);
  const [selected, setSelected] = useState<{ clo: number; col: number } | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [adding, setAdding] = useState<{ clo: Clo; col: Col } | null>(null);
  const [strengthFor, setStrengthFor] = useState<Cell | null>(null);
  const [msg, setMsg] = useState<{ tone: "red" | "green" | "yellow"; text: string } | null>(null);
  useCrumbs(["Хамрах хүрээ", course ? `${course.code} ${course.name}` : "…"]);

  const run = m.data?.run;
  const readOnly = version?.status !== "active";

  const data: Data | null = useMemo(() => {
    if (view === "item") {
      if (!m.data) return null;
      return {
        clos: m.data.clos,
        cols: m.data.items.map((i) => ({ id: i.id, title: i.title, kind: ITEM_TYPE_NAMES[i.type],
          text: [i.text, i.question_text].filter(Boolean).join(" — "), bloom_level: i.bloom_level })),
        cells: m.data.cells.map((c) => ({ ...c, col_id: c.item_id })),
        proposed: m.data.proposed, confirmed: m.data.confirmed,
      };
    }
    if (!cp.data) return null;
    const progs = new Map(cp.data.programs.map((p) => [p.id, p.name]));
    return {
      clos: cp.data.clos,
      cols: cp.data.plos.map((p) => ({ id: p.id, title: p.code, kind: progs.get(p.program_id) ?? "PLO",
        text: p.text, bloom_level: p.bloom_level })),
      cells: cp.data.cells.map((c) => ({ ...c, col_id: c.plo_id })),
      proposed: cp.data.proposed, confirmed: cp.data.confirmed,
      note: cp.data.programs.length ? undefined
        : "Энэ хичээл ямар ч хөтөлбөрт хамааруулагдаагүй тул PLO-той харьцуулах боломжгүй. Хөтөлбөрийн хариуцагч хичээлийг хөтөлбөрт хамааруулна (UC6).",
    };
  }, [view, m.data, cp.data]);

  const cellMap = useMemo(() => {
    const map = new Map<string, Cell>();
    data?.cells.forEach((c) => map.set(`${c.clo_id}:${c.col_id}`, c));
    return map;
  }, [data]);

  // ?link=ID — түвшний зөрүү дэлгэцийн «Харах» товчоос (элементийн харагдац)
  const linkParam = Number(params.get("link")) || null;
  const fromLink = linkParam && view === "item" ? data?.cells.find((c) => c.link_id === linkParam) : undefined;
  const sel = selected ?? (fromLink ? { clo: fromLink.clo_id, col: fromLink.col_id } : null);
  const cell = sel ? cellMap.get(`${sel.clo}:${sel.col}`) : undefined;
  const selClo = data?.clos.find((c) => c.id === sel?.clo);
  const selCol = data?.cols.find((c) => c.id === sel?.col);

  const reload = async () => { await m.reload(); if (view === "plo") await cp.reload(); };

  async function act(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await fn();
      setMsg({ tone: "green", text: ok });
      await reload();
    } catch (e) {
      setMsg({ tone: "red", text: (e as Error).message });
    }
  }

  if (cErr) return <Alert>{cErr}</Alert>;
  if (cLoading && !courses.length) return <Loading />;
  if (!course) return <Empty>Хичээл алга. <Link to="/courses">Хичээл нэмэх</Link></Empty>;

  const visible = (c?: Cell) => !!c && (filter === "all" || c.status === filter);
  const colLabel = view === "item" ? "сургалтын элемент" : "PLO";

  return (
    <>
      <PageHeader title="Хамрах хүрээний матриц"
        subtitle={run ? <>{METHOD_NAMES[run.method] ?? run.method} арга · {fmtDate(run.started_at)} · {data?.proposed ?? 0} санал, {data?.confirmed ?? 0} баталгаажсан</> : `${course.code} · ${course.name}`}
        actions={<>
          <CoursePicker courses={courses} course={course} onSelect={(id) => { setSelected(null); select(id); }} />
          <VersionPicker versions={versions} version={version} onSelect={(id) => { setSelected(null); selectVersion(id); }} />
          <select style={{ width: "auto" }} value={filter} onChange={(e) => setFilter(e.target.value as Filter)} aria-label="Шүүлтүүр">
            <option value="all">Бүх холбоос</option>
            <option value="proposed">Зөвхөн санал</option>
            <option value="confirmed">Зөвхөн баталгаажсан</option>
          </select>
          <Button onClick={() => run && act(() => createReport(run.id, "csv"), "Тайлан үүслээ.")} disabled={!run}>⤓ Тайлан</Button>
        </>} />
      <HistoryBanner version={version} onActive={() => course.active_version && selectVersion(course.active_version.id)} />
      <div className="tabs" role="tablist">
        {(["item", "plo"] as View[]).map((v) => (
          <button key={v} role="tab" aria-selected={view === v} className={view === v ? "active" : ""}
            onClick={() => { setView(v); setSelected(null); }}>
            {v === "item" ? "CLO × сургалтын элемент" : "CLO × PLO"}
          </button>
        ))}
      </div>
      {msg && <div style={{ marginBottom: 14 }}><Alert tone={msg.tone}>{msg.text}</Alert></div>}
      {(m.error || cp.error) && <Alert>{m.error || cp.error}</Alert>}
      {!data ? <Loading /> : data.note ? <Alert tone="blue">{data.note}</Alert> : !data.clos.length || !data.cols.length ? (
        <Empty>CLO эсвэл {colLabel} бүртгэгдээгүй. <Link to={`/courses/${course.id}`}>Хичээлийн өгөгдөл</Link></Empty>
      ) : (
        <div className="split">
          <div className="card">
            {!run && <div style={{ marginBottom: 14 }}><Alert tone="blue">Шинжилгээ хийгдээгүй байна.{!readOnly && <> <Link to={`/courses/${course.id}/analysis`}>Шинжилгээ ажиллуулах</Link></>}</Alert></div>}
            {run?.status === "running" && <div style={{ marginBottom: 14 }}><Alert tone="yellow">Шинжилгээ явагдаж байна ({run.progress}%)… <button className="link-btn" onClick={() => void reload()}>Шинэчлэх</button></Alert></div>}
            {run?.status === "failed" && <div style={{ marginBottom: 14 }}><Alert>Сүүлийн шинжилгээ амжилтгүй болсон.</Alert></div>}
            <div className="matrix-wrap">
              <table className="matrix">
                <thead>
                  <tr>
                    <th />
                    {data.cols.map((c) => <th key={c.id} title={`${c.kind}: ${c.text || c.title}`}>{c.title}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {data.clos.map((c) => (
                    <tr key={c.id}>
                      <th className="row-h" title={c.text}>{c.code}</th>
                      {data.cols.map((col) => {
                        const x = cellMap.get(`${c.id}:${col.id}`);
                        const show = visible(x);
                        const isSel = sel?.clo === c.id && sel?.col === col.id;
                        return (
                          <td key={col.id}>
                            <div className={`cell ${show ? x!.strength : ""} ${isSel ? "selected" : ""}`}
                              title={show ? `${STRENGTH[x!.strength]} · ${LINK_STATUS[x!.status].label}` : "Холбоогүй"}
                              onClick={() => setSelected({ clo: c.id, col: col.id })}>
                              {show ? fmtScore(x!.score) : "–"}
                              {show && x!.status === "confirmed" && <span className="check">✓</span>}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="legend">
              <span className="tag" style={{ background: "var(--cell-direct)", color: "#fff" }}>Шууд</span>
              <span className="tag" style={{ background: "var(--cell-partial)", color: "var(--navy)" }}>Хэсэгчлэн</span>
              <span className="tag">Холбоогүй</span>
              <span>· Нүдэн дээрх тоо нь ижил төстэй байдлын оноо · ✓ баталгаажсан</span>
            </div>
            {view === "plo" && <p className="muted small">CLO–PLO холбоосыг хөтөлбөрийн хариуцагч баталгаажуулна. Түвшин: Δ = L(CLO) − L(PLO).</p>}
          </div>

          <div className="card detail" style={{ minHeight: 480, display: "flex", flexDirection: "column" }}>
            {!sel || !selClo || !selCol ? <Empty>Матрицын нүдэн дээр дарж холбоосын дэлгэрэнгүйг харна уу (ФШ-24).</Empty> : (
              <>
                <div className="card-head">
                  <h3>Холбоосын дэлгэрэнгүй</h3>
                  {cell ? <Tag tone={LINK_STATUS[cell.status].tone}>{LINK_STATUS[cell.status].label}</Tag> : <Tag>Холбоогүй</Tag>}
                </div>
                <h4>{selClo.code} <BloomLevel level={selClo.bloom_level} /></h4>
                <div>{selClo.text}</div>
                <h4>{selCol.kind} · {selCol.title} <BloomLevel level={selCol.bloom_level} /></h4>
                <div>{selCol.text || <span className="muted">—</span>}</div>
                {cell ? (
                  <>
                    <div className="grid-2" style={{ gap: 12, marginTop: 14 }}>
                      <div className="box"><div className="muted small">Оноо</div><b style={{ fontSize: 20 }}>{cell.score.toFixed(2)}</b>
                        <div className="muted small">{STRENGTH[cell.strength]} · {METHOD_NAMES[cell.method] ?? cell.method}</div></div>
                      <div className="box"><div className="muted small">Түвшин</div>
                        <Tag tone={GAP[cell.level_gap].tone}>{GAP[cell.level_gap].label}</Tag></div>
                    </div>
                    <h4>Таарсан үг</h4>
                    <div className="chips">
                      {cell.matched_terms.length ? cell.matched_terms.map((t) => <span key={t} className="chip">{t}</span>)
                        : <span className="muted small">Түлхүүр үг давхцаагүй (утгын ижил төстэй байдлаар санал болгосон)</span>}
                    </div>
                    {cell.llm_explanation && (
                      <><h4>LLM тайлбар</h4><div className="box" style={{ background: "#fafbfd" }}>{cell.llm_explanation}</div></>
                    )}
                    <div className="spacer" />
                    {!readOnly && (
                      <div className="row" style={{ marginTop: 20 }}>
                        <Button kind="success" style={{ flex: 1 }} disabled={cell.status === "confirmed"}
                          onClick={() => act(() => confirmLink(cell.link_id), "Холбоос баталгаажлаа.")}>Батлах</Button>
                        <Button style={{ flex: 1 }} onClick={() => setStrengthFor(cell)}>Түвшин өөрчлөх</Button>
                        <Button kind="danger" style={{ flex: 1 }}
                          onClick={() => act(() => rejectLink(cell.link_id), "Холбоосыг татгалзлаа.")}>Татгалзах</Button>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="spacer" />
                    {!readOnly && <div style={{ marginTop: 20 }}><Button kind="primary" onClick={() => setAdding({ clo: selClo, col: selCol })}>+ Холбоос нэмэх</Button></div>}
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
      {adding && <AddCellLinkModal clo={adding.clo} col={adding.col} targetType={view} onClose={() => setAdding(null)}
        onSaved={() => { setAdding(null); setMsg({ tone: "green", text: "Холбоос нэмэгдлээ." }); void reload(); }} />}
      {strengthFor && <StrengthModal linkId={strengthFor.link_id} current={strengthFor.strength} onClose={() => setStrengthFor(null)}
        onSaved={() => { setStrengthFor(null); setMsg({ tone: "green", text: "Холбоосын түвшин өөрчлөгдлөө." }); void reload(); }} />}
    </>
  );
}

/** Хоосон нүдэнд холбоос нэмэх (UC4 1а): CLO → элемент эсвэл CLO → PLO. API нь А10-ийнх. */
function AddCellLinkModal({ clo, col, targetType, onClose, onSaved }:
  { clo: Clo; col: Col; targetType: View; onClose: () => void; onSaved: () => void }) {
  const [strength, setStrength] = useState<Strength>("direct");
  const [error, setError] = useState<string | null>(null);
  async function save() {
    try {
      await createLink({ source_type: "clo", source_id: clo.id, target_type: targetType, target_id: col.id, strength });
      onSaved();
    } catch (e) { setError((e as Error).message); }
  }
  return (
    <Modal title="Холбоос нэмэх" onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" onClick={save}>Нэмэх</Button></>}>
      <div className="row"><b>{clo.code}</b><BloomLevel level={clo.bloom_level} /><span>{clo.text}</span></div>
      <div className="row"><b>{col.title}</b><BloomLevel level={col.bloom_level} /><span className="muted">{col.kind}</span></div>
      <div className="row">
        {(["direct", "partial"] as Strength[]).map((s) => (
          <label key={s} className={`option ${strength === s ? "selected" : ""}`} style={{ flex: 1 }}>
            <input type="radio" checked={strength === s} onChange={() => setStrength(s)} />
            <span><b>{STRENGTH[s]}</b></span>
          </label>
        ))}
      </div>
      {error && <Alert>{error}</Alert>}
    </Modal>
  );
}
