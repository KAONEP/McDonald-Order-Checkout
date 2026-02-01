from __future__ import annotations
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import streamlit as st

from app.src.pipeline import load_order, run_pipeline

DEFAULT_ITEM_KEYS = ["burger", "fries", "drink", "nuggets"]

# ========= Helpers =========
def items_dict_to_df(items: Dict[str, int]) -> pd.DataFrame:
    """{"burger":1, ...} -> DataFrame(item,count)"""
    rows = [{"item": k, "count": int(v)} for k, v in items.items()]
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["item", "count"])
    df = df.sort_values(["count", "item"], ascending=[False, True]).reset_index(drop=True)
    return df


def detected_list_to_df(detected: List[Dict[str, Any]]) -> pd.DataFrame:
    """[{'class':'burger','count':1}, ...] -> DataFrame(item,count)"""
    rows = [{"item": x.get("class", ""), "count": int(x.get("count", 0))} for x in detected]
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["item", "count"])
    df = df.sort_values(["count", "item"], ascending=[False, True]).reset_index(drop=True)
    return df


def diff_to_df(missing: Dict[str, int], extra: Dict[str, int], rule_missing: Dict[str, int]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    def add_rows(d: Dict[str, int], kind: str):
        for k, v in d.items():
            rows.append({"type": kind, "item": k, "count": int(v)})

    add_rows(missing or {}, "不足")
    add_rows(extra or {}, "余分")
    add_rows(rule_missing or {}, "ルール不足")

    if not rows:
        rows = [{"type": "-", "item": "-", "count": 0}]

    df = pd.DataFrame(rows)
    df = df.sort_values(["type", "count", "item"], ascending=[True, False, True]).reset_index(drop=True)
    return df


def summarize_counts(d: Dict[str, int]) -> int:
    return int(sum(d.values())) if d else 0

def normalize_order(raw: Any) -> Dict[str, int]:
    if isinstance(raw, dict) and "items" in raw and isinstance(raw["items"], dict):
        return {k: int(v) for k, v in raw["items"].items()}
    if isinstance(raw, dict):
        return {k: int(v) for k, v in raw.items()}
    raise ValueError("注文JSONの形式が正しくありません。dict形式、または items フィールドを含む必要があります。")

# ========= App =========
def main() -> None:
    st.set_page_config(page_title="MCD Checkout Demo", layout="wide")
    st.title("🍟 McDonald Checkout Demo YOLO26")

    ROOT = Path(__file__).resolve().parent

    candidates_orders = [
        ROOT / "app" / "orders",
    ]
    candidates_images = [
        ROOT / "app" / "demo_images",
    ]

    ORDERS_DIR = next((p for p in candidates_orders if p.exists()), None)
    IMAGES_DIR = next((p for p in candidates_images if p.exists()), None)

    if ORDERS_DIR is None:
        st.error("orders ディレクトリが見つかりません。app/orders または orders が存在するか確認してください。")
        st.stop()

    # ===== Sidebar =====
    st.sidebar.header("🧾 注文")
    order_source = st.sidebar.radio("Order選択", ["demoを選択", "入力"], index=0)

    order_items: Dict[str, int] = {}

    if order_source == "demoを選択":
        if ORDERS_DIR is None:
            st.sidebar.error(
                "orders ディレクトリが見つかりません。app/orders または orders が存在するか確認してください。")
            st.stop()

        order_files = sorted(ORDERS_DIR.glob("*.json"))
        if not order_files:
            st.sidebar.error(f"{ORDERS_DIR} 内に .json の注文ファイルが見つかりません。")
            st.stop()

        order_path = st.sidebar.selectbox(
            "注文JSON",
            order_files,
            format_func=lambda p: p.name,
        )

        try:
            raw_order = load_order(Path(order_path))
            order_items = normalize_order(raw_order)
        except Exception as e:
            st.sidebar.error(f"注文JSONの読み込みに失敗しました: {e}")
            st.stop()

        st.sidebar.markdown("### 注文内容（プレビュー）")
        st.sidebar.dataframe(items_dict_to_df(order_items), use_container_width=True, hide_index=True)

    else:
        st.sidebar.markdown("### 注文内容（入力）")
        cols = st.sidebar.columns(2)
        for i, key in enumerate(DEFAULT_ITEM_KEYS):
            with cols[i % 2]:
                order_items[key] = int(
                    st.number_input(key, min_value=0, max_value=20, value=0, step=1, key=f"manual_{key}")
                )

        st.sidebar.markdown("#### 任意項目（必要なら）")
        custom_key = st.sidebar.text_input("item key（クラス名と一致）", value="")
        custom_count = st.sidebar.number_input("count", min_value=0, max_value=20, value=0, step=1)
        if custom_key.strip():
            order_items[custom_key.strip()] = int(custom_count)

        st.sidebar.markdown("### 注文内容（プレビュー）")
        st.sidebar.dataframe(items_dict_to_df({k: v for k, v in order_items.items() if v > 0}),
                             use_container_width=True, hide_index=True)

        # （任意）保存ボタン：テスト者が orders/ に放り込みたい時用
        if ORDERS_DIR is not None:
            if st.sidebar.button("💾 この注文を orders/ に保存"):
                try:
                    fname = st.sidebar.text_input("file name", value="order_manual.json", key="save_name")
                    # 入力欄が上のボタン後に出ると扱いにくいので、実用上は固定名でもOK
                except Exception:
                    pass
            # ↑この “保存UI” は操作が面倒になりやすいので、必要なら俺が別途綺麗にする。
        else:
            st.sidebar.caption("orders ディレクトリが未設定のため保存はできません（手入力のまま判定できます）。")
    # ===== Image Input =====
    st.header("📷 Input Image")

    # ===== 选择方式 =====
    image_path: str | None = None

    uploaded = st.file_uploader(
        "Upload tray image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded is not None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp.write(uploaded.getbuffer())
        tmp.close()
        image_path = tmp.name

    st.markdown("**Or choose demo image**")

    if IMAGES_DIR is not None:
        demo_images = [
            p for p in sorted(IMAGES_DIR.glob("*.*"))
            if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
        ]
        demo_choice = st.selectbox(
            "Demo image",
            ["(none)"] + [p.name for p in demo_images],
        )
        if demo_choice != "(none)":
            image_path = str(IMAGES_DIR / demo_choice)

    if image_path:
        st.image(
            image_path,
            caption="Input image",
            width=520
        )

    st.divider()

    # ===== Run Button =====
    run = st.button("▶ Run Detection", type="primary", disabled=image_path is None)

    if run:
        with st.spinner("Running YOLO inference..."):
            out = run_pipeline(order_items, image_path)

        vis_path = out.get("vis_image")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.image(image_path, caption="Original", width=350)

        with col2:
            st.image(vis_path, caption="Detected", width=350)

        expected_items = out.get("order", order_items)
        detected = out.get("detected", [])
        result = out.get("result", {})

        missing = result.get("missing", {}) or {}
        extra = result.get("extra", {}) or {}
        rule_missing = result.get("rule_missing", {}) or {}
        notes = result.get("notes", []) or []

        is_ok = (not missing) and (not extra) and (not rule_missing)

        st.subheader(" Result")

        c1, c2, c3, c4 = st.columns(4)

        c1.caption(f"判定：{'OK✅' if is_ok else 'NG❌'}")
        c2.caption(f"不足：{summarize_counts(missing)}")
        c3.caption(f"余分：{summarize_counts(extra)}")
        c4.caption(f"ルール不足：{summarize_counts(rule_missing)}")

        st.divider()

        left, right = st.columns(2)

        with left:
            st.markdown("### 注文内容（Expected）")
            st.dataframe(items_dict_to_df(expected_items), use_container_width=True, hide_index=180)

        with right:
            st.markdown("### 検出結果（Detected）")
            det_df = detected_list_to_df(detected)
            if det_df.empty:
                st.info("検出結果なし")
            else:
                st.dataframe(det_df, use_container_width=True, hide_index=True)

        st.divider()

        st.markdown("###  差分（不足 / 余分 / ルール不足）")
        st.dataframe(diff_to_df(missing, extra, rule_missing), use_container_width=True, hide_index=180)

        if is_ok:
            st.success("判定：一致（OK）")
        else:
            st.error("判定：不一致（NG）")

        if notes:
            st.markdown("###  Notes")
            for n in notes:
                st.write(f"- {n}")

        st.download_button(
            "Download result JSON",
            json.dumps(out, indent=2, ensure_ascii=False),
            file_name="result.json",
            mime="application/json",
        )

        with st.expander("差分（不足 / 余分 / ルール不足）"):
            st.dataframe(
                diff_to_df(missing, extra, rule_missing),
                use_container_width=True,
                height=180
            )


if __name__ == "__main__":
    main()
