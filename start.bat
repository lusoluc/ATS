@echo off
setlocal
title SecurATS - Entwicklungsserver
rem Startet den Django-Entwicklungsserver. Beim ersten Aufruf wird die
rem virtuelle Umgebung angelegt und alles Noetige installiert.

if not exist .venv\Scripts\python.exe (
    echo [SETUP] Erstelle virtuelle Umgebung und installiere Abhaengigkeiten...
    python -m venv .venv || goto :fehler
    .venv\Scripts\python -m pip install --quiet -r requirements.txt || goto :fehler
)

echo [START] Wende Migrationen an...
.venv\Scripts\python manage.py migrate --noinput || goto :fehler

echo [START] Server laeuft auf http://127.0.0.1:8000/ (Beenden: Strg+C)
start "" http://127.0.0.1:8000/
.venv\Scripts\python manage.py runserver
goto :eof

:fehler
echo [FEHLER] Start fehlgeschlagen - bitte doctor.bat ausfuehren.
exit /b 1
