@echo off
setlocal
title Enterprise Karriereplattform - Startmenue
echo =======================================================================
echo            Enterprise Karriereplattform - Server Start
echo =======================================================================
echo.
echo Starte Backend API (Port 3001) und Frontend UI (Port 3000)...

:: Start Backend in a new hidden/minimized or just separated console
start "LV Backend API" cmd /c "npm start"

:: Wait a little
timeout /t 2 /nobreak >nul

:: Start Frontend in a new console
start "LV Frontend UI" cmd /c "cd frontend && npm run dev"

echo.
echo Die Server werden im Hintergrund (neue Fenster) gestartet.
echo.
echo Frontend (Benutzeroberflaeche): http://localhost:3000
echo Backend (API Service):          http://localhost:3001
echo.
echo Um die Server zu stoppen, schliessen Sie einfach die beiden 
echo neu geoeffneten schwarzen Kommandozeilen-Fenster.
echo =======================================================================
pause
