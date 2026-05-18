@echo off
setlocal enabledelayedexpansion
title Enterprise Karriereplattform - Setup & Installation
echo =======================================================================
echo          Enterprise Karriereplattform - Automatisches Setup
echo =======================================================================
echo.

echo [1/6] Pruefe Systemvoraussetzungen (Node.js)...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [FEHLER] Node.js wurde nicht gefunden.
    echo Bitte laden Sie Node.js (LTS Version) von https://nodejs.org/ herunter und installieren Sie es.
    echo Stellen Sie sicher, dass Node.js zur "PATH" Umgebungsvariablen hinzugefuegt wird.
    pause
    exit /b 1
)
node -v > node_version.txt
set /p NODE_VERS=<node_version.txt
del node_version.txt
echo [OK] Node.js gefunden: !NODE_VERS!
echo.

echo [2/6] Richte Umgebungsvariablen (.env) ein...
set "PROJECT_ROOT=%cd%"
set "PRISMA_DB_PATH=%PROJECT_ROOT%\prisma\dev.db"
set "PRISMA_DB_PATH_FORWARD=!PRISMA_DB_PATH:\=/!"

echo DATABASE_URL="file:./dev.db" > .env
echo JWT_SECRET="enterprise-secret-key-super-secure-change-me" >> .env
echo PORT=3001 >> .env
echo [OK] Root .env erstellt (Port 3001)

if not exist "frontend" mkdir frontend
echo DATABASE_URL="file:!PRISMA_DB_PATH_FORWARD!" > frontend\.env.local
echo [OK] Frontend .env.local erstellt mit korrektem Datenbank-Pfad.
echo.

echo [3/6] Installiere Backend/Root Abhaengigkeiten...
call npm install
if %errorlevel% neq 0 (
    echo [FEHLER] Backend Abhaengigkeiten konnten nicht installiert werden.
    echo Bitte pruefen Sie Ihre Internetverbindung oder fuehren Sie "doctor.bat" aus.
    pause
    exit /b 1
)
echo [OK] Root Abhaengigkeiten installiert.
echo.

echo [4/6] Installiere Frontend Abhaengigkeiten...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [FEHLER] Frontend Abhaengigkeiten konnten nicht installiert werden.
    cd ..
    pause
    exit /b 1
)
cd ..
echo [OK] Frontend Abhaengigkeiten installiert.
echo.

echo [5/6] Initialisiere und migriere die Datenbank...
call npx prisma generate
if %errorlevel% neq 0 (
    echo [FEHLER] Prisma Generate fehlgeschlagen.
    pause
    exit /b 1
)

call npx prisma db push
if %errorlevel% neq 0 (
    echo [FEHLER] Datenbank Migration fehlgeschlagen.
    pause
    exit /b 1
)
echo [OK] Datenbank bereit.
echo.

echo [6/6] Fuehre initiale Daten-Befuellung (Seeding) durch...
call node seed.mjs
if %errorlevel% neq 0 (
    echo [HINWEIS] Seeding Script hat einen Fehler gemeldet oder existiert nicht. Dies ist kein kritischer Fehler, wenn die DB bereits Daten enthaelt.
) else (
    echo [OK] Datenbank erfolgreich mit Standard-Daten befuellt.
)
echo.

echo =======================================================================
echo ERFOLG! Die Installation ist abgeschlossen.
echo =======================================================================
echo Sie koennen die Plattform nun mit der Datei "start.bat" starten.
echo Bei Problemen fuehren Sie bitte "doctor.bat" zur Fehleranalyse aus.
echo =======================================================================
pause
