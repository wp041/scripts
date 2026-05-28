# 使い方
# python extract_jpg.py {input_dir} {output_dir}
# 相対パス・絶対パスどちらもいけます


import os
import shutil
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=".jpgを再帰取得してパス名付きでoutputに出力（\を_に置き換え）")
parser.add_argument("input_dir", type=Path, help="対象フォルダ")
parser.add_argument("output_dir", type=Path, help="出力先フォルダ")
args = parser.parse_args()

args.output_dir.mkdir(parents=True, exist_ok=True)

for jpg in args.input_dir.rglob("*.jpg"):
    relative = jpg.relative_to(args.input_dir)
    new_name = str(relative).replace(os.sep, "_")
    shutil.copy2(jpg, args.output_dir / new_name)
    print(f"{jpg} → {new_name}")