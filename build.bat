@echo off
REM Gera dist\WindowsAutoCleaner.exe (instalador) e dist\Desinstalar_WindowsAutoCleaner.exe
py -m pip install pyinstaller
if errorlevel 1 goto erro

py -m PyInstaller --onefile --name WindowsAutoCleaner --paths src src\main.py
if errorlevel 1 goto erro

py -m PyInstaller --onefile --name Desinstalar_WindowsAutoCleaner --paths src src\desinstalar.py
if errorlevel 1 goto erro

echo.
echo Pronto: dist\WindowsAutoCleaner.exe  e  dist\Desinstalar_WindowsAutoCleaner.exe
pause
exit /b 0

:erro
echo.
echo ERRO: a geracao do executavel falhou. Veja as mensagens acima.
pause
exit /b 1
 