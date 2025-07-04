@echo off
chcp 932
echo D&D Word to Markdown Converter
echo ==============================

for %%f in (*.docx) do (
    echo Converting %%f to Markdown format...
    pandoc "%%f" --wrap=none --extract-media=media -t gfm -o "%%~nf.md"
    
    if errorlevel 0 (
        echo Conversion successful: %%~nf.md created.
    ) else (
        echo Error converting %%f.
    )
)

echo.
echo All documents processed.
echo Press any key to exit...
pause > nul
