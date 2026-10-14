import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, money, pct } from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [rows, setRows] = useState([]);

  useEffect(() => {
    api("/receipts/stats").then(setStats);
    api("/receipts").then((data) => setRows(data.slice(0, 6)));
  }, []);

  async function downloadExcel() {
    const res = await api("/reports/excel");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "capton_reporte_contable.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <div className="topbar">
        <div>
          <h1 style={{ margin: 0 }}>Tablero contable</h1>
          <p className="muted">Extracción local, reconstrucción de daño y cuadratura lista para auditoría.</p>
        </div>
        <div className="row">
          <Link className="btn secondary" to="/upload">Subir imagen</Link>
          <button className="btn" onClick={downloadExcel}>Exportar Excel</button>
        </div>
      </div>
      <section className="stats">
        <article className="stat">
          <span className="muted">Comprobantes</span>
          <b>{stats?.total_receipts ?? "—"}</b>
        </article>
        <article className="stat">
          <span className="muted">Total detectado</span>
          <b>{money(stats?.total_amount)}</b>
        </article>
        <article className="stat">
          <span className="muted">Confianza OCR</span>
          <b>{pct(stats?.avg_confidence)}</b>
        </article>
        <article className="stat">
          <span className="muted">Daño medio</span>
          <b>{pct(stats?.avg_damage)}</b>
        </article>
      </section>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Últimos documentos</h3>
        {rows.length === 0 && <p className="muted">Aún no hay cargas. Suba una foto de boleta o factura.</p>}
        {rows.map((r) => (
          <div key={r.id} className="row" style={{ justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <div>
              <strong>{r.merchant || r.original_filename}</strong>
              <div className="muted">{r.rut_emisor || "RUT no detectado"} · {r.issued_at || "sin fecha"}</div>
            </div>
            <div className="row">
              <span className={`badge ${r.status}`}>{r.status}</span>
              <span>{money(r.total_amount)}</span>
              <Link to={`/receipts/${r.id}`}>Ver</Link>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
