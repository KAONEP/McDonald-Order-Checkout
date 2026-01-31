from pathlib import Path
import re

# ====== 你只需要改这里 ======
DATASET_ROOT = r"C:\Users\13171\MCD_CHECKOUT\traning"   # 这里填包含 train/valid/test 的那一层根目录
USE_SPLIT_PREFIX = True        # True: train_0001 / valid_0001 / test_0001
PREFIX = "img"                 # 当 USE_SPLIT_PREFIX=False 时使用，如 img_0001
DO_RENAME = True              # 先 False 预览；确认后改 True 真改
# ============================

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

def natural_key(p: Path):
    s = p.name
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def pick_splits(root: Path):
    # 兼容 train/val/test 或 train/valid/test
    candidates = []
    for name in ["train", "valid", "val", "test"]:
        d = root / name
        if d.exists() and d.is_dir():
            candidates.append(d)
    return candidates

def collect_images(img_dir: Path):
    return sorted(
        [p for p in img_dir.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS],
        key=natural_key
    )

def rename_split(split_dir: Path):
    img_dir = split_dir / "images"
    lbl_dir = split_dir / "labels"

    if not img_dir.exists():
        print(f"[SKIP] {split_dir.name}: no images/ folder")
        return []

    imgs = collect_images(img_dir)
    if not imgs:
        print(f"[SKIP] {split_dir.name}: images/ is empty")
        return []

    # 每个 split 单独编号，补零位数按该 split 的数量
    width = max(2, len(str(len(imgs))))

    plan = []
    for i, src in enumerate(imgs, start=1):
        if USE_SPLIT_PREFIX:
            new_stem = f"{split_dir.name}_{i:0{width}d}"
        else:
            new_stem = f"{PREFIX}_{i:0{width}d}"

        dst_img = src.with_name(new_stem + src.suffix.lower())

        src_lbl = lbl_dir / (src.stem + ".txt") if lbl_dir.exists() else None
        dst_lbl = lbl_dir / (new_stem + ".txt") if lbl_dir.exists() else None

        plan.append((src, dst_img, src_lbl, dst_lbl))

    # 冲突检查
    for src, dst_img, src_lbl, dst_lbl in plan:
        if dst_img.exists() and dst_img.resolve() != src.resolve():
            raise FileExistsError(f"[{split_dir.name}] target image exists: {dst_img}")
        if src_lbl and dst_lbl and dst_lbl.exists() and (not src_lbl.exists() or dst_lbl.resolve() != src_lbl.resolve()):
            raise FileExistsError(f"[{split_dir.name}] target label exists: {dst_lbl}")

    return plan

def apply_plan(plan):
    # 两段式改名：先改临时名避免撞车，再改最终名
    tmp_suffix = ".tmp_ren"
    tmp_pairs = []

    # 先改图片
    for src, dst_img, src_lbl, dst_lbl in plan:
        tmp_img = src.with_name(src.name + tmp_suffix)
        if DO_RENAME:
            src.rename(tmp_img)
        tmp_pairs.append((tmp_img, dst_img))

        # 再改 label（如果存在）
        if src_lbl and src_lbl.exists():
            tmp_lbl = src_lbl.with_name(src_lbl.name + tmp_suffix)
            if DO_RENAME:
                src_lbl.rename(tmp_lbl)
            tmp_pairs.append((tmp_lbl, dst_lbl))

    # 再从临时名改到最终名
    for tmp_src, final_dst in tmp_pairs:
        if DO_RENAME:
            tmp_src.rename(final_dst)

def main():
    root = Path(DATASET_ROOT)
    if not root.exists():
        raise FileNotFoundError(f"DATASET_ROOT not found: {root}")

    splits = pick_splits(root)
    if not splits:
        raise FileNotFoundError("No split folders found (train/valid(or val)/test).")

    all_plans = []
    print("Found splits:", ", ".join([d.name for d in splits]))

    for split_dir in splits:
        plan = rename_split(split_dir)
        if plan:
            all_plans.append((split_dir.name, plan))

    if not all_plans:
        print("Nothing to rename.")
        return

    print("\n=== Rename preview ===")
    for split_name, plan in all_plans:
        print(f"\n[{split_name}] {len(plan)} images")
        for src, dst_img, src_lbl, dst_lbl in plan[:20]:
            print(f"  [IMG] {src.name} -> {dst_img.name}")
            if src_lbl:
                if src_lbl.exists():
                    print(f"   [LBL] {src_lbl.name} -> {dst_lbl.name}")
                else:
                    print(f"   [LBL] (missing) {src_lbl.name}")
        if len(plan) > 20:
            print(f"  ... ({len(plan)-20} more)")

    if not DO_RENAME:
        print("\nDry-run only. Set DO_RENAME=True to actually rename.")
        return

    for split_name, plan in all_plans:
        apply_plan(plan)
        print(f"[DONE] {split_name}")

    print("\nAll done.")

if __name__ == "__main__":
    main()
