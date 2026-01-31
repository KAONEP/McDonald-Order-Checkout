# src/vision_mock.py

from __future__ import annotations
from typing import List, Dict, Any


def detect_items(image_path: str, scenario: str = "ok") -> List[Dict[str, Any]]:
    """
    Mock 检测器：不读图片内容，通过 scenario 控制返回值
    scenario:
      - ok: 全都齐
      - missing_item: 缺 fries
      - missing_sauce: 有 nuggets 但缺 sauce
    """
    base = [
        {"class": "burger", "count": 1},
        {"class": "fries", "count": 1},
        {"class": "drink", "count": 1},
        {"class": "nuggets", "count": 1},
        {"class": "sauce", "count": 1},
    ]

    if scenario == "ok":
        return base

    if scenario == "missing_item":
        return [x for x in base if x["class"] != "fries"]

    if scenario == "missing_sauce":
        return [x for x in base if x["class"] != "sauce"]

    # 默认当 ok
    return base
