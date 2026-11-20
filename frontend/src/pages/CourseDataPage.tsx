// Boundary: ХичээлийнӨгөгдөлДэлгэц (proto-03; UC2, ФШ-04..06, 11, 21). Хариуцагч: Б6
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  addClo, addItem, deleteClo, deleteItem, getCourse, importCsv, listClos, listItems, listVersions, updateClo, updateItem,
} from "../api/courses";
import type { Clo, ImportResult, Item, ItemType, Version } from "../api/types";
import { HistoryBanner, VersionPicker } from "../components/CoursePicker";
import { useAuth } from "../auth";
import {
  Alert, BloomLegend, BloomLevel, Button, Empty, Field, ITEM_TYPE_NAMES, LevelSourceTag, Loading, Modal, PageHeader, Tag,
  BLOOM_NAMES,
} from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";
import AnalysisDialog from "./AnalysisDialog";

export default function CourseDataPage({ openAnalysis = false }: { openAnalysis?: boolean }) {
  const id = Number(useParams().id);
  const nav = useNavigate();
  const { user } = useAuth();
  const course = useAsync(() => getCourse(id), [id]);
  const versions = useAsync(() => listVersions(id), [id]);
  const [params, setParams] = useSearchParams();
  // ?version=ID — түүх хувилбарыг харах (ФШ-07); байхгүй бол идэвхтэй хувилбар
  const vParam = Number(params.get("version")) || null;
  const version: Version | null = (versions.data ?? []).find((v) => v.id === vParam) ?? course.data?.active_version ?? null;
  const vid = version?.id;
  const selectVersion = (v: number) => setParams((p) => {
    if (v === course.data?.active_version?.id) p.delete("version"); else p.set("version", String(v));
    return p;
  });
  const clos = useAsync(() => (vid ? listClos(vid) : Promise.resolve([] as Clo[])), [vid]);
  const items = useAsync(() => (vid ? listItems(vid) : Promise.resolve([] as Item[])), [vid]);
  const [editClo, setEditClo] = useState<Clo | "new" | null>(null);
  const [editItem, setEditItem] = useState<Item | "new" | null>(null);
  const [importing, setImporting] = useState(false);
  const [analysis, setAnalysis] = useState(openAnalysis);
  const [error, setError] = useState<string | null>(null);

  const c = course.data;
  useCrumbs(["Миний хичээлүүд", c ? `${c.code} ${c.name}` : "…"]);
  if (course.error) return <Alert>{course.error}</Alert>;
  if (!c) return <Loading />;
  const owner = c.teacher_id === user?.id;
  const editable = owner && version?.status === "active";

  const reloadAll = () => { void clos.reload(); void items.reload(); void course.reload(); void versions.reload(); };

  async function remove(kind: "clo" | "item", obj: Clo | Item, label: string) {
    if (!confirm(`«${label}»-г устгах уу? Холбогдох холбоосууд мөн устна.`)) return;
    try {
      await (kind === "clo" ? deleteClo(obj.id) : deleteItem(obj.id));
      reloadAll();
    } catch (e) { setError((e as Error).message); }
  }

  return (
    <>
      <PageHeader
        title={`${c.code} · ${c.name}`}
        subtitle={<>Хичээлийн суралцахуйн үр дүн ба сургалтын элементүүд
          {version && <> · v{version.version_no} ({version.academic_year}) · <Link to={`/courses/${c.id}/versions`}>Хувилбарын түүх</Link></>}
          {version && <> · <Link to={`/matrix?course=${c.id}${version.status === "history" ? `&version=${version.id}` : ""}`}>Хамрах хүрээ</Link></>}
        </>}
        actions={<>
          <VersionPicker versions={versions.data ?? []} version={version} onSelect={selectVersion} />
          {editable && <>
            <Button onClick={() => setImporting(true)}>⤓ CSV импортлох</Button>
            <Button kind="primary" onClick={() => setAnalysis(true)}>▶ Шинжилгээ ажиллуулах</Button>
          </>}
        </>}
      />
      <HistoryBanner version={version} onActive={() => c.active_version && selectVersion(c.active_version.id)} />
      {!owner && <Alert tone="blue">Зөвхөн харах горим: энэ хичээлийг зөвхөн тухайн хичээлийн багш засна (ФБШ-04).</Alert>}
      {error && <Alert>{error}</Alert>}

      <div className="grid-2" style={{ marginTop: owner ? 0 : 16 }}>
        <div className="card table-card">
          <div className="card-head">
            <h3>Суралцахуйн үр дүн (CLO)</h3>
            {editable && <Button small onClick={() => setEditClo("new")}>+ Нэмэх</Button>}
          </div>
          {clos.loading && !clos.data ? <Loading /> : !clos.data?.length ? <Empty>CLO бүртгэгдээгүй.</Empty> : (
            <table>
              <thead><tr><th>Код</th><th>Текст</th><th>Блум</th><th>Түвшний эх</th><th /></tr></thead>
              <tbody>
                {clos.data.map((x) => (
                  <tr key={x.id}>
                    <td className="nowrap"><b>{x.code}</b></td>
                    <td className="text">{x.text}</td>
                    <td><BloomLevel level={x.bloom_level} title={x.level_reason ?? undefined} /></td>
                    <td><LevelSourceTag source={x.level_source} reason={x.level_reason} /></td>
                    <td>{editable && (
                      <div className="row-actions">
                        <Button kind="ghost" small onClick={() => setEditClo(x)}>Засах</Button>
                        <Button kind="ghost" small onClick={() => remove("clo", x, x.code)} title="Устгах">✕</Button>
                      </div>
                    )}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card table-card">
          <div className="card-head">
            <h3>Сургалтын элементүүд</h3>
            {editable && <Button small onClick={() => setEditItem("new")}>+ Нэмэх</Button>}
          </div>
          {items.loading && !items.data ? <Loading /> : !items.data?.length ? <Empty>Сургалтын элемент бүртгэгдээгүй.</Empty> : (
            <table>
              <thead><tr><th>Төрөл</th><th>Гарчиг / текст</th><th>Блум</th><th /></tr></thead>
              <tbody>
                {items.data.map((x) => (
                  <tr key={x.id}>
                    <td><Tag>{ITEM_TYPE_NAMES[x.type]}</Tag></td>
                    <td className="text">
                      {x.title}{x.question_text ? `: "${x.question_text}"` : ""}
                      {x.text && <div className="muted small">{x.text}</div>}
                    </td>
                    <td><BloomLevel level={x.bloom_level} title={x.level_reason ?? undefined} />
                      {x.level_source === "manual" && <div className="muted small">гараар</div>}</td>
                    <td>{editable && (
                      <div className="row-actions">
                        <Button kind="ghost" small onClick={() => setEditItem(x)}>Засах</Button>
                        <Button kind="ghost" small onClick={() => remove("item", x, x.title)} title="Устгах">✕</Button>
                      </div>
                    )}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      <BloomLegend />

      {editClo && vid && <CloModal clo={editClo === "new" ? null : editClo} versionId={vid}
        onClose={() => setEditClo(null)} onSaved={() => { setEditClo(null); reloadAll(); }} />}
      {editItem && vid && <ItemModal item={editItem === "new" ? null : editItem} versionId={vid}
        onClose={() => setEditItem(null)} onSaved={() => { setEditItem(null); reloadAll(); }} />}
      {importing && vid && <ImportModal versionId={vid} onClose={() => setImporting(false)} onImported={reloadAll} />}
      {analysis && c.active_version && <AnalysisDialog course={c}
        onClose={() => { setAnalysis(false); if (openAnalysis) nav(`/courses/${c.id}`, { replace: true }); }}
        onDone={reloadAll} />}
    </>
  );
}

/** Блумын түвшин сонгогч: «Автомат» = систем тодорхойлно; 1–6 = гараар засах (ФШ-21). */
function BloomSelect({ value, onChange }: { value: number | null; onChange: (v: number | null) => void }) {
  return (
    <select value={value ?? ""} onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}>
      <option value="">Автомат (систем тодорхойлно)</option>
      {BLOOM_NAMES.map((n, i) => <option key={n} value={i + 1}>{i + 1}. {n} — гараар</option>)}
    </select>
  );
}

function CloModal({ clo, versionId, onClose, onSaved }:
  { clo: Clo | null; versionId: number; onClose: () => void; onSaved: () => void }) {
  const [code, setCode] = useState(clo?.code ?? "");
  const [text, setText] = useState(clo?.text ?? "");
  const [level, setLevel] = useState<number | null>(clo?.level_source === "manual" ? clo.bloom_level : null);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      if (clo) {
        const wasManual = clo.level_source === "manual" ? clo.bloom_level : null;
        await updateClo(clo.id, { code, text, ...(level !== wasManual ? { bloom_level: level } : {}) });
      } else await addClo(versionId, { code, text, bloom_level: level });
      onSaved();
    } catch (err) { setError((err as Error).message); }
  }

  return (
    <Modal title={clo ? `${clo.code} засах` : "CLO нэмэх"} onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" type="submit" form="clo-form">Хадгалах</Button></>}>
      <form id="clo-form" onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <Field label="Код"><input required maxLength={10} placeholder="CLO1" value={code} onChange={(e) => setCode(e.target.value)} /></Field>
        <Field label="Текст" hint="Үйл үгээр эхлүүлж бичвэл Блумын түвшин илүү зөв тодорхойлогдоно (жишээ: «ER диаграм зохиох»).">
          <textarea required value={text} onChange={(e) => setText(e.target.value)} />
        </Field>
        <Field label="Блумын түвшин" hint={clo?.level_reason ? `Одоогийн үндэслэл: ${clo.level_reason}` : undefined}>
          <BloomSelect value={level} onChange={setLevel} />
        </Field>
        {error && <Alert>{error}</Alert>}
      </form>
    </Modal>
  );
}

function ItemModal({ item, versionId, onClose, onSaved }:
  { item: Item | null; versionId: number; onClose: () => void; onSaved: () => void }) {
  const [type, setType] = useState<ItemType>(item?.type ?? "lecture");
  const [title, setTitle] = useState(item?.title ?? "");
  const [text, setText] = useState(item?.text ?? "");
  const [question, setQuestion] = useState(item?.question_text ?? "");
  const [level, setLevel] = useState<number | null>(item?.level_source === "manual" ? item.bloom_level : null);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const body = { type, title, text, question_text: type === "exam" ? question || null : null };
    try {
      if (item) {
        const wasManual = item.level_source === "manual" ? item.bloom_level : null;
        await updateItem(item.id, { ...body, ...(level !== wasManual ? { bloom_level: level } : {}) });
      } else await addItem(versionId, { ...body, bloom_level: level });
      onSaved();
    } catch (err) { setError((err as Error).message); }
  }

  return (
    <Modal title={item ? "Сургалтын элемент засах" : "Сургалтын элемент нэмэх"} onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" type="submit" form="item-form">Хадгалах</Button></>}>
      <form id="item-form" onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <Field label="Төрөл">
          <select value={type} onChange={(e) => setType(e.target.value as ItemType)}>
            {(Object.keys(ITEM_TYPE_NAMES) as ItemType[]).map((t) => <option key={t} value={t}>{ITEM_TYPE_NAMES[t]}</option>)}
          </select>
        </Field>
        <Field label="Гарчиг"><input required maxLength={200} placeholder="Лекц 3. ER загвар" value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
        <Field label="Тайлбар"><textarea value={text} onChange={(e) => setText(e.target.value)} /></Field>
        {type === "exam" && (
          <Field label="Шалгалтын асуулт"><textarea value={question} onChange={(e) => setQuestion(e.target.value)} /></Field>
        )}
        <Field label="Блумын түвшин" hint={item?.level_reason ? `Одоогийн үндэслэл: ${item.level_reason}` : undefined}>
          <BloomSelect value={level} onChange={setLevel} />
        </Field>
        {error && <Alert>{error}</Alert>}
      </form>
    </Modal>
  );
}

function ImportModal({ versionId, onClose, onImported }: { versionId: number; onClose: () => void; onImported: () => void }) {
  const [kind, setKind] = useState<"clo" | "item">("clo");
  const [file, setFile] = useState<File | null>(null);
  const [over, setOver] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const r = await importCsv(versionId, kind, file);
      setResult(r);
      if (r.imported) onImported();
    } catch (e) { setError((e as Error).message); }
    setBusy(false);
  }

  return (
    <Modal title="CSV импортлох" width={620} onClose={onClose}
      subtitle="UTF-8 кодчилолтой, эхний мөр нь толгой. Загвар: data/samples/"
      footer={<><Button onClick={onClose}>Хаах</Button><Button kind="primary" disabled={!file || busy} onClick={submit}>Импортлох</Button></>}>
      <div className="row">
        {(["clo", "item"] as const).map((k) => (
          <label key={k} className={`option ${kind === k ? "selected" : ""}`} style={{ flex: 1 }}>
            <input type="radio" checked={kind === k} onChange={() => { setKind(k); setResult(null); }} />
            <span><b>{k === "clo" ? "CLO" : "Сургалтын элемент"}</b>
              <span className="muted small">{k === "clo" ? "code, text" : "type, title [, text, question_text]"}</span></span>
          </label>
        ))}
      </div>
      <label className={`dropzone ${over ? "over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); setFile(e.dataTransfer.files[0] ?? null); setResult(null); }}>
        <input type="file" accept=".csv,text/csv" hidden onChange={(e) => { setFile(e.target.files?.[0] ?? null); setResult(null); }} />
        {file ? <><b>{file.name}</b> · {(file.size / 1024).toFixed(1)} KB</> : "CSV файлаа энд чирч оруулах эсвэл дарж сонгох"}
      </label>
      {kind === "item" && <p className="muted small" style={{ margin: 0 }}>type ∈ lecture, lab, assignment, exam</p>}
      {error && <Alert>{error}</Alert>}
      {result && (
        <>
          <Alert tone={result.errors.length ? "yellow" : "green"}>
            {result.imported} мөр импортлогдлоо{result.errors.length ? `, ${result.errors.length} мөр алдаатай` : ""}.
          </Alert>
          {result.errors.length > 0 && (
            <table>
              <thead><tr><th>Мөр</th><th>Шалтгаан</th></tr></thead>
              <tbody>{result.errors.map((e) => <tr key={e.row}><td>{e.row}</td><td>{e.reason}</td></tr>)}</tbody>
            </table>
          )}
        </>
      )}
    </Modal>
  );
}
