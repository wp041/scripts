import sqlite3
import os

# フォルダ内のすべての .clip ファイルを処理
folder_path = './'  # 対象のフォルダパス
for root, dirs, files in os.walk(folder_path):
    for filename in files:
        if filename.endswith('.clip'):
            clip_path = os.path.join(root, filename)
            
            # .clipファイルからSQLite部分を探して抜き出す
            with open(clip_path, mode='rb') as f:
                clip_str = f.read()

                search_text = "SQLite format 3"
                search_text_bytes = search_text.encode("utf-8")

                find_index = clip_str.find(search_text_bytes)

                if find_index != -1:
                    result_str = clip_str[find_index:]
                else:
                    print(f"SQLite format not found in the file: {filename}")
                    continue

            # 一旦別ファイルに保存
            sqlite_filename = filename.replace('.clip', '.sqlite')
            sqlite_path = os.path.join(root, sqlite_filename)
            
            with open(sqlite_path, mode="wb") as f:
                f.write(result_str)

            # サムネ取得
            connect = None
            try:
                connect = sqlite3.connect(sqlite_path)
                cursor = connect.cursor()
                cursor.execute("SELECT ImageData FROM CanvasPreview")
                png_data = cursor.fetchone()

                if png_data and png_data[0]:
                    png_filename = filename.replace('.clip', '.png')
                    png_path = os.path.join(root, png_filename)
                    with open(png_path, mode="wb") as f:
                        f.write(png_data[0])
                else:
                    print(f"No image data found in the database: {sqlite_filename}")
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
            finally:
                # 接続を確実にクローズ
                if connect:
                    connect.close()
                # .sqliteファイルを削除
                if os.path.exists(sqlite_path):
                    try:
                        os.remove(sqlite_path)
                    except Exception as e:
                        print(f"Failed to remove {sqlite_path}: {e}")

print("Processing complete!")