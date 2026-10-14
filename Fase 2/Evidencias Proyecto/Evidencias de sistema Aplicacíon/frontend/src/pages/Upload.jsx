import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function pick(f) {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function submit(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const rec = await api("/receipts/upload", { method: "POST", body });
      navigate(`/receipts/${rec.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1>Digitalizar comprobante</h1>
      <p className="muted">JPG, PNG, WEBP o TIFF · máximo 12 MB. El pipeline restaura daño, extrae campos chilenos y deja trazas de auditoría.</p>
      <form className="card" onSubmit={submit} style={{ marginTop: 16 }}>
        <div
          className="drop"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            pick(e.dataTransfer.files[0]);
          }}
        >
          <p>Arrastre la foto del recibo o elija un archivo</p>
          <input type="file" accept="image/*" onChange={(e) => pick(e.target.files[0])} />
        </div>
        {preview && (
          <div style={{ marginTop: 18, maxWidth: 360 }}>
            <img className="thumb" src={preview} alt="Vista previa" />
          </div>
        )}
        {error && <p className="error">{error}</p>}
        <div className="row" style={{ marginTop: 16 }}>
          <button className="btn" disabled={!file || loading}>
            {loading ? "Enviando al pipeline…" : "Procesar con IA local"}
          </button>
          <button
            type="button"
            className="btn ghost"
            disabled={loading}
            onClick={async () => {
              setLoading(true);
              setError("");
              try {
                const rec = await api("/receipts/demo", { method: "POST" });
                navigate(`/receipts/${rec.id}`);
              } catch (err) {
                setError(err.message);
              } finally {
                setLoading(false);
              }
            }}
          >
            Cargar boleta de demostración
          </button>
        </div>
      </form>
    </>
  );
}
