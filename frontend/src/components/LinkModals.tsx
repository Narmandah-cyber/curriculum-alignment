// Холбоос гараар нэмэх, холбоосын хүч өөрчлөх цонх (UC4 1а, ФШ-19). API нь А10-ийнх. Хариуцагч: Б7.
import { useState } from "react";
import { changeStrength, createLink } from "../api/courses";
import type { Clo, Item, Strength } from "../api/types";
import { Alert, BloomLevel, Button, Field, ITEM_TYPE_NAMES, Modal, STRENGTH } from "./ui";

function StrengthChoice({ value, onChange }: { value: Strength; onChange: (s: Strength) => void }) {
  return (
    <div className="row">
      {(["direct", "partial"] as Strength[]).map((s) => (
        <label key={s} className={`option ${value === s ? "selected" : ""}`} style={{ flex: 1 }}>
          <input type="radio" checked={value === s} onChange={() => onChange(s)} />
          <span><b>{STRENGTH[s]}</b><span className="muted small">{s === "direct" ? "Элемент CLO-г бүрэн хамарна" : "Хэсэгчлэн хамарна"}</span></span>
        </label>
      ))}
    </div>
  );
}

export function AddLinkModal({ clo, item, items, onClose, onSaved }:
  { clo: Clo; item?: Item; items?: Item[]; onClose: () => void; onSaved: () => void }) {
  const [target, setTarget] = useState<number | null>(item?.id ?? items?.[0]?.id ?? null);
  const [strength, setStrength] = useState<Strength>("direct");
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!target) return;
    try {
      await createLink({ source_type: "clo", source_id: clo.id, target_type: "item", target_id: target, strength });
      onSaved();
    } catch (e) { setError((e as Error).message); }
  }

  return (
    <Modal title="Холбоос нэмэх" onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" disabled={!target} onClick={save}>Нэмэх</Button></>}>
      <div className="row"><b>{clo.code}</b><BloomLevel level={clo.bloom_level} /><span>{clo.text}</span></div>
      {item ? (
        <div className="row"><b>{item.title}</b><BloomLevel level={item.bloom_level} /></div>
      ) : (
        <Field label="Сургалтын элемент">
          <select value={target ?? ""} onChange={(e) => setTarget(Number(e.target.value))}>
            {(items ?? []).map((i) => <option key={i.id} value={i.id}>{ITEM_TYPE_NAMES[i.type]} · {i.title}</option>)}
          </select>
        </Field>
      )}
      <Field label="Холбоосын хүч"><StrengthChoice value={strength} onChange={setStrength} /></Field>
      {error && <Alert>{error}</Alert>}
    </Modal>
  );
}

export function StrengthModal({ linkId, current, onClose, onSaved }:
  { linkId: number; current: Strength; onClose: () => void; onSaved: () => void }) {
  const [strength, setStrength] = useState<Strength>(current === "direct" ? "partial" : "direct");
  const [error, setError] = useState<string | null>(null);
  async function save() {
    try { await changeStrength(linkId, strength); onSaved(); } catch (e) { setError((e as Error).message); }
  }
  return (
    <Modal title="Холбоосын түвшин өөрчлөх" onClose={onClose}
      footer={<><Button onClick={onClose}>Цуцлах</Button><Button kind="primary" onClick={save} disabled={strength === current}>Хадгалах</Button></>}>
      <StrengthChoice value={strength} onChange={setStrength} />
      {error && <Alert>{error}</Alert>}
    </Modal>
  );
}
