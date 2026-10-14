import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export default function Register() {
  const [form, setForm] = useState({
    full_name: "",
    company_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api("/auth/register", { method: "POST", body: JSON.stringify(form) });
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: form.email, password: form.password }),
      });
      setToken(data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <div className="brand" style={{ fontSize: 22 }}>SmartExpence-IA</div>
        <h1>Registrar empresa</h1>
        <form className="card" onSubmit={onSubmit} style={{ maxWidth: 460, marginTop: 24 }}>
          <label>Nombre</label>
          <input value={form.full_name} onChange={(e) => set("full_name", e.target.value)} required />
          <label>Empresa</label>
          <input value={form.company_name} onChange={(e) => set("company_name", e.target.value)} required />
          <label>Correo</label>
          <input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
          <label>Contraseña (mín. 8)</label>
          <input type="password" minLength={8} value={form.password} onChange={(e) => set("password", e.target.value)} required />
          {error && <p className="error">{error}</p>}
          <button className="btn" disabled={loading}>{loading ? "Creando…" : "Crear cuenta"}</button>
          <p className="muted" style={{ marginTop: 16 }}>
            ¿Ya tiene acceso? <Link to="/login">Ingresar</Link>
          </p>
        </form>
      </div>
      <aside className="auth-aside">
        <div>
          <h2>On-premise por diseño</h2>
          <p>PostgreSQL, API y frontend viven en su red. No hay telemetría ni APIs cloud obligatorias.</p>
        </div>
      </aside>
    </div>
  );
}
