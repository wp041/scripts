import os
import sys
import subprocess
import tempfile
from tkinter import Tk, Label, Button, Frame, StringVar, filedialog, messagebox

# ImageMagickコマンド確認用変数
use_convert_command = False

def check_imagemagick():
    """ImageMagickがインストールされているか確認"""
    global use_convert_command
    try:
        subprocess.run(["magick", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ImageMagick (magick) を検出しました")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        try:
            # magickコマンドがない場合、convertコマンドを試す（古いバージョンのImageMagick）
            subprocess.run(["convert", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # convertコマンドが存在する場合
            use_convert_command = True
            print("ImageMagick (convert) を検出しました")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("ImageMagickがインストールされていません")
            print("https://imagemagick.org/script/download.php からインストールしてください。")
            return False

def select_files():
    """PNGファイル選択"""
    files = filedialog.askopenfilenames(
        title="変換するPNGファイルを選択",
        filetypes=[("PNG画像", "*.png")]
    )
    return list(files) if files else []

def convert_files(files):
    """ファイル変換処理"""
    if not files:
        messagebox.showinfo("情報", "ファイルが選択されていません")
        return
    
    # 変換先のPDFファイル名を取得
    output_pdf = filedialog.asksaveasfilename(
        title="PDFの保存先を選択",
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
        initialfile="converted_images.pdf"
    )
    
    if not output_pdf:
        return  # キャンセルされた
    
    try:
        # 進捗ウィンドウの作成
        progress_win = Tk()
        progress_win.title("変換中...")
        progress_win.geometry("300x100")
        progress_label = Label(progress_win, text="PNGファイルを処理中...")
        progress_label.pack(pady=20)
        progress_win.update()
        
        # 一時ディレクトリ作成
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_files = []
            
            # 各ファイルを処理
            for i, file_path in enumerate(files):
                output_file = os.path.join(temp_dir, f"processed_{i}.png")
                
                # 進捗表示更新
                progress_label.config(text=f"処理中: {i+1}/{len(files)}")
                progress_win.update()
                
                # ImageMagickで閾値処理
                command = ["convert"] if use_convert_command else ["magick"]
                subprocess.run([
                    *command, file_path, 
                    "-threshold", "70%", 
                    output_file
                ], check=True)
                
                processed_files.append(output_file)
            
            # 進捗表示更新
            progress_label.config(text="PDFファイルを作成中...")
            progress_win.update()
            
            # まとめてPDF化
            command = ["convert"] if use_convert_command else ["magick"]
            subprocess.run([
                *command, *processed_files, output_pdf
            ], check=True)
            
            progress_win.destroy()
            messagebox.showinfo("完了", f"PDFの作成が完了しました\n保存先: {output_pdf}")
            return True
            
    except Exception as e:
        try:
            progress_win.destroy()
        except:
            pass
        messagebox.showerror("エラー", f"変換中にエラーが発生しました\n{str(e)}")
        return False

def main():
    """メイン関数"""
    # ImageMagick確認
    if not check_imagemagick():
        messagebox.showerror("エラー", "ImageMagickがインストールされていません。\nインストールしてから再度実行してください。")
        return
    
    # ルートウィンドウを作成して隠す（ファイル選択ダイアログのみ表示）
    root = Tk()
    root.withdraw()
    
    try:
        # ファイル選択
        files = select_files()
        
        if files:
            # 変換処理実行
            convert_files(files)
    except Exception as e:
        messagebox.showerror("エラー", f"エラーが発生しました: {str(e)}")
    finally:
        root.destroy()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        input("Enterキーを押して終了...")