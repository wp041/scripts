"""
classify_by_color.py

スキャン画像の紙色を読み取り、色別フォルダに振り分けるスクリプト

使い方:
    python classify_by_color.py <入力ディレクトリ> <出力ディレクトリ>

    例: python classify_by_color.py ./scanned ./sorted
"""

import cv2
import numpy as np
import shutil
import sys
from pathlib import Path

# ────────────────────────────────
# 設定
# ────────────────────────────────

# 対象拡張子
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}

# 暗部マスク: V（明度）がこれ以下のピクセルは除外（文字・罫線を除く）
DARK_V_THRESHOLD = 100  # 0〜255

# 無彩色判定: S（彩度）がこれ以下なら無彩色とみなす
ACHROMATIC_S_THRESHOLD = 30  # 0〜255

# 明度による白/グレー/クリームの分岐
# ※クリームは無彩色かつ暖色寄り（Hueが低い）を後段で補足
WHITE_V_THRESHOLD = 200    # これ以上 → 白
GRAY_V_THRESHOLD  = 100    # これ以上（かつ白未満）→ グレー、未満 → 暗グレー

# Hue範囲テーブル（OpenCVのHueは 0〜179）
# (フォルダ名, Hue下限, Hue上限)
HUE_RANGES = [
    ("red",    0,   10),
    ("orange", 11,  20),
    ("yellow", 21,  35),
    ("green",  36,  85),
    ("cyan",   86, 100),
    ("blue",  101, 130),
    ("purple",131, 155),
    ("pink",  156, 170),
    ("red",   171, 179),   # 赤の折り返し
]

# クリームの判定（無彩色 かつ 支配的Hueがorange/yellowゾーン かつ 高明度）
# ※ピクセル数が少なくてもhint程度に使う
CREAM_HUE_MIN = 15
CREAM_HUE_MAX = 35
CREAM_V_MIN   = 180

# ────────────────────────────────
# 色分類ロジック
# ────────────────────────────────

def dominant_hue(hue_channel: np.ndarray) -> int:
    """Hueチャンネルを16段階に量子化してモードを返す（0〜179）"""
    bins = 16
    bin_size = 180 // bins
    quantized = hue_channel // bin_size
    counts = np.bincount(quantized.ravel(), minlength=bins)
    dominant_bin = int(np.argmax(counts))
    return dominant_bin * bin_size + bin_size // 2  # binの中央値を返す


def hue_to_label(hue: int) -> str:
    for label, lo, hi in HUE_RANGES:
        if lo <= hue <= hi:
            return label
    return "other"


def classify_image(image_path: Path) -> str:
    """
    画像を読み込み、色カテゴリ名（フォルダ名）を返す。
    """
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise ValueError(f"読み込み失敗: {image_path}")

    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(img_hsv)

    # 暗部マスク（文字・罫線除去）
    bright_mask = V > DARK_V_THRESHOLD

    H_bright = H[bright_mask]
    S_bright = S[bright_mask]
    V_bright = V[bright_mask]

    if H_bright.size == 0:
        return "dark"

    # 無彩色判定（彩度の中央値で判断）
    median_s = float(np.median(S_bright))
    median_v = float(np.median(V_bright))

    if median_s < ACHROMATIC_S_THRESHOLD:
        # 無彩色ゾーン → 白/グレー/クリームへ振り分け
        if median_v >= WHITE_V_THRESHOLD:
            # クリームかどうかを確認（支配的Hueが暖色ゾーンか）
            dom_hue = dominant_hue(H_bright)
            if CREAM_HUE_MIN <= dom_hue <= CREAM_HUE_MAX and median_v >= CREAM_V_MIN:
                return "cream"
            return "white"
        elif median_v >= GRAY_V_THRESHOLD:
            return "gray"
        else:
            return "dark_gray"

    # 有彩色 → Hue分類
    # 彩度が高いピクセルに絞ってドミナントHueを取得
    chromatic_mask = S_bright > ACHROMATIC_S_THRESHOLD
    H_chromatic = H_bright[chromatic_mask]

    if H_chromatic.size == 0:
        return "white"

    dom_hue = dominant_hue(H_chromatic)
    return hue_to_label(dom_hue)


# ────────────────────────────────
# ファイル振り分け
# ────────────────────────────────

def sort_images(input_dir: Path, output_dir: Path) -> None:
    images = [p for p in input_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]

    if not images:
        print("対象画像が見つかりません。")
        return

    results: dict[str, list[Path]] = {}

    for img_path in images:
        try:
            label = classify_image(img_path)
        except Exception as e:
            print(f"[ERROR] {img_path.name}: {e}")
            label = "error"

        results.setdefault(label, []).append(img_path)

    # コピー
    for label, paths in results.items():
        dest_dir = output_dir / label
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src in paths:
            shutil.copy2(src, dest_dir / src.name)
            print(f"[{label}] {src.name}")

    print(f"\n完了: {len(images)}枚 → {len(results)}カテゴリ")


# ────────────────────────────────
# エントリポイント
# ────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("使い方: python classify_by_color.py <入力dir> <出力dir>")
        sys.exit(1)

    input_dir  = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not input_dir.exists():
        print(f"入力ディレクトリが存在しない: {input_dir}")
        sys.exit(1)

    sort_images(input_dir, output_dir)


if __name__ == "__main__":
    main()
