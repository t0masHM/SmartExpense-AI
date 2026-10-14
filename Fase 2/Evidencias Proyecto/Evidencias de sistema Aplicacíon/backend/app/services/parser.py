from __future__ import annotations

import re
from datetime import datetime
from typing import Any

RUT_RE = re.compile(r"\b(\d{1,2}(?:\.?\d{3}){2}-[\dkK])\b")
RUT_LOOSE = re.compile(r"\b(\d{7,8}-[\dkK])\b")
DATE_RE = re.compile(
    r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
)
MONEY_RE = re.compile(r"\$?\s*(\d{1,3}(?:[.\s]\d{3})+(?:,\d{1,2})?|\d+(?:,\d{2}))")
FOLIO_RE = re.compile(
    r"(?:folio|n[°ºo.]|nro|num(?:ero)?|boleta|factura)[^\d]{0,24}(\d{3,12})",
    re.I,
)


def rut_dv(body: str) -> str:
    digits = [int(c) for c in body if c.isdigit()][::-1]
    factors = [2, 3, 4, 5, 6, 7]
    total = sum(d * factors[i % 6] for i, d in enumerate(digits))
    rest = 11 - (total % 11)
    if rest == 11:
        return "0"
    if rest == 10:
        return "K"
    return str(rest)


def normalize_rut(value: str) -> str | None:
    clean = re.sub(r"[^0-9kK]", "", value).upper()
    if len(clean) < 8:
        return None
    body, dv = clean[:-1], clean[-1]
    if not body.isdigit():
        return None
    expected = rut_dv(body)
    formatted = f"{int(body):,}".replace(",", ".") + f"-{expected}"
    if dv != expected:
        return formatted
    return f"{int(body):,}".replace(",", ".") + f"-{dv}"


def repair_rut(value: str) -> tuple[str | None, str | None]:
    """Corrige o completa el dígito verificador de un RUT chileno (módulo 11)."""
    clean = re.sub(r"[^0-9kK]", "", value).upper()
    digits = "".join(c for c in clean if c.isdigit())
    if len(clean) >= 2 and clean[-1] in "0123456789K":
        body = clean[:-1]
        if body.isdigit() and 7 <= len(body) <= 8:
            expected = rut_dv(body)
            formatted = normalize_rut(body + expected)
            if clean[-1] != expected:
                return formatted, f"DV RUT corregido a {expected} (módulo 11)"
            return formatted, None
    if 7 <= len(digits) <= 8:
        expected = rut_dv(digits)
        return normalize_rut(digits + expected), f"DV RUT inferido ({expected}) por módulo 11"
    return normalize_rut(value), None


def _to_float(raw: str) -> float | None:
    txt = raw.replace(" ", "").replace("$", "")
    if "," in txt and "." in txt:
        txt = txt.replace(".", "").replace(",", ".")
    elif "," in txt:
        parts = txt.split(",")
        if len(parts[-1]) <= 2:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", "")
    else:
        if txt.count(".") > 1:
            txt = txt.replace(".", "")
    try:
        return round(float(txt), 2)
    except ValueError:
        return None


def _normalize_date(raw: str) -> str | None:
    raw = raw.replace(".", "/")
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _guess_merchant(text: str) -> str | None:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    skip = re.compile(r"^(rut|giro|boleta|factura|fecha|total|iva|neto)", re.I)
    for line in lines[:8]:
        if skip.search(line):
            continue
        if len(line) >= 4 and not re.fullmatch(r"[\d\s\.\-,\$]+", line):
            return line[:120]
    return lines[0][:120] if lines else None


def _doc_type(text: str) -> str:
    lower = text.lower()
    if "factura electronica" in lower or "factura electrónica" in lower:
        return "Factura electrónica"
    if "factura" in lower:
        return "Factura"
    if "boleta electronica" in lower or "boleta electrónica" in lower:
        return "Boleta electrónica"
    if "boleta" in lower:
        return "Boleta"
    return "Comprobante"


def parse_chilean_receipt(text: str) -> dict[str, Any]:
    notes: list[str] = []
    ruts = [m.group(1) for m in RUT_RE.finditer(text)]
    ruts += [m.group(1) for m in RUT_LOOSE.finditer(text)]
    normalized: list[str] = []
    for rut in ruts:
        value, note = repair_rut(rut)
        if value and value not in normalized:
            normalized.append(value)
            if note:
                notes.append(note)

    dates = []
    for match in DATE_RE.finditer(text):
        parsed = _normalize_date(match.group(1))
        if parsed:
            dates.append(parsed)

    amounts: list[float] = []
    for match in MONEY_RE.finditer(text):
        val = _to_float(match.group(1))
        if val and val >= 1:
            amounts.append(val)

    folio = None
    fm = FOLIO_RE.search(text)
    if fm:
        folio = fm.group(1)

    total = max(amounts) if amounts else None
    net = None
    tax = None
    lower = text.lower()
    if "iva" in lower and amounts:
        for a in sorted(amounts, reverse=True):
            if total and abs(a - total / 1.19) < max(2.0, total * 0.02):
                net = round(total / 1.19, 2)
                tax = round(total - net, 2)
                notes.append("IVA 19% inferido desde el total")
                break
    if total and net is None:
        maybe_net = [a for a in amounts if a < total]
        if maybe_net:
            net = max(maybe_net)
            tax = round(total - net, 2) if total >= net else None

    if total and net and tax is None:
        tax = round(total - net, 2)
    if net and tax and total is None:
        total = round(net + tax, 2)
        notes.append("total reconstruido como neto + IVA")
    if total and tax and net is None:
        net = round(total - tax, 2)

    return {
        "document_type": _doc_type(text),
        "merchant": _guess_merchant(text),
        "rut_emisor": normalized[0] if normalized else None,
        "rut_receptor": normalized[1] if len(normalized) > 1 else None,
        "folio": folio,
        "issued_at": dates[0] if dates else None,
        "net_amount": net,
        "tax_amount": tax,
        "total_amount": total,
        "parse_notes": notes,
        "amounts_detected": amounts[:12],
        "ruts_detected": normalized,
    }
