import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, setToken } from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
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
        <h1>Entrar al libro local</h1>
        <p className="muted">Los comprobantes nunca salen de su infraestructura.</p>
        <form className="card" onSubmit={onSubmit} style={{ maxWidth: 460, marginTop: 24 }}>
          <label>Correo</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label>Contraseña</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <p className="error">{error}</p>}
          <button className="btn" disabled={loading}>{loading ? "Ingresando…" : "Ingresar"}</button>
          <p className="muted" style={{ marginTop: 16 }}>
            ¿Primera vez? <Link to="/register">Crear cuenta de empresa</Link>
          </p>
        </form>
      </div>
      <aside className="auth-aside">
        <div>
          <h2>Soberanía de datos financieros</h2>
          <p>
            Extrae RUT, fechas y montos incluso de recibos borrosos o rasgados. El modelo de
            reconstrucción y el OCR corren en contenedores locales.
          </p>
          <div className="chip-row">
            <span className="chip">Docker Compose</span>
            <span className="chip">OCR + inpaint</span>
            <span className="chip">Excel de auditoría</span>
          </div>
        </div>
        <p style={{ fontSize: 13, color: "#d7c9aa" }}>Proyecto APT · perfil Full-Stack e infraestructura</p>
      </aside>
    </div>
  );
}
