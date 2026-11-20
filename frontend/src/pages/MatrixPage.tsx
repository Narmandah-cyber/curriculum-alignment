// Boundary: МатрицДэлгэц (proto-05; UC4, UC5, ФШ-19, 22, 24). Хариуцагч: Б7
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { confirmLink, createReport, getMatrix, rejectLink } from "../api/courses";
import type { Clo, Item, MatrixCell } from "../api/types";
import { CoursePicker, useSelectedCourse } from "../components/CoursePicker";
import { AddLinkModal, StrengthModal } from "../components/LinkModals";
import {
  Alert, BloomLevel, Button, Empty, fmtDate, GAP, ITEM_TYPE_NAMES, LINK_STATUS, Loading, PageHeader, STRENGTH, Tag,
} from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

const METHOD_NAMES: Record<string, string> = { rule: "Дүрэмд суурилсан", embedding: "Embedding", hybrid: "Хосолсон" };
type Filter = "all" | "proposed" | "confirmed";

const fmtScore = (s: number) => s.toFixed(2).replace(/^0/, "");

export default function MatrixPage() {
  const { courses, course, select, params, error: cErr, loading: cLoading } = useSelectedCourse();
  const vid = course?.active_version?.id;
  const m = useAsync(() => (vid ? getMatrix(vid) : Promise.resolve(null)), [vid]);
  const [selected, setSelected] = useState<{ clo: number; item: number } | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [adding, setAdding] = useState<{ clo: Clo; item: Item } | null>(null);
  const [strengthFor, setStrengthFor] = useState<MatrixCell | null>(null);
  const [msg, setMsg] = useState<{ tone: "red" | "green" | "yellow"; text: string } | null>(null);
  useCrumbs(["Хамрах хүрээ", course ? `${course.code} ${course.name}` : "…"]);

  const data = m.data;
  const cellMap = useMemo(() => {
    const map = new Map<string, MatrixCell>();
    data?.cells.forEach((c) => map.set(`${c.clo_id}:${c.item_id}`, c));
    return map;
  }, [data]);

  // ?link=ID — түвшний зөрүү дэлгэцийн «Харах» товчоос
  const linkParam = Number(params.get("link")) || null;
  const fromLink = linkParam ? data?.cells.find((c) => c.link_id === linkParam) : undefined;
  const sel = selected ?? (fromLink ? { clo: fromLink.clo_id, item: fromLink.item_id } : null);
  const cell = sel ? cellMap.get(`${sel.clo}:${sel.item}`) : undefined;
  const selClo = data?.clos.find((c) => c.id === sel?.clo);
  const selItem = data?.items.find((i) => i.id === sel?.item);

  async function act(fn: () => Promise<unknown>, ok: string) {
    setMsg(null);
    try {
      await fn();
      setMsg({ tone: "green", text: ok });
      await m.reload();
    } catch (e) {
      setMsg({ tone: "red", text: (e as Error).message });
    }
  }

  async function report() {
    if (!data?.run) return;
    await act(() => createReport(data.run!.id, "csv"), "Тайлан үүслээ.");
  }

  if (cErr) return <Alert>{cErr}</Alert>;
  if (cLoading && !courses.length) return <Loading />;
  if (!course) return <Empty>Хичээл алга. <Link to="/courses">Хичээл нэмэх</Link></Empty>;

  const visible = (c?: MatrixCell) => !!c && (filter === "all" || c.status === filter);
  const run = data?.run;

  return (
    <>
      <PageHeader title="Хамрах хүрээний матриц"
        subtitle={run ? <>{METHOD_NAMES[run.method] ?? run.method} арга · {fmtDate(run.started_at)} · {data?.proposed} санал, {data?.confirmed} баталгаажсан</> : `${course.code} · ${course.name}`}
        actions={<>
          <CoursePicker courses={courses} course={course} onSelect={(id) => { setSelected(null); select(id); }} />
          <select style={{ width: "auto" }} value={filter} onChange={(e) => setFilter(e.target.value as Filter)} aria-label="Шүүлтүүр">
            <option value="all">Бүх холбоос</option>
            <option value="proposed">Зөвхөн санал</option>
            <option value="confirmed">Зөвхөн баталгаажсан</option>
          </select>
          <Button onClick={report} disabled={!run}>⤓ Тайлан</Button>
        </>} />
      {msg && <div style={{ marginBottom: 14 }}><Alert tone={msg.tone}>{msg.text}</Alert></div>}
      {m.error && <Alert>{m.error}</Alert>}
      {!data ? <Loading /> : !data.clos.length || !data.items.length ? (
        <Empty>CLO эсвэл сургалтын элемент бүртгэгдээгүй. <Link to={`/courses/${course.id}`}>Хичээлийн өгөгдөл</Link></Empty>
      ) : (
        <div className="split">
          <div className="card">
            {!run && <div style={{ marginBottom: 14 }}><Alert tone="blue">Шинжилгээ хийгдээгүй байна. <Link to={`/courses/${course.id}/analysis`}>Шинжилгээ ажиллуулах</Link></Alert></div>}
            {run?.status === "running" && <div style={{ marginBottom: 14 }}><Alert tone="yellow">Шинжилгээ явагдаж байна ({run.progress}%)… <button className="link-btn" onClick={() => void m.reload()}>Шинэчлэх</button></Alert></div>}
            {run?.status === "failed" && <div style={{ marginBottom: 14 }}><Alert>Сүүлийн шинжилгээ амжилтгүй болсон.</Alert></div>}
            <div className="matrix-wrap">
              <table className="matrix">
                <thead>
                  <tr>
                    <th />
                    {data.items.map((i) => <th key={i.id} title={`${ITEM_TYPE_NAMES[i.type]}: ${i.title}`}>{i.title}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {data.clos.map((c) => (
                    <tr key={c.id}>
                      <th className="row-h" title={c.text}>{c.code}</th>
                      {data.items.map((i) => {
                        const x = cellMap.get(`${c.id}:${i.id}`);
                        const show = visible(x);
                        const isSel = sel?.clo === c.id && sel?.item === i.id;
                        return (
                          <td key={i.id}>
                            <div className={`cell ${show ? x!.strength : ""} ${isSel ? "selected" : ""}`}
                              title={show ? `${STRENGTH[x!.strength]} · ${LINK_STATUS[x!.status].label}` : "Холбоогүй — дарж холбоос нэмэх"}
                              onClick={() => setSelected({ clo: c.id, item: i.id })}>
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
              <span className="tag" style={{ background: "var(--cell-partial)", color: "#1f2a55" }}>Хэсэгчлэн</span>
              <span className="tag">Холбоогүй</span>
              <span>· Нүдэн дээрх тоо нь ижил төстэй байдлын оноо · ✓ баталгаажсан</span>
            </div>
          </div>

          <div className="card detail" style={{ minHeight: 480, display: "flex", flexDirection: "column" }}>
            {!sel || !selClo || !selItem ? <Empty>Матрицын нүдэн дээр дарж холбоосын дэлгэрэнгүйг харна уу (ФШ-24).</Empty> : (
              <>
                <div className="card-head">
                  <h3>Холбоосын дэлгэрэнгүй</h3>
                  {cell ? <Tag tone={LINK_STATUS[cell.status].tone}>{LINK_STATUS[cell.status].label}</Tag> : <Tag>Холбоогүй</Tag>}
                </div>
                <h4>{selClo.code} <BloomLevel level={selClo.bloom_level} /></h4>
                <div>{selClo.text}</div>
                <h4>{ITEM_TYPE_NAMES[selItem.type]} · {selItem.title} <BloomLevel level={selItem.bloom_level} /></h4>
                <div>{[selItem.text, selItem.question_text].filter(Boolean).join(" — ") || <span className="muted">—</span>}</div>
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
                    <div className="row" style={{ marginTop: 20 }}>
                      <Button kind="success" style={{ flex: 1 }} disabled={cell.status === "confirmed"}
                        onClick={() => act(() => confirmLink(cell.link_id), "Холбоос баталгаажлаа.")}>Батлах</Button>
                      <Button style={{ flex: 1 }} onClick={() => setStrengthFor(cell)}>Түвшин өөрчлөх</Button>
                      <Button kind="danger" style={{ flex: 1 }}
                        onClick={() => act(() => rejectLink(cell.link_id), "Холбоосыг татгалзлаа.")}>Татгалзах</Button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="spacer" />
                    <div style={{ marginTop: 20 }}><Button kind="primary" onClick={() => setAdding({ clo: selClo, item: selItem })}>+ Холбоос нэмэх</Button></div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
      {adding && <AddLinkModal clo={adding.clo} item={adding.item} onClose={() => setAdding(null)}
        onSaved={() => { setAdding(null); setMsg({ tone: "green", text: "Холбоос нэмэгдлээ." }); void m.reload(); }} />}
      {strengthFor && <StrengthModal linkId={strengthFor.link_id} current={strengthFor.strength} onClose={() => setStrengthFor(null)}
        onSaved={() => { setStrengthFor(null); setMsg({ tone: "green", text: "Холбоосын түвшин өөрчлөгдлөө." }); void m.reload(); }} />}
    </>
  );
}
