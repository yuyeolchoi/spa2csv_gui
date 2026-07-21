@echo off
REM SPA to CSV Converter - standalone exe build script
REM Produces dist\SPA_to_CSV.exe (no console window)
cd /d "%~dp0"
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --onefile --windowed --name SPA_to_CSV --noconfirm main.py
echo.
echo Done. Executable: dist\SPA_to_CSV.exe
pause
