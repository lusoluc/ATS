@echo off
setlocal
title SecurATS - System Doctor
echo =======================================================================
echo          SecurATS System Doctor - Umgebungspruefung (Django)
echo =======================================================================
echo Bitte senden Sie die komplette Ausgabe bei Supportanfragen mit.
echo.

echo [PRUEFUNG 1] Python:
where python >nul 2>nul
if errorlevel 1 (
    echo   [FEHLER] Python nicht gefunden - bitte Python 3.12 installieren.
) else (
    python --version
)
echo.

echo [PRUEFUNG 2] Virtuelle Umgebung:
if exist .venv\Scripts\python.exe (
    echo   [OK] .venv vorhanden
    .venv\Scripts\python --version
) else (
    echo   [HINWEIS] Keine .venv - start.bat legt sie beim ersten Start an.
)
echo.

echo [PRUEFUNG 3] Django-Systemcheck:
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python manage.py check 2>&1
) else (
    echo   uebersprungen - keine .venv
)
echo.

echo [PRUEFUNG 4] Offene Migrationen:
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python manage.py migrate --check >nul 2>&1
    if errorlevel 1 (
        echo   [HINWEIS] Es stehen Migrationen aus - start.bat wendet sie an.
    ) else (
        echo   [OK] Datenbank ist auf aktuellem Stand.
    )
)
echo.

echo [PRUEFUNG 5] Docker (nur fuer Produktivbetrieb relevant):
where docker >nul 2>nul
if errorlevel 1 (
    echo   [HINWEIS] Docker nicht gefunden - fuer die Entwicklung nicht noetig.
) else (
    docker --version
)
echo.
echo ======================= Pruefung abgeschlossen ========================
pause
