@echo off
call conda activate hydroocean-grib
if errorlevel 1 (
    echo No se pudo activar hydroocean-grib.
    echo Ejecute primero setup_env.bat desde Anaconda Prompt.
    pause
    exit /b 1
)
python main.py
if errorlevel 1 pause
