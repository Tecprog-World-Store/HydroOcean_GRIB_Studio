@echo off
echo ===============================================
echo HydroOcean GRIB Studio - Creacion de ambiente
echo ===============================================
where conda >nul 2>nul
if errorlevel 1 (
    echo ERROR: conda no esta disponible en PATH.
    echo Abra Anaconda Prompt y ejecute este archivo nuevamente.
    pause
    exit /b 1
)
conda env create -f environment.yml
echo.
echo Si el entorno ya existia use:
echo conda env update -n hydroocean-grib -f environment.yml --prune
echo.
echo Para iniciar:
echo conda activate hydroocean-grib
echo python main.py
pause
