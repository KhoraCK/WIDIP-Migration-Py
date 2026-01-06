@echo off
echo ========================================
echo    WIBOT - Arret
echo ========================================
echo.

:: Arreter le frontend (fermer les fenetres npm)
echo [1/2] Arret du frontend...
taskkill /FI "WINDOWTITLE eq WIBOT Frontend*" /F >nul 2>&1
taskkill /IM "node.exe" /F >nul 2>&1

:: Arreter le backend Docker
echo [2/2] Arret du backend Docker...
cd /d "%~dp0wibot-backend"
docker-compose down

echo.
echo ========================================
echo    WIBOT arrete !
echo ========================================
echo.
pause
