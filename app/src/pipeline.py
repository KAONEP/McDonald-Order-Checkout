from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, Any

from .vision_yolo import detect_items
from .compare import compare_with_rules


def load_order(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "items" not in data or not isinstance(data["items"], dict):
        raise ValueError("order json must contain { 'items': { ... } }")

    return {k: int(v) for k, v in data["items"].items()}


def run_pipeline(order_items: dict, image_path: str) -> Dict[str, Any]:
    detected_items, vis_path = detect_items(
        image_path,
        save_vis=True,
        vis_dir="outputs/vis",
        conf=0.25,
    )

    result = compare_with_rules(order_items, detected_items)

    return {
        "order": order_items,
        "detected": detected_items,
        "result": result,
        "vis_image": vis_path,
    }
