from __future__ import annotations

from typing import Any, Dict, List, Tuple
from pathlib import Path

import cv2
from ultralytics import YOLO

# =====================
MODEL_PATH = "models/best.pt"
CLASSES = ["burger", "drink", "fries", "nuggets", "sauce"]
# =====================


def detect_items(
    image_path: str,
    *,
    save_vis: bool = False,
    vis_dir: str = "outputs/vis",
    conf: float = 0.25,
) -> Tuple[List[Dict[str, Any]], str | None]:
    """
    物体検出を行い、商品ごとの個数を返す。
    オプションで、バウンディングボックス付き画像を保存する。

    Returns
    -------
    detected_list : List[Dict[str, Any]]
        例: [{"class": "burger", "count": 2}, ...]
    vis_path : str | None
        可視化画像の保存パス（save_vis=False の場合は None）
    """

    model = YOLO(MODEL_PATH)
    results = model.predict(source=image_path, conf=conf, verbose=False)
    r = results[0]

    # -------- 集計 --------
    counts: Dict[str, int] = {c: 0 for c in CLASSES}

    if r.boxes is not None and r.boxes.cls is not None:
        for cid in r.boxes.cls.tolist():
            cid_int = int(cid)
            if 0 <= cid_int < len(CLASSES):
                cname = CLASSES[cid_int]
                counts[cname] += 1

    detected_list = [
        {"class": k, "count": v}
        for k, v in counts.items()
        if v > 0
    ]

    # -------- 可視化保存 --------
    vis_path: str | None = None

    if save_vis:
        out_dir = Path(vis_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(image_path).stem
        vis_path = str(out_dir / f"{stem}_detected.jpg")

        # YOLO が描画した ndarray（BGR）を取得
        annotated = r.plot()
        cv2.imwrite(vis_path, annotated)

    return detected_list, vis_path


