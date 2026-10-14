from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict

import cv2
import numpy as np
import pytesseract

from app.services.char_model import predict_char


@dataclass
class OcrResult:
    text: str
    mean_confidence: float
    reconstructed_chars: int
    boxes: list[dict]


def run_ocr(image: np.ndarray) -> OcrResult:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if image.ndim == 3 else image
    data = pytesseract.image_to_data(
        rgb,
        lang="spa+eng",
        config="--oem 3 --psm 6",
        output_type=pytesseract.Output.DICT,
    )
    confs: list[float] = []
    boxes: list[dict] = []
    reconstructed = 0
    lines: dict[tuple[int, int], list[tuple[int, str]]] = defaultdict(list)

    n = len(data["text"])
    for i in range(n):
        raw = (data["text"][i] or "").strip()
        if not raw:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        x, y, w, h = int(data["left"][i]), int(data["top"][i]), int(data["width"][i]), int(data["height"][i])
        token = raw
        if 0 <= conf < 55 and w > 8 and h > 8:
            patch = rgb[max(y, 0) : y + h, max(x, 0) : x + w]
            if patch.size:
                repaired: list[str] = []
                step = max(w // max(len(raw), 1), 8)
                gray_patch = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY) if patch.ndim == 3 else patch
                for idx, ch in enumerate(raw):
                    x0 = min(idx * step, max(gray_patch.shape[1] - 8, 0))
                    slice_img = gray_patch[:, x0 : x0 + step] if step > 4 else gray_patch
                    pred, pconf = predict_char(slice_img)
                    if pconf >= 0.35 and (not ch.isalnum() or pconf > 0.5):
                        repaired.append(pred)
                        reconstructed += 1
                    else:
                        repaired.append(ch)
                token = "".join(repaired)
        block = int(data.get("block_num", [0])[i])
        line = int(data.get("line_num", [0])[i])
        lines[(block, line)].append((x, token))
        if conf >= 0:
            confs.append(conf)
        boxes.append({"text": token, "conf": conf, "x": x, "y": y, "w": w, "h": h})

    ordered_lines = []
    for key in sorted(lines):
        parts = sorted(lines[key], key=lambda item: item[0])
        ordered_lines.append(" ".join(p[1] for p in parts))
    text = "\n".join(ordered_lines) if ordered_lines else " ".join(b["text"] for b in boxes)

    mean_conf = float(np.mean(confs) / 100.0) if confs else 0.0
    return OcrResult(
        text=text,
        mean_confidence=round(mean_conf, 3),
        reconstructed_chars=reconstructed,
        boxes=boxes,
    )
