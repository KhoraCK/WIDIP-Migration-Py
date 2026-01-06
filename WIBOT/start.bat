@echo off
echo ========================================
echo    WIBOT - Demarrage
echo ========================================
echo.

:: Demarrer le backend (Docker)
echo [1/2] Demarrage du backend Docker...
cd /d "%~dp0wibot-backend"
docker-compose up -d

echo.
echo Attente du demarrage des services (15 secondes)...
timeout /t 15 /nobreak >nul

:: Demarrer le frontend
echo.
echo [2/2] Demarrage du frontend...
cd /d "%~dp0wibot-frontend"
start "WIBOT Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo    WIBOT demarre !
echo ========================================
echo.
echo Frontend : http://localhost:5173
echo n8n Editor : http://localhost:5679
echo.
echo Identifiants : khora / test123
echo.
pause
