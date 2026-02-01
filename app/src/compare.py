from __future__ import annotations
from typing import Dict, List, Any
from .rules import DEPENDENCIES, RULE_DESCRIPTIONS


def list_to_count_map(detected_items: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    detected_items: [{"class":"burger","count":1}, ...]
    -> {"burger":1, ...}
    """
    m: Dict[str, int] = {}
    for it in detected_items:
        cls = str(it["class"])
        cnt = int(it.get("count", 1))
        m[cls] = m.get(cls, 0) + cnt
    return m


def compare_with_rules(order_items: Dict[str, int], detected_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    order_items: {"burger":1,"fries":1,"drink":1,"nuggets":1}
    detected_items: [{"class":"burger","count":1}, ...]
    """
    detected_map = list_to_count_map(detected_items)

    result = {
        "missing": {},        # 常规缺失（订单里有，但检测少）
        "extra": {},          # 常规多出（订单里有，但检测多）
        "rule_missing": {},   # 规则缺失（如 nuggets_sauce）
        "notes": []           # 备注说明
    }

    # 1) 常规对比：只比订单里出现的项
    for cls, need in order_items.items():
        need = int(need)
        got = int(detected_map.get(cls, 0))
        if got < need:
            result["missing"][cls] = need - got
        elif got > need:
            result["extra"][cls] = got - need

    # 2) 规则检查：nuggets -> sauce
    for parent, deps in DEPENDENCIES.items():
        parent_need = int(order_items.get(parent, 0))
        if parent_need <= 0:
            continue

        for dep_cls, dep_per_parent in deps.items():
            dep_need = parent_need * int(dep_per_parent)
            dep_got = int(detected_map.get(dep_cls, 0))
            if dep_got < dep_need:
                result["rule_missing"][dep_cls] = dep_need - dep_got
                desc = RULE_DESCRIPTIONS.get(parent)
                if desc and desc not in result["notes"]:
                    result["notes"].append(desc)

    return result
