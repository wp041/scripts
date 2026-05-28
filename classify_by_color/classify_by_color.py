"""
スキャン画像の紙色を読み取り、色別フォルダに振り分けるスクリプト

使い方:
    python classify_by_color.py <入力ディレクトリ> <出力ディレクトリ>

    例: python classify_by_color.py ./scanned ./sorted
    
※venvでの使用を推奨

1.インストール
pip install -r requirements.txt


"""

import cv2
import numpy as np
import shutil
import argparse
from pathlib import Path
from scipy.stats import entropy as scipy_entropy
import logging

# ────────────────────────────────
# 設定

# 対象拡張子
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# 暗部マスク: V（明度）がこれ以下のピクセルは除外（文字・罫線を除く）
DARK_V_THRESHOLD = 100  # 0〜255

# 無彩色判定: S（彩度）がこれ以下なら無彩色とみなす
ACHROMATIC_S_THRESHOLD = 20  # 0〜255

# 明度による白/グレー/クリームの分岐
# ※クリームは無彩色かつ暖色寄り（Hueが低い）を後段で補足
WHITE_V_THRESHOLD = 200    # これ以上 → 白
GRAY_V_THRESHOLD  = 100    # これ以上（かつ白未満）→ グレー、未満 → 暗グレー

# Hue範囲テーブル（OpenCVのHueは 0〜179）
# (フォルダ名, Hue下限, Hue上限)
HUE_RANGES = [
    ("さくら",    0,   10),
    ("ビワ", 11,  20),
    ("レモン", 21,  35),
    ("若草",  36,  85),
    ("アサギ",   86, 130),
    ("さくら",   171, 179),   # 赤の折り返し
]

# 判別不能判定の閾値
DOMINANCE_THRESHOLD = 0.5   # より大きい　最頻binが全体の変数%未満なら判別不能→0.8～0.5
ENTROPY_THRESHOLD   = 0.75   # より小さい　最大 log(16) ≈ 変数→0.75～1.25？

# ────────────────────────────────

# 色分類関数

def dominant_hue(hue_channel: np.ndarray) -> int | None:
    """
    Hueチャンネルを16段階に量子化してモードを返す（0〜179）。
    ばらつきが大きく判別不能な場合は None を返す。
    """
    bins = 16
    bin_size = 180 // bins
    quantized = hue_channel // bin_size
    counts = np.bincount(quantized.ravel(), minlength=bins)


    # 占有率チェック
    dominance = counts.max() / counts.sum()
    logging.debug("占有= %.3f", dominance)
    if dominance < DOMINANCE_THRESHOLD:
        return None
    
    # エントロピーチェック
    probs = counts / counts.sum()
    h = scipy_entropy(probs)
    logging.debug("ento= %.3f", h)
    if h > ENTROPY_THRESHOLD:
        return None

    dominant_bin = int(np.argmax(counts))
    return dominant_bin * bin_size + bin_size // 2  # binの中央値を返す


def hue_to_label(hue: int) -> str:
    for label, lo, hi in HUE_RANGES:
        if lo <= hue <= hi:
            return label
    return "other"


def classify_image(image_path: Path) -> str:
    logging.debug("相対パス= %s", image_path)
    # 日本語用に
    img_bgr = cv2.imdecode(np.frombuffer(image_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
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
    logging.debug("明度= %s", median_s)
    logging.debug("彩度= %s", median_v)

    if median_s < ACHROMATIC_S_THRESHOLD:
        # 無彩色ゾーン → 白/グレー/クリームへ振り分け
        if median_v >= WHITE_V_THRESHOLD:
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
    if dom_hue is None:
        return "unclassified"

    logging.debug("色相= %s（量子化中央値）", dom_hue)
    return hue_to_label(dom_hue)


# 振り分け関数

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


# エントリポイント

def main():
    parser = argparse.ArgumentParser(description="スキャン紙色判別用スクリプト")
    parser.add_argument("input_dir", type=Path, help="入力ディレクトリを入力")
    parser.add_argument("output_dir", type=Path, help="出力ディレクトリを入力")
    parser.add_argument("-d", "--debug", action="store_true", help="デバッグモードオプション（各画像の解析結果を表示）")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(message)s"
    )

    sort_images(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()