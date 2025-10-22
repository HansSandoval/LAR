@echo off
REM Iniciar el visualizador VRP con Streamlit
REM Ejecución: Doble click en este archivo

REM Cambiar directorio al proyecto
cd /d "C:\Users\hanss\Desktop\LAR"

REM Ejecutar Streamlit
"%USERPROFILE%\Desktop\LAR\gestion_rutas\venv\Scripts\python.exe" -m streamlit run app_visualizador_vrp.py

pause
