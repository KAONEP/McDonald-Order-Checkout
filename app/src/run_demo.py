from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime
from .vision_yolo import detect_items
from .compare import compare_with_rules


def load_order(order_path: Path) -> dict:
    data = json.loads(order_path.read_text(encoding="utf-8"))

    if "items" not in data or not isinstance(data["items"], dict):
        raise ValueError("order json must contain { 'items': { ... } }")

    data["items"] = {k: int(v) for k, v in data["items"].items()}
    return data


def pretty_print(order_items: dict, detected_items: dict, result: dict):
    # 注文内容（本来あるべきもの）
    print("\n[注文内容]:", order_items)

    # 検出結果（実際に検出されたもの）
    print("[検出結果]:", detected_items)

    print("\n[判定結果]")

    # 不足・余分情報の取得
    missing = result.get("missing", {})
    extra = result.get("extra", {})

    # 不足の表示
    if missing:
        for name, count in missing.items():
            print(f"- 不足: {name} ×{count}")
    else:
        print("- 不足: なし")

    # 余分の表示
    if extra:
        for name, count in extra.items():
            print(f"- 余分: {name} ×{count}")
    else:
        print("- 余分: なし")

    # 最終判定
    status = "✅ 一致" if not missing and not extra else "❌ 不一致"
    print(f"- 判定: {status}")


def main():
    # コマンドライン引数定義
    parser = argparse.ArgumentParser()
    parser.add_argument("--order", required=True, help="例: orders/order_001.json")
    parser.add_argument("--image", required=True, help="例: demo_images/test_001.jpg")
    parser.add_argument(
        "--scenario",
        default="ok",
        choices=["ok", "missing_item", "missing_sauce"],
        help="mock用：検出結果のシナリオ制御"
    )
    args = parser.parse_args()

    # プロジェクトルート取得（app/）
    root = Path(__file__).resolve().parents[1]

    # パス解決
    order_path = (root / args.order).resolve()
    image_path = (root / args.image).resolve()

    # 注文読み込み
    order = load_order(order_path)
    order_items = order["items"]

    # 物体検出の実行
    detected_items = detect_items(str(image_path), scenario=args.scenario)

    # 注文と検出結果の比較
    result = compare_with_rules(order_items, detected_items)

    # ===== 人間向け出力（簡潔） =====
    pretty_print(order_items, detected_items, result)

    # ===== 機械向け出力（JSON） =====
    out = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "order_file": str(order_path),
        "image_file": str(image_path),
        "scenario": args.scenario,
        "order_items": order_items,
        "detected_items": detected_items,
        "result": result,
    }

    # 出力ディレクトリ作成
    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 結果保存
    out_name = f"{order_path.stem}__{args.scenario}.result.json"
    (outputs_dir / out_name).write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n[INFO] 結果JSON保存先: {outputs_dir / out_name}")


if __name__ == "__main__":
    main()
