@echo off
setlocal
title Landesverein Karriereplattform - System Doctor
echo =======================================================================
echo         Landesverein System Doctor - Fehleranalyse
echo =======================================================================
echo Dieses Skript prueft Ihre Umgebung auf typische Probleme.
echo Bitte senden Sie die Ausgabe dieses Skripts an den Support.
echo =======================================================================
echo.

echo [PRUEFUNG 1] Betriebssystem:
ver
echo.

echo [PRUEFUNG 2] Node.js Installation:
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [FEHLER] Node.js NICHT GEFUNDEN!
) else (
    node -v
)
echo.

echo [PRUEFUNG 3] NPM Installation:
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [FEHLER] NPM NICHT GEFUNDEN!
) else (
    npm -v
)
echo.

echo [PRUEFUNG 4] Ordnerstruktur:
if not exist "frontend" (
    echo [FEHLER] Ordner "frontend" fehlt!
) else (
    echo [OK] Frontend Ordner existiert.
)
if not exist "prisma" (
    echo [FEHLER] Ordner "prisma" fehlt!
) else (
    echo [OK] Prisma Ordner existiert.
)
echo.

echo [PRUEFUNG 5] Umgebungsvariablen (.env):
if not exist ".env" (
    echo [FEHLER] Root .env Datei fehlt! Wurde setup.bat ausgefuehrt?
) else (
    echo [OK] Root .env Datei existiert.
)
if not exist "frontend\.env.local" (
    echo [FEHLER] Frontend .env.local fehlt! Wurde setup.bat ausgefuehrt?
) else (
    echo [OK] Frontend .env.local existiert.
)
echo.

echo [PRUEFUNG 6] Datenbank-Status:
if not exist "prisma\dev.db" (
    echo [FEHLER] dev.db nicht gefunden! Die Datenbank wurde nicht initialisiert.
) else (
    echo [OK] SQLite Datenbank dev.db existiert.
)
echo.

echo [PRUEFUNG 7] Port-Belegung (3000 und 3001):
netstat -ano | findstr :3000 >nul
if %errorlevel% equ 0 (
    echo [WARNUNG] Port 3000 ist bereits belegt! (Moege das Frontend blockieren)
) else (
    echo [OK] Port 3000 ist frei.
)
netstat -ano | findstr :3001 >nul
if %errorlevel% equ 0 (
    echo [WARNUNG] Port 3001 ist bereits belegt! (Moege das Backend blockieren)
) else (
    echo [OK] Port 3001 ist frei.
)
echo.

echo =======================================================================
echo Analyse abgeschlossen. 
echo Wenn FEHLER gemeldet wurden, beheben Sie diese oder fuehren Sie 
echo 'setup.bat' erneut aus.
echo =======================================================================
pause
