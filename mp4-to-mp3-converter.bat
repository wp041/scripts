@echo off
setlocal enabledelayedexpansion

if [%1]==[] (
    echo Drop MP4 files here
    pause
    exit /b
)

where ffmpeg >nul 2>nul
if !ERRORLEVEL! neq 0 (
    echo ffmpeg not found
    echo Please install ffmpeg
    pause
    exit /b
)

echo Files to convert:
for %%i in (%*) do (
    echo - "%%~nxi"
)

pause

for %%i in (%*) do (
    echo Converting: "%%~nxi"
    ffmpeg -i "%%~fi" -vn -acodec libmp3lame -b:a 320k -q:a 0 "%%~dpi%%~ni.mp3" -y
    if !ERRORLEVEL! equ 0 (
        echo Converted: "%%~nxi"
    ) else (
        echo Failed: "%%~nxi"
    )
    echo -------------------
)

echo All done!
pause