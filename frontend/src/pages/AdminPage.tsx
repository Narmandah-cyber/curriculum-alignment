// Boundary: АдминДэлгэц (proto-09; UC10, UC11, ФШ-02, 09, 11). Хариуцагч: Б8
// Өгөгдөл: А3 (хэрэглэгч, тохиргоо, Блумын толь), А5 (CS2023). Хэрэгжээгүй хэсэг Pending-ээр харагдана.
import { useEffect, useState, type FormEvent } from "react";
import {
  addBloomVerb, createUser, deleteBloomVerb, grantRole, listBloomVerbs, listCs2023, listSettings, listUsers, revokeRole,
  setSetting, updateUser,
} from "../api/program";
import type { Role, User } from "../api/types";
import { ROLE_NAMES, useAuth } from "../auth";
import { Alert, BLOOM_NAMES, BloomLevel, Button, Empty, Field, LoadError, Modal, PageHeader, Tag } from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

const ROLES: Role[] = ["teacher", "coordinator", "admin"];
const ROLE_TONE: Record<Role, "blue" | "yellow"> = { teacher: "blue", coordinator: "blue", admin: "yellow" };

// settings хүснэгтийн түлхүүр (docs/LOOKUP.md); утга нь текст
const FIELDS = [
  { key: "embedding_model", label: "Embedding загвар", type: "text", placeholder: "intfloat/multilingual-e5-base" },
  { key: "direct_threshold", label: "Холбоосын босго (шууд)", type: "number", placeholder: "0.70" },
  { key: "link_threshold", label: "Холбоосын босго (хэсэгчлэн)", type: "number", placeholder: "0.50" },
  { key: "llm_enabled", label: "LLM үйлчилгээ", type: "select", placeholder: "false" },
] as const;

export default function AdminPage() {
  useCrumbs(["Тохиргоо", "Хэрэглэгч ба эрх"]);
  const { user: me } = useAuth();
  const users = useAsync(() => listUsers(), []);
  const settings = useAsync(() => listSettings(), []);
  const verbs = useAsync(() => listBloomVerbs(), []);
  const cs = useAsync(() => listCs2023(), []);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [verbsOpen, setVerbsOpen] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ tone: "red" | "green"; text: string } | null>(null);

  useEffect(() => {
    if (settings.data) setValues(Object.fromEntries(settings.data.map((s) => [s.key, s.value])));
  }, [settings.data]);

  async function save() {
    setMsg(null);
    const direct = Number(values.direct_threshold || 0.7), partial = Number(values.link_threshold || 0.5);
    for (const k of ["direct_threshold", "link_threshold"]) {
      const v = values[k];
      if (v !== undefined && v !== "" && !(Number(v) > 0 && Number(v) < 1)) {
        setMsg({ tone: "red", text: "Босго 0-ээс 1-ийн хооронд байна." });
        return;
      }
    }
    if (partial >= direct) { setMsg({ tone: "red", text: "«Хэсэгчлэн» босго «шууд» босгоос бага байх ёстой." }); return; }
    const before = Object.fromEntries((settings.data ?? []).map((s) => [s.key, s.value]));
    try {
      for (const f of FIELDS) {
        const v = values[f.key];
        if (v !== undefined && v !== before[f.key]) await setSetting(f.key, v);
      }
      setMsg({ tone: "green", text: "Тохиргоо хадгалагдлаа. Дараагийн шинжилгээнд хэрэглэгдэнэ." });
      await settings.reload();
    } catch (e) { setMsg({ tone: "red", text: (e as Error).message }); }
  }

  const settingsDisabled = settings.status === 501;

  return (
    <>
      <PageHeader title="Хэрэглэгч ба тохиргоо" subtitle="Хэрэглэгчийн эрх, шинжилгээний тохиргоо, жишиг өгөгдөл"
        actions={<Button kind="primary" onClick={() => setAdding(true)} disabled={users.status === 501}>+ Хэрэглэгч нэмэх</Button>} />
      <div className="split" style={{ gridTemplateColumns: "minmax(0, 1fr) 380px" }}>
        <div className="card">
          <h3 style={{ marginBottom: 12 }}>Хэрэглэгчид</h3>
          <LoadError error={users.error} status={users.status} task="А3" what="Хэрэглэгчийн жагсаалт" />
          {users.status === 501 && me && (
            <table style={{ marginTop: 12 }}>
              <thead><tr><th>Нэр</th><th>Имейл</th><th>Үүрэг</th><th>Төлөв</th></tr></thead>
              <tbody><UserRow u={me} note="(та)" /></tbody>
            </table>
          )}
          {users.data && (users.data.length ? (
            <table>
              <thead><tr><th style={{ width: 160 }}>Нэр</th><th>Имейл</th><th style={{ width: 230 }}>Үүрэг</th><th style={{ width: 110 }}>Төлөв</th><th /></tr></thead>
              <tbody>{users.data.map((u) => <UserRow key={u.id} u={u} note={u.id === me?.id ? "(та)" : undefined} onEdit={() => setEditing(u)} />)}</tbody>
            </table>
          ) : <Empty>Хэрэглэгч алга.</Empty>)}
        </div>

        <div className="card card-col">
          <h3>Шинжилгээний тохиргоо</h3>
          {settingsDisabled && <LoadError error={settings.error} status={501} task="А3" what="Тохиргоо" />}
          {settings.error && !settingsDisabled && <Alert>{settings.error}</Alert>}
          {FIELDS.map((f) => (
            <Field key={f.key} label={f.label}>
              {f.type === "select" ? (
                <select disabled={settingsDisabled} value={values[f.key] ?? "false"} onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}>
                  <option value="false">Идэвхгүй (сонголттой)</option>
                  <option value="true">Идэвхтэй</option>
                </select>
              ) : (
                <input disabled={settingsDisabled} type={f.type} step="0.01" min={0} max={1} placeholder={f.placeholder}
                  value={values[f.key] ?? ""} onChange={(e) => setValues({ ...values, [f.key]: e.target.value })} />
              )}
            </Field>
          ))}
          <h3>Жишиг өгөгдөл</h3>
          <div className="row"><span style={{ fontSize: 13 }}>CS2023 мэдлэгийн чиглэл</span><span className="spacer" />
            {cs.data ? <Tag>{new Set(cs.data.map((u) => u.area)).size} чиглэл</Tag> : <Tag>{cs.status === 501 ? "А5" : "—"}</Tag>}</div>
          <div className="row"><span style={{ fontSize: 13 }}>Блумын үйл үгийн толь</span><span className="spacer" />
            {verbs.data ? <Tag>{verbs.data.length} үйл үг</Tag> : <Tag>{verbs.status === 501 ? "А3" : "—"}</Tag>}
            <Button small kind="ghost" onClick={() => setVerbsOpen(true)} disabled={!verbs.data}>Засах</Button></div>
          <p className="muted small" style={{ margin: 0 }}>Босгын утгууд нь жишээ; эцсийн утгыг тэмдэглэгээтэй өгөгдөл дээр сонгоно (docs/ANNOTATION.md).</p>
          {msg && <Alert tone={msg.tone}>{msg.text}</Alert>}
          <Button kind="primary" onClick={save} disabled={settingsDisabled}>Хадгалах</Button>
        </div>
      </div>
      {adding && <UserModal onClose={() => setAdding(false)} onSaved={() => { setAdding(false); void users.reload(); }} />}
      {editing && <UserModal user={editing} self={editing.id === me?.id} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); void users.reload(); }} />}
      {verbsOpen && <VerbsModal onClose={() => { setVerbsOpen(false); void verbs.reload(); }} />}
    </>
  );
}

function UserRow({ u, note, onEdit }: { u: User; note?: string; onEdit?: () => void }) {
  return (
    <tr>
      <td>{u.full_name} {note && <span className="muted small">{note}</span>}</td>
      <td>{u.email}</td>
      <td><div className="chips">{u.roles.map((r) => <Tag key={r} tone={ROLE_TONE[r]}>{ROLE_NAMES[r]}</Tag>)}</div></td>
      <td>{u.is_active ? <Tag tone="green">Идэвхтэй</Tag> : <Tag>Түр хаасан</Tag>}</td>
      {onEdit && <td><Button small kind="ghost" onClick={onEdit}>Засах</Button></td>}
    </tr>
  );
}

/** Хэрэглэгч нэмэх / засах: үүрэг оноох-цуцлах, идэвхгүй болгох (UC10). */
function UserModal({ user, self, onClose, onSaved }: { user?: User; self?: boolean; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(user?.full_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [password, setPassword] = useState("");
  const [roles, setRoles] = useState<Role[]>(user?.roles ?? ["teacher"]);
  const [active, setActive] = useState(user?.is_active ?? true);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!roles.length) { setError("Дор хаяж нэг үүрэг сонгоно уу."); return; }
    try {
      if (!user) await createUser({ full_name: name.trim(), email: email.trim(), password, roles });
      else {
        const patch: Partial<User> = {};
        if (name !== user.full_name) patch.full_name = name.trim();
        if (email !== user.email) patch.email = email.trim();
        if (active !== user.is_active) patch.is_active = active;
        if (Object.keys(patch).length) await updateUser(user.id, patch);
        for (const r of ROLES) {
          if (roles.includes(r) && !user.roles.includes(r)) await grantRole(user.id, r);
          if (!roles.includes(r) && user.roles.includes(r)) await revokeRole(user.id, r);
        }
      }
      onSaved();
    } catch (err) { setError((err as Error).message); }
  }

  return (
    <Modal title={user ? "Хэрэглэгч засах" : "Хэрэглэгч нэмэх"} onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" type="submit" form="user-form">Хадгалах</Button></>}>
      <form id="user-form" onSubmit={submit} style={{ display: "grid", gap: 14 }}>
        <Field label="Овог нэр"><input required placeholder="Б. Багш" value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Field label="Имейл"><input required type="email" placeholder="name@must.edu.mn" value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        {!user && <Field label="Анхны нууц үг" hint="Хэрэглэгч анх нэвтрээд солино."><input required type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></Field>}
        <div className="field-label">Үүрэг</div>
        <div className="row wrap">
          {ROLES.map((r) => (
            <label key={r} className={`option ${roles.includes(r) ? "selected" : ""}`} style={{ flex: 1, alignItems: "center" }}>
              <input type="checkbox" checked={roles.includes(r)} disabled={self && r === "admin"}
                onChange={(e) => setRoles(e.target.checked ? [...roles, r] : roles.filter((x) => x !== r))} />
              <span>{ROLE_NAMES[r]}</span>
            </label>
          ))}
        </div>
        {user && !self && (
          <label className="row"><input type="checkbox" style={{ width: "auto" }} checked={active} onChange={(e) => setActive(e.target.checked)} /> Идэвхтэй (нэвтэрч болно)</label>
        )}
        {error && <Alert>{error}</Alert>}
      </form>
    </Modal>
  );
}

/** Блумын үйл үгийн толь (UC11, ФШ-11): нэмэх, хасах. */
function VerbsModal({ onClose }: { onClose: () => void }) {
  const verbs = useAsync(() => listBloomVerbs(), []);
  const [verb, setVerb] = useState("");
  const [level, setLevel] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<number | null>(null);

  async function add(e: FormEvent) {
    e.preventDefault();
    try { await addBloomVerb(verb.trim().toLowerCase(), level); setVerb(""); await verbs.reload(); }
    catch (err) { setError((err as Error).message); }
  }
  async function remove(id: number) {
    try { await deleteBloomVerb(id); await verbs.reload(); } catch (err) { setError((err as Error).message); }
  }
  const list = (verbs.data ?? []).filter((v) => !filter || v.level === filter).sort((a, b) => a.level - b.level || a.verb.localeCompare(b.verb));

  return (
    <Modal title="Блумын үйл үгийн толь" width={640} onClose={onClose} footer={<Button onClick={onClose}>Хаах</Button>}
      subtitle="Үйл үгийг нэгдүгээр хэлбэрээр (-х) бичнэ: «тайлбарлах». Систем нөхцөлтэй хэлбэрийг (тайлбарлана) таньна.">
      <LoadError error={verbs.error} status={verbs.status} task="А3" what="Блумын толь" />
      <form onSubmit={add} className="row" style={{ alignItems: "flex-end" }}>
        <div style={{ flex: 1 }}><Field label="Үйл үг"><input required placeholder="зохиомжлох" value={verb} onChange={(e) => setVerb(e.target.value)} /></Field></div>
        <Field label="Түвшин">
          <select value={level} onChange={(e) => setLevel(Number(e.target.value))}>
            {BLOOM_NAMES.map((n, i) => <option key={n} value={i + 1}>{i + 1}. {n}</option>)}
          </select>
        </Field>
        <Button type="submit">+ Нэмэх</Button>
      </form>
      <div className="row wrap">
        <Button small kind={filter === null ? "primary" : "secondary"} onClick={() => setFilter(null)}>Бүгд</Button>
        {BLOOM_NAMES.map((n, i) => <Button key={n} small kind={filter === i + 1 ? "primary" : "secondary"} onClick={() => setFilter(i + 1)}>{i + 1}</Button>)}
      </div>
      <div style={{ maxHeight: 320, overflow: "auto" }}>
        <table>
          <tbody>{list.map((v) => (
            <tr key={v.id}><td><BloomLevel level={v.level} /></td><td style={{ width: "100%" }}>{v.verb}</td>
              <td><Button small kind="ghost" onClick={() => remove(v.id)} title="Хасах">✕</Button></td></tr>
          ))}</tbody>
        </table>
      </div>
      {error && <Alert>{error}</Alert>}
    </Modal>
  );
}
