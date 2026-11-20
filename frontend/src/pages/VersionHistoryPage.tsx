// Boundary: ХувилбарынТүүхДэлгэц (proto-10; UC12, ФШ-07). Хариуцагч: Б6
import { useEffect, useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { compareVersions, getCourse, listVersions, renewCourse } from "../api/courses";
import type { Version, VersionCompare } from "../api/types";
import { useAuth } from "../auth";
import { Alert, Button, Empty, Field, fmtDate, Loading, Modal, PageHeader, Tag } from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

const CHANGE = {
  added: { label: "Нэмэгдсэн", tone: "green" as const },
  modified: { label: "Өөрчлөгдсөн", tone: "yellow" as const },
  removed: { label: "Хасагдсан", tone: "red" as const },
};

function nextYear(y: string) {
  const a = Number(y.slice(0, 4));
  return Number.isFinite(a) ? `${a + 1}-${a + 2}` : "";
}

export default function VersionHistoryPage() {
  const id = Number(useParams().id);
  const { user } = useAuth();
  const course = useAsync(() => getCourse(id), [id]);
  const versions = useAsync(() => listVersions(id), [id]);
  const [pair, setPair] = useState<[number, number] | null>(null);   // [хуучин, шинэ]
  const [cmp, setCmp] = useState<VersionCompare | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [renewing, setRenewing] = useState(false);

  const c = course.data;
  useCrumbs(["Миний хичээлүүд", c ? `${c.code} ${c.name}` : "…", "Хувилбарын түүх"]);
  const vs = versions.data ?? [];

  // Анхдагч: хамгийн сүүлийн хоёр хувилбарыг харьцуулна
  useEffect(() => {
    if (vs.length >= 2 && !pair) setPair([vs[1].id, vs[0].id]);
  }, [vs, pair]);

  useEffect(() => {
    if (!pair) return;
    compareVersions(pair[0], pair[1]).then((r) => { setCmp(r); setError(null); }).catch((e: Error) => setError(e.message));
  }, [pair]);

  function pick(v: Version) {
    // Сонгосон хувилбарыг өмнөхтэй нь харьцуулна
    const idx = vs.findIndex((x) => x.id === v.id);
    const older = vs[idx + 1];
    if (older) setPair([older.id, v.id]);
    else if (vs.length >= 2) setPair([v.id, vs[0].id]);
  }

  if (course.error) return <Alert>{course.error}</Alert>;
  if (!c) return <Loading />;
  const owner = c.teacher_id === user?.id;
  const label = (v?: Version) => (v ? `v${v.version_no} (${v.academic_year})` : "");

  return (
    <>
      <PageHeader title={`${c.code} · ${c.name} — хувилбарын түүх`}
        subtitle="Хичээлийн хөтөлбөр шинэчлэгдэх бүрд өмнөх хувилбар «түүх» болж хадгалагдана"
        actions={owner && <Button kind="primary" onClick={() => setRenewing(true)}>+ Шинэ хувилбар үүсгэх</Button>} />
      {error && <Alert>{error}</Alert>}
      <div className="split" style={{ gridTemplateColumns: "400px minmax(0, 1fr)" }}>
        <div className="card">
          <h3 style={{ marginBottom: 14 }}>Хувилбарууд</h3>
          {versions.loading && !versions.data ? <Loading /> : vs.map((v) => (
            <div key={v.id} className={`version ${v.status === "active" ? "active-v" : ""} ${pair?.[1] === v.id ? "picked" : ""}`}
              onClick={() => pick(v)}>
              <div className="row">
                <b>v{v.version_no} · {v.academic_year}</b>
                {v.status === "active" ? <Tag tone="green">Идэвхтэй</Tag> : <Tag>Түүх</Tag>}
              </div>
              <span className="muted small">{v.clo_count} CLO · {v.item_count} сургалтын элемент</span>
              <span className="muted small">Үүсгэсэн: {fmtDate(v.created_at)} · {v.status === "active" ? "Засварлах боломжтой" : "🔒 Зөвхөн харах"}</span>
            </div>
          ))}
          <Alert tone="yellow">Хуучин хувилбарын CLO, сургалтын элемент, шинжилгээний үр дүн устахгүй, «түүх» төлөвтэй хадгалагдана. Түүх хувилбарыг засах боломжгүй.</Alert>
        </div>

        <div className="card">
          {vs.length < 2 ? <Empty>Харьцуулах хоёр хувилбар алга. «Шинэ хувилбар үүсгэх» товчоор дараагийн хичээлийн жилийн хувилбарыг үүсгэнэ үү.</Empty>
            : !cmp ? <Loading /> : (
              <>
                <div className="row wrap" style={{ marginBottom: 12 }}>
                  <h3>Харьцуулалт:</h3>
                  <select style={{ width: "auto" }} value={pair?.[0]} onChange={(e) => setPair([Number(e.target.value), pair![1]])}>
                    {vs.filter((v) => v.id !== pair?.[1]).map((v) => <option key={v.id} value={v.id}>{label(v)}</option>)}
                  </select>
                  <span>→</span>
                  <select style={{ width: "auto" }} value={pair?.[1]} onChange={(e) => setPair([pair![0], Number(e.target.value)])}>
                    {vs.filter((v) => v.id !== pair?.[0]).map((v) => <option key={v.id} value={v.id}>{label(v)}</option>)}
                  </select>
                </div>
                <div className="row" style={{ marginBottom: 12 }}>
                  <Tag tone="green">+{cmp.added} нэмэгдсэн</Tag>
                  <Tag tone="yellow">{cmp.modified} өөрчлөгдсөн</Tag>
                  <Tag tone="red">{cmp.removed} хасагдсан</Tag>
                </div>
                {cmp.changes.length === 0 ? <Empty>Ялгаа алга.</Empty> : (
                  <table>
                    <thead><tr><th>Өөрчлөлт</th><th>Объект</th><th>Агуулга</th></tr></thead>
                    <tbody>
                      {cmp.changes.map((ch, i) => (
                        <tr key={i}>
                          <td><Tag tone={CHANGE[ch.change].tone}>{CHANGE[ch.change].label}</Tag></td>
                          <td className="nowrap">{ch.key}<div className="muted small">{ch.kind === "clo" ? "CLO" : "Элемент"}</div></td>
                          <td>{ch.change === "modified" ? <>"{ch.old_text}" → "{ch.new_text}"</> : (ch.new_text ?? ch.old_text)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <div style={{ marginTop: 14 }}>
                  <Alert tone="blue">Шинэ хувилбар үүсгэхэд баталгаажсан холбоосууд хуулагдсан CLO, элементэд шилжинэ. Өөрчлөгдсөн CLO-ийн холбоосыг дахин шалгахыг санал болгоно.</Alert>
                </div>
              </>
            )}
        </div>
      </div>
      {renewing && <RenewModal suggested={nextYear(vs[0]?.academic_year ?? "")} onClose={() => setRenewing(false)}
        onSubmit={async (year) => {
          await renewCourse(id, year);
          setRenewing(false);
          setPair(null);
          setCmp(null);
          void versions.reload();
          void course.reload();
        }} />}
    </>
  );
}

function RenewModal({ suggested, onClose, onSubmit }:
  { suggested: string; onClose: () => void; onSubmit: (year: string) => Promise<void> }) {
  const [year, setYear] = useState(suggested);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try { await onSubmit(year); } catch (err) { setError((err as Error).message); setBusy(false); }
  }
  return (
    <Modal title="Шинэ хувилбар үүсгэх" onClose={onClose}
      subtitle="Идэвхтэй хувилбарын CLO, сургалтын элемент, баталгаажсан холбоос хуулагдаж, одоогийн хувилбар «түүх» болно."
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" type="submit" form="renew-form" disabled={busy}>Үүсгэх</Button></>}>
      <form id="renew-form" onSubmit={submit}>
        <Field label="Хичээлийн жил"><input required pattern="\d{4}-\d{4}" value={year} onChange={(e) => setYear(e.target.value)} /></Field>
      </form>
      {error && <Alert>{error}</Alert>}
    </Modal>
  );
}
