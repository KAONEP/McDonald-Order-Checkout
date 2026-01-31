from __future__ import annotations

from typing import Any, Dict, List
from ultralytics import YOLO

MODEL_PATH = "models/best.pt"
CLASSES = ["burger", "drink", "fries", "nuggets", "sauce"]


def detect_items(image_path: str, scenario: str = "ok") -> List[Dict[str, Any]]:
    model = YOLO(MODEL_PATH)
    results = model.predict(source=image_path, conf=0.25, verbose=False)
    r = results[0]
    counts: Dict[str, int] = {c: 0 for c in CLASSES}
    if r.boxes is None or r.boxes.cls is None:
        return []

    cls_ids = r.boxes.cls.tolist()

    for cid in cls_ids:
        cid_int = int(cid)
        if 0 <= cid_int < len(CLASSES):
            cname = CLASSES[cid_int]
            counts[cname] += 1

    detected_list = [{"class": k, "count": v} for k, v in counts.items() if v > 0]
    return detected_list


