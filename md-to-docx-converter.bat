@echo off
chcp 932
echo D&D Markdown to Word Converter
echo ==============================

for %%f in (*.md) do (
    echo Converting %%f to Word format...
    pandoc "%%f" -o "%%~nf.docx"
    
    if errorlevel 0 (
        echo Conversion successful: %%~nf.docx created.
    ) else (
        echo Error converting %%f.
    )
)

echo.
echo All documents processed.
echo Press any key to exit...
pause > nul
