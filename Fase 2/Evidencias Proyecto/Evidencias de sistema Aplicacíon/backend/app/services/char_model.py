from __future__ import annotations

from pathlib import Path

import cv2
import joblib
import numpy as np

from app.config import get_settings
from ml.train_reconstructor import hog_features, train_and_save

_CACHE: dict | None = None


def model_file() -> Path:
    return Path(get_settings().model_dir) / "char_reconstructor.joblib"


def ensure_model() -> dict:
    global _CACHE
    path = model_file()
    if _CACHE is None:
        if not path.exists():
            train_and_save(path, samples_per_char=70)
        _CACHE = joblib.load(path)
    return _CACHE


def predict_char(patch: np.ndarray) -> tuple[str, float]:
    bundle = ensure_model()
    clf = bundle["model"]
    gray = patch if patch.ndim == 2 else cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    feats = hog_features(gray).reshape(1, -1)
    proba = clf.predict_proba(feats)[0]
    idx = int(np.argmax(proba))
    return str(clf.classes_[idx]), float(proba[idx])
