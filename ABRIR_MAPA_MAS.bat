@echo off
echo ========================================
echo   ABRIENDO MAPA INTERACTIVO MAS
echo   Sistema Multi-Agente en Tiempo Real
echo ========================================
echo.
echo Verificando que el servidor este corriendo...
timeout /t 2 /nobreak > nul

echo Abriendo mapa en el navegador...
start http://localhost:8000/static/mapa_mas_tiempo_real.html

echo.
echo Si el mapa no carga:
echo 1. Asegúrate de ejecutar INICIAR_SERVIDOR_MAS.bat primero
echo 2. Espera a que el servidor este completamente iniciado
echo 3. Verifica que el puerto 8000 este disponible
echo.
pause
