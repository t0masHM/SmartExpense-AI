from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def render_demo_boleta() -> bytes:
    img = Image.new("RGB", (700, 980), "#f6f1e6")
    draw = ImageDraw.Draw(img)
    draw.rectangle((24, 24, 676, 956), outline="#1c1915", width=3)

    title = _font(28)
    body = _font(22)
    small = _font(18)
    lines = [
        (title, 70, "MINIMARKET LOS ALERCES SPA"),
        (small, 118, "GIRO: Abarrotes y minimarket"),
        (body, 168, "RUT: 76.543.210-K"),
        (body, 218, "BOLETA ELECTRONICA N 45821"),
        (body, 268, "Fecha: 01/09/2026"),
        (body, 318, "RUT cliente: 12.345.678-5"),
        (small, 368, "--------------------------------"),
        (body, 418, "Pan amasado          $ 1.200"),
        (body, 468, "Leche 1L             $ 1.450"),
        (body, 518, "Cafe molido          $ 4.990"),
        (small, 568, "--------------------------------"),
        (body, 618, "NETO                 $ 6.420"),
        (body, 668, "IVA 19%              $ 1.220"),
        (title, 728, "TOTAL                $ 7.640"),
    ]
    for font, y, text in lines:
        draw.text((50, y), text, fill="#1c1915", font=font)

    draw.ellipse((480, 150, 575, 245), fill="#3a3a3a")
    draw.line((70, 400, 640, 445), fill="#6a6a6a", width=8)
    draw.rectangle((0, 900, 90, 980), fill="#141414")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
