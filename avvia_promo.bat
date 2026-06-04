@echo off
title Promo Slide Generator

echo ============================================
echo  Promo Slide Generator - Avvio
echo ============================================
echo.

:: Controlla se Python e' installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato. Installa Python da https://www.python.org
    pause
    exit /b 1
)

:: Installa dipendenze
echo Installazione/aggiornamento dipendenze...
pip install -r promo_requirements.txt --quiet

echo.
echo Avvio app... Il browser si apre automaticamente.
echo Per fermare l'app premi CTRL+C in questa finestra.
echo.

:: Avvia Streamlit
streamlit run promo_slide_generator.py --server.headless false

pause
