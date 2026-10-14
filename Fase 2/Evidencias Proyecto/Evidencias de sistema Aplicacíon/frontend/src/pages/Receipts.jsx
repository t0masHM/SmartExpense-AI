import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, money } from "../api";

export default function Receipts() {
  const [rows, setRows] = useState([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");

  async function load(query = q, st = status) {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (st) params.set("status", st);
    const qs = params.toString();
    setRows(await api(`/receipts${qs ? `?${qs}` : ""}`));
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div className="topbar">
        <div>
          <h1 style={{ margin: 0 }}>Libro de gastos</h1>
          <p className="muted">Busque por comercio, RUT, folio o archivo.</p>
        </div>
      </div>
      <div className="row" style={{ marginBottom: 16 }}>
        <input style={{ maxWidth: 280 }} placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select style={{ maxWidth: 180 }} value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">Todos los estados</option>
          <option value="pending">pending</option>
          <option value="processing">processing</option>
          <option value="done">done</option>
          <option value="failed">failed</option>
        </select>
        <button className="btn ghost" onClick={() => load()}>Filtrar</button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Comercio</th>
              <th>RUT</th>
              <th>Fecha</th>
              <th>Total</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.merchant || r.original_filename}</td>
                <td>{r.rut_emisor || "—"}</td>
                <td>{r.issued_at || "—"}</td>
                <td>{money(r.total_amount)}</td>
                <td><span className={`badge ${r.status}`}>{r.status}</span></td>
                <td><Link to={`/receipts/${r.id}`}>Abrir</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
