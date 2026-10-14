from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class RestorationResult:
    restored: np.ndarray
    mask: np.ndarray
    damage_score: float
    notes: list[str]


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def estimate_blur(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def build_damage_mask(gray: np.ndarray) -> tuple[np.ndarray, list[str]]:
    notes: list[str] = []
    h, w = gray.shape
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Manchas oscuras / tinta corrida
    dark = cv2.threshold(blur, 55, 255, cv2.THRESH_BINARY_INV)[1]
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    # Zonas quemadas o sobreexpuestas
    bright = cv2.threshold(blur, 245, 255, cv2.THRESH_BINARY)[1]

    # Bordes rotos / arrugas (gradiente alto anómalo en bloques)
    mag = cv2.Sobel(blur, cv2.CV_32F, 1, 1, ksize=3)
    mag = cv2.convertScaleAbs(mag)
    wrinkles = cv2.threshold(mag, 90, 255, cv2.THRESH_BINARY)[1]
    wrinkles = cv2.dilate(wrinkles, np.ones((2, 2), np.uint8), iterations=1)

    mask = cv2.bitwise_or(dark, bright)
    mask = cv2.bitwise_or(mask, wrinkles)

    # Recortes en márgenes (papel rasgado)
    border = np.zeros_like(gray)
    edge = 8
    for region in (gray[:edge, :], gray[-edge:, :], gray[:, :edge], gray[:, -edge:]):
        if region.size and float(region.mean()) < 40:
            notes.append("margen rasgado o sombreado")
            break
    if float(gray[:edge, :].mean()) < 45:
        border[:edge, :] = 255
    if float(gray[-edge:, :].mean()) < 45:
        border[-edge:, :] = 255
    mask = cv2.bitwise_or(mask, border)

    coverage = float(np.count_nonzero(mask)) / float(mask.size)
    if coverage > 0.35:
        mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=1)
        notes.append("máscara recortada para no borrar texto válido")
    if coverage > 0.02:
        notes.append("se detectaron manchas, brillos o arrugas")
    blur_var = estimate_blur(gray)
    if blur_var < 80:
        notes.append("imagen borrosa: se aplica nitidez previa a OCR")
    return mask, notes


def deskew(gray: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(gray < 200))
    if len(coords) < 50:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.4 or abs(angle) > 20:
        return gray
    h, w = gray.shape
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC, borderValue=255)


def restore_image(image: np.ndarray) -> RestorationResult:
    gray = _to_gray(image)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    mask, notes = build_damage_mask(gray)
    restored = gray.copy()
    if np.count_nonzero(mask) > 20:
        restored = cv2.inpaint(gray, mask, 3, cv2.INPAINT_TELEA)
        notes.append("inpaint Telea sobre píxeles dañados")
    restored = deskew(restored)
    blur_var = estimate_blur(restored)
    if blur_var < 90:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        restored = cv2.filter2D(restored, -1, kernel)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    restored = clahe.apply(restored)
    binary = cv2.adaptiveThreshold(
        restored, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12
    )
    damage_score = round(min(1.0, float(np.count_nonzero(mask)) / (mask.size * 0.25)), 3)
    color = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    mask_bgr = cv2.applyColorMap(mask, cv2.COLORMAP_HOT)
    return RestorationResult(restored=color, mask=mask_bgr, damage_score=damage_score, notes=notes)
