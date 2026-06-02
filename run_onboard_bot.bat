@echo off
:: Set UTF-8 encoding for the terminal output
chcp 65001 > nul
set PYTHONUTF8=1
title OnboardBot Launcher

echo ===================================================
echo             🚀 STARTING ONBOARDBOT 🚀
echo ===================================================
echo.

:: Check if Ollama is running
echo [1/3] Checking Ollama Status...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo [!] Ollama is not running. Attempting to start Ollama...
    
    :: Attempt to start using the system command
    start "" "ollama" serve 2>nul
    
    :: Fallback: try starting the local AppData app if direct command fails
    if %ERRORLEVEL% NEQ 0 (
        if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
            start "" "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" serve
        ) else if exist "%LOCALAPPDATA%\Programs\Ollama\ollama_app.exe" (
            start "" "%LOCALAPPDATA%\Programs\Ollama\ollama_app.exe"
        )
    )
    
    echo [*] Waiting for Ollama to initialize...
    ping 127.0.0.1 -n 6 > nul
) else (
    echo [✓] Ollama is already running.
)
echo.

:: Check if llama3.2 is pulled
echo [2/3] Verifying llama3.2 model...
ollama list 2>nul | findstr /i "llama3.2" > nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] llama3.2 model not found. Attempting to pull it...
    ollama pull llama3.2
    if %ERRORLEVEL% NEQ 0 (
        echo [WARNING] Could not verify/pull llama3.2 model. Will attempt to run anyway...
    )
) else (
    echo [✓] llama3.2 model is available.
)
echo.

:: Launch Streamlit app
echo [3/3] Launching Streamlit Web UI...
echo [*] Starting Streamlit in your default web browser...
echo.
python -X utf8 -m streamlit run app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Error launching Streamlit. Please make sure python and streamlit are installed.
)

echo.
echo ===================================================
echo Launcher finished. Press any key to close this window.
echo ===================================================
pause > nul

