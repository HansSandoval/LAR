@echo off
echo ========================================
echo   SISTEMA MULTI-AGENTE (MAS)
echo   Gestion de Rutas de Recoleccion
echo   Sector Sur - Iquique
echo ========================================
echo.
echo Iniciando servidor FastAPI...
echo.

cd /d "%~dp0"
".venv\Scripts\python.exe" run_server.py

pause
