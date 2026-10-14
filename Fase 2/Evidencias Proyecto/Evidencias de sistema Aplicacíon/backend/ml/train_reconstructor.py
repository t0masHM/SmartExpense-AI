"""Entrenamiento de un clasificador de caracteres dañados (dígitos y letras de RUT).

Genera muestras sintéticas con manchas, desenfoque y recortes, y entrena un
RandomForest sobre descriptores HOG. El modelo se usa en inferencia para
reconstruir caracteres de baja confianza en zonas deterioradas.
"""

from __future__ import annotations

import random
from pathlib import Path

import cv2
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

CHARSET = "0123456789K.-"


def _render_char(ch: str, size: int = 28) -> np.ndarray:
    img = np.full((size, size), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.85 if ch not in ".-" else 0.55
    thickness = 2 if ch not in ".-" else 1
    (w, h), _ = cv2.getTextSize(ch, font, scale, thickness)
    x = max((size - w) // 2, 0)
    y = (size + h) // 2
    cv2.putText(img, ch, (x, y), font, scale, 20, thickness, cv2.LINE_AA)
    return img


def _damage(img: np.ndarray) -> np.ndarray:
    out = img.copy()
    h, w = out.shape
    mode = random.choice(["blur", "stain", "scratch", "noise", "cut"])
    if mode == "blur":
        k = random.choice([3, 5])
        out = cv2.GaussianBlur(out, (k, k), 0)
    elif mode == "stain":
        cx, cy = random.randint(4, w - 5), random.randint(4, h - 5)
        cv2.circle(out, (cx, cy), random.randint(3, 7), int(random.randint(40, 140)), -1)
    elif mode == "scratch":
        cv2.line(
            out,
            (random.randint(0, w), random.randint(0, h)),
            (random.randint(0, w), random.randint(0, h)),
            int(random.randint(0, 80)),
            random.randint(1, 2),
        )
    elif mode == "noise":
        noise = np.random.randint(0, 80, out.shape, dtype=np.uint8)
        out = cv2.subtract(out, noise)
    else:
        x0, y0 = random.randint(0, w // 2), random.randint(0, h // 2)
        out[y0 : y0 + 8, x0 : x0 + 8] = 255
    if random.random() < 0.4:
        out = cv2.rotate(out, random.choice([cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE]))
        out = cv2.resize(out, (w, h))
    return np.clip(out, 0, 255).astype(np.uint8)


def hog_features(img: np.ndarray) -> np.ndarray:
    resized = cv2.resize(img, (28, 28), interpolation=cv2.INTER_AREA)
    gx = cv2.Sobel(resized, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(resized, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    bins = 9
    hist = np.zeros(bins, dtype=np.float32)
    cell = 7
    feats: list[np.ndarray] = []
    for y in range(0, 28, cell):
        for x in range(0, 28, cell):
            m = mag[y : y + cell, x : x + cell].ravel()
            a = ang[y : y + cell, x : x + cell].ravel()
            hist = np.zeros(bins, dtype=np.float32)
            for mag_i, ang_i in zip(m, a):
                b = int((ang_i % 180) / (180 / bins)) % bins
                hist[b] += mag_i
            feats.append(hist)
    vec = np.concatenate(feats)
    n = np.linalg.norm(vec) + 1e-6
    return (vec / n).astype(np.float32)


def train_and_save(model_path: Path, samples_per_char: int = 80) -> dict:
    X: list[np.ndarray] = []
    y: list[str] = []
    for ch in CHARSET:
        clean = _render_char(ch)
        for _ in range(samples_per_char):
            sample = _damage(clean)
            X.append(hog_features(sample))
            y.append(ch)
        X.append(hog_features(clean))
        y.append(ch)

    X_arr = np.vstack(X)
    y_arr = np.array(y)
    X_train, X_test, y_train, y_test = train_test_split(
        X_arr, y_arr, test_size=0.2, random_state=42, stratify=y_arr
    )
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=18,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    clf.fit(X_train, y_train)
    acc = float(accuracy_score(y_test, clf.predict(X_test)))
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "charset": CHARSET, "accuracy": acc}, model_path)
    return {"accuracy": acc, "samples": int(len(y_arr)), "path": str(model_path)}


if __name__ == "__main__":
    out = Path("models/char_reconstructor.joblib")
    print(train_and_save(out))
