// Boundary: НэвтрэхДэлгэц (proto-01; ФШ-01). Хариуцагч: Б1 — ажиллах хувилбар бэлэн.
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/client";
import { Button } from "../components/ui";

export default function LoginPage() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      await login(email, password);
      nav("/");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div style={{ display: "grid", placeItems: "center", minHeight: "100vh" }}>
      <form className="card" onSubmit={submit} style={{ width: 360, display: "grid", gap: 12 }}>
        <h2 style={{ margin: 0 }}>Уялдаа</h2>
        <input placeholder="Имэйл" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input placeholder="Нууц үг" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <div style={{ color: "var(--red)" }}>{error}</div>}
        <Button kind="primary" type="submit">Нэвтрэх</Button>
      </form>
    </div>
  );
}
