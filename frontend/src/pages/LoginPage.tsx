// Boundary: НэвтрэхДэлгэц (proto-01; ФШ-01). Хариуцагч: Б1.
import { useState, type FormEvent } from "react";
import { login } from "../api/client";
import { Alert, Button, Field } from "../components/ui";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email.trim(), password);
      location.assign("/");          // хэрэглэгчийн контекстыг шинээр ачаална
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  return (
    <div className="login-bg">
      <form className="login-card" onSubmit={submit}>
        <div className="brand" style={{ color: "var(--text)", margin: 0 }}><span className="logo" /> Уялдаа</div>
        <div>
          <h1>Нэвтрэх</h1>
          <p className="subtitle">Сургалтын хөтөлбөр, хичээлийн уялдааг шинжлэх систем</p>
        </div>
        <Field label="Имейл хаяг">
          <input type="email" required autoComplete="username" placeholder="name@must.edu.mn"
            value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>
        <Field label="Нууц үг">
          <input type="password" required autoComplete="current-password" placeholder="••••••••"
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </Field>
        {error && <Alert>{error}</Alert>}
        <Button kind="primary" type="submit" disabled={busy}>{busy ? "Нэвтэрч байна…" : "Нэвтрэх"}</Button>
        <p className="muted small" style={{ textAlign: "center", margin: 0 }}>Нууц үгээ мартсан бол админд хандана уу</p>
      </form>
    </div>
  );
}
