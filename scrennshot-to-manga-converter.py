import sys
import os
import subprocess
from pathlib import Path

def process_images(image_paths):
    # 処理するファイルが存在するか確認
    if not image_paths:
        print("ファイルがドロップされていません")
        return
    
    print(f"{len(image_paths)}個のファイルを処理します...")
    
    # 作業ディレクトリを取得
    working_dir = os.path.dirname(image_paths[0])
    os.chdir(working_dir)
    
    # 処理済み画像を保存する一時ディレクトリ
    temp_dir = "temp_processed"
    os.makedirs(temp_dir, exist_ok=True)
    
    processed_files = []
    
    # 各画像を処理
    for i, img_path in enumerate(image_paths):
        img_name = os.path.basename(img_path)
        output_path = os.path.join(temp_dir, f"proc_{i:03d}_{img_name}")
        
        # ImageMagickで画像処理: auto-level, shave, trim
        cmd = [
            "magick", img_path, 
            "-auto-level", 
            "-fuzz", "80%", 
            "-trim", 
            output_path
        ]
        
        print(f"処理中: {img_name}")
        subprocess.run(cmd, check=True)
        processed_files.append(output_path)
    
    # 右から左の順序に並び替え（ファイル名でソート後逆順にする）
    processed_files.sort(reverse=True)
    
    # 結合コマンド（右から左への横方向結合）
    output_filename = "combined_manga.png"
    combine_cmd = ["magick"] + processed_files + ["+append", output_filename]
    
    print("画像を結合しています...")
    subprocess.run(combine_cmd, check=True)
    
    print(f"完了しました！結合画像: {output_filename}")
    
    # 一時ディレクトリを削除（オプション）
    import shutil
    shutil.rmtree(temp_dir)
    
    return output_filename

if __name__ == "__main__":
    # コマンドライン引数（ドラッグ＆ドロップされたファイル）を取得
    if len(sys.argv) > 1:
        image_paths = [path for path in sys.argv[1:] if Path(path).suffix.lower() in ['.png', '.jpg', '.jpeg']]
        result = process_images(image_paths)
        if result:
            print(f"処理が完了しました: {result}")
    else:
        print("使い方: 画像ファイルをこのスクリプトにドラッグ＆ドロップしてください")
    
    input("\n何かキーを押して終了...")