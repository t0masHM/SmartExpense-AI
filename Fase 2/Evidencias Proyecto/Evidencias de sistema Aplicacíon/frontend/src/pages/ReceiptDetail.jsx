import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, getToken, money, pct } from "../api";

function AuthImage({ receiptId, kind, alt }) {
  const [src, setSrc] = useState("");
  useEffect(() => {
    let url;
    async function load() {
      const res = await fetch(`/api/receipts/${receiptId}/image?kind=${kind}`, {
        headers: { Authorization: "Bearer " + getToken() },
      });
      if (!res.ok) return;
      const blob = await res.blob();
      url = URL.createObjectURL(blob);
      setSrc(url);
    }
    load();
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [receiptId, kind]);
  if (!src) return <div className="muted">Sin imagen</div>;
  return <img src={src} alt={alt} />;
}

export default function ReceiptDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [rec, setRec] = useState(null);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  async function load() {
    try {
      setRec(await api(`/receipts/${id}`));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function reprocess() {
    setRec(await api(`/receipts/${id}/reprocess`, { method: "POST" }));
  }

  async function remove() {
    if (!confirm("¿Eliminar este comprobante?")) return;
    await api(`/receipts/${id}`, { method: "DELETE" });
    navigate("/receipts");
  }

  async function exportGeneratedReceiptPdf() {
    setExporting(true);
    setExportError("");
    try {
      const { jsPDF } = await import("jspdf");
      const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: [90, 220] });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const ticketX = 5;
      const ticketWidth = pageWidth - ticketX * 2;
      let y = 14;
      const addSeparator = () => {
        pdf.setDrawColor(150);
        pdf.setLineDashPattern([1, 1], 0);
        pdf.line(ticketX + 6, y, ticketX + ticketWidth - 6, y);
        pdf.setLineDashPattern([], 0);
        y += 5;
      };
      const addDetail = (label, value, bold = false) => {
        pdf.setFont("helvetica", "normal");
        pdf.setFontSize(8);
        pdf.setTextColor(100);
        pdf.text(label, ticketX + 7, y);
        y += 4;
        pdf.setFont("helvetica", bold ? "bold" : "normal");
        pdf.setFontSize(bold ? 11 : 10);
        pdf.setTextColor(35);
        const lines = pdf.splitTextToSize(value || "No identificado", ticketWidth - 14);
        pdf.text(lines, ticketX + 7, y);
        y += lines.length * 4.5 + 3;
      };
      const formattedDate = rec.issued_at
        ? new Date(`${rec.issued_at}T00:00:00`).toLocaleDateString("es-CL")
        : null;

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(14);
      pdf.setTextColor(31, 61, 43);
      pdf.text("BOLETA RECREADA", pageWidth / 2, y, { align: "center" });
      y += 7;
      pdf.setFontSize(12);
      const merchantLines = pdf.splitTextToSize(rec.merchant || "Comercio no identificado", ticketWidth - 14);
      pdf.text(merchantLines, pageWidth / 2, y, { align: "center" });
      y += merchantLines.length * 5 + 1;
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(9);
      pdf.setTextColor(90);
      pdf.text(rec.document_type || "Comprobante", pageWidth / 2, y, { align: "center" });
      y += 7;
      addSeparator();

      addDetail("RUT EMISOR", rec.rut_emisor);
      addDetail("FOLIO", rec.folio);
      addDetail("FECHA", formattedDate);
      addDetail("RUT RECEPTOR", rec.rut_receptor);
      addSeparator();

      addDetail("NETO", rec.net_amount == null ? null : money(rec.net_amount));
      addDetail("IVA", rec.tax_amount == null ? null : money(rec.tax_amount));
      addDetail("TOTAL", rec.total_amount == null ? null : money(rec.total_amount), true);
      addSeparator();
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(7);
      pdf.setTextColor(100);
      const disclaimer = pdf.splitTextToSize(
        "Recreación generada con los datos reconocidos de la imagen. No reemplaza la boleta tributaria original.",
        ticketWidth - 14
      );
      pdf.text(disclaimer, pageWidth / 2, y, { align: "center" });
      y += disclaimer.length * 3.5 + 5;

      pdf.setDrawColor(190);
      pdf.setLineDashPattern([], 0);
      pdf.roundedRect(ticketX, 7, ticketWidth, y - 2, 2, 2);
      const filename = (rec.merchant || "boleta")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "") || "boleta";
      pdf.save(`${filename}-recreada.pdf`);
      setExporting(false);
    } catch (err) {
      setExportError(err.message || "No se pudo descargar la boleta PDF.");
      setExporting(false);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!rec) return <p className="muted">Cargando pipeline…</p>;

  const fields = [
    ["Tipo", rec.document_type],
    ["Comercio", rec.merchant],
    ["RUT emisor", rec.rut_emisor],
    ["RUT receptor", rec.rut_receptor],
    ["Folio", rec.folio],
    ["Fecha", rec.issued_at],
    ["Neto", money(rec.net_amount)],
    ["IVA", money(rec.tax_amount)],
    ["Total", money(rec.total_amount)],
    ["Confianza", pct(rec.confidence)],
    ["Daño", pct(rec.damage_score)],
  ];

  return (
    <>
      <div className="topbar">
        <div>
          <Link to="/receipts">← Libro</Link>
          <h1 style={{ margin: "8px 0 0" }}>{rec.merchant || rec.original_filename}</h1>
          <p className="muted">{rec.original_filename} · <span className={`badge ${rec.status}`}>{rec.status}</span></p>
        </div>
        <div className="row">
          <button
            className="btn"
            onClick={exportGeneratedReceiptPdf}
            disabled={rec.status !== "done" || exporting}
            title={rec.status === "done" ? "Descargar una boleta nueva con los datos extraídos" : "Espere a que termine la extracción de datos"}
          >
            {exporting ? "Generando PDF…" : "Descargar boleta PDF"}
          </button>
          <button className="btn ghost" onClick={reprocess}>Reprocesar</button>
          <button className="btn danger" onClick={remove}>Eliminar</button>
        </div>
      </div>

      {exportError && <p className="error" role="alert">{exportError}</p>}
      {rec.error_message && <p className="error">{rec.error_message}</p>}
      {rec.reconstruction_notes && (
        <div className="card" style={{ marginBottom: 18 }}>
          <strong>Trazas de reconstrucción</strong>
          <p className="muted">{rec.reconstruction_notes}</p>
        </div>
      )}

      <div className="compare" style={{ marginBottom: 20 }}>
        <div>
          <small className="muted">Original</small>
          <AuthImage receiptId={id} kind="original" alt="original" />
        </div>
        <div>
          <small className="muted">Restaurado</small>
          {rec.has_restored ? <AuthImage receiptId={id} kind="restored" alt="restaurado" /> : <p className="muted">En proceso…</p>}
        </div>
        <div>
          <small className="muted">Máscara de daño</small>
          {rec.has_mask ? <AuthImage receiptId={id} kind="mask" alt="máscara" /> : <p className="muted">En proceso…</p>}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <h3 style={{ marginTop: 0 }}>Campos extraídos</h3>
        <div className="fields">
          {fields.map(([k, v]) => (
            <div className="field" key={k}>
              <small>{k}</small>
              <strong>{v || "—"}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Texto OCR</h3>
        <pre className="raw">{rec.raw_text || "Aún no hay texto. Si el estado es pending, espere unos segundos."}</pre>
      </div>
    </>
  );
}
