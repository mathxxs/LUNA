@echo off
chcp 65001 >nul
title LUNA - Setup e avvio automatico

REM Posiziona la working dir nella cartella dello script
cd /d "%~dp0"

echo.
echo ===============================================
echo    LUNA - verifica e avvio automatico
echo ===============================================
echo.

REM ---- 1/5 Python ----
echo [1/5] Verifica Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ERRORE: Python non trovato nel PATH.
    echo    Installa Python 3.11+ da https://www.python.org/downloads
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo    OK - %%v

REM ---- 2/5 Dipendenze Python ----
echo.
echo [2/5] Verifica dipendenze Python...
python -c "import streamlit, langgraph, langchain_ollama, chromadb, ddgs, httpx, trafilatura, pypdf, pydantic_settings" >nul 2>&1
if errorlevel 1 (
    echo    Pacchetti mancanti. Installazione in corso, attendi...
    python -m pip install --quiet -r requirements.txt
    if errorlevel 1 (
        echo    ERRORE: pip install fallito.
        echo    Prova manualmente: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo    OK - dipendenze installate
) else (
    echo    OK - tutte le dipendenze presenti
)

REM ---- 3/5 Ollama installato ----
echo.
echo [3/5] Verifica Ollama installato...
where ollama >nul 2>&1
if errorlevel 1 (
    echo    ERRORE: Ollama non trovato nel PATH.
    echo    Installa Ollama da https://ollama.com/download/windows
    echo    Dopo l'installazione, riavvia questo script.
    echo.
    pause
    exit /b 1
)
echo    OK - Ollama installato

REM ---- 4/5 Ollama server ----
echo.
echo [4/5] Verifica Ollama server in esecuzione...
ollama list >nul 2>&1
if errorlevel 1 (
    echo    Ollama server non risponde, avvio in background...
    start "Ollama Server" /B ollama serve
    timeout /t 5 /nobreak >nul
    ollama list >nul 2>&1
    if errorlevel 1 (
        echo    ERRORE: impossibile avviare Ollama.
        echo    Avvia Ollama manualmente dall'icona nella tray e rilancia lo script.
        pause
        exit /b 1
    )
)
echo    OK - Ollama server attivo

REM ---- 5/5 Modelli necessari ----
echo.
echo [5/5] Verifica modelli Ollama necessari...
call :check_model qwen3.5:2b           || (pause & exit /b 1)
call :check_model qwen3.5:4b           || (pause & exit /b 1)
call :check_model qwen3.5:9b           || (pause & exit /b 1)
call :check_model embeddinggemma:300m  || (pause & exit /b 1)

REM ---- Avvio Streamlit ----
echo.
echo ===============================================
echo    Tutto pronto. Avvio della UI...
echo ===============================================
echo.
echo    La UI si aprira automaticamente nel browser
echo    su http://localhost:8501
echo.
echo    Per chiudere: chiudi questa finestra
echo    oppure premi Ctrl+C.
echo.

python -m streamlit run app.py

echo.
echo Streamlit terminato.
pause
exit /b 0

REM ============================================================
REM   Subroutine: verifica un modello Ollama, lo scarica se manca
REM   Uso: call :check_model nome_modello
REM ============================================================
:check_model
ollama list | findstr /C:"%~1" >nul
if errorlevel 1 (
    echo    Modello %~1 mancante, download in corso ^(puo richiedere alcuni minuti^)...
    ollama pull %~1
    if errorlevel 1 (
        echo    ERRORE: download di %~1 fallito.
        exit /b 1
    )
    echo    OK - %~1 scaricato
) else (
    echo    OK - %~1
)
exit /b 0
