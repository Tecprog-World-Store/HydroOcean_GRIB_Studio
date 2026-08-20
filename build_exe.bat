@echo off
setlocal
call conda activate hydroocean-grib
if errorlevel 1 (
  echo No se pudo activar hydroocean-grib.
  pause
  exit /b 1
)

echo Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist\HydroOceanGRIBStudio rmdir /s /q dist\HydroOceanGRIBStudio

echo Compilando con PyInstaller...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --name HydroOceanGRIBStudio ^
  --add-data "src\logo-tecprog-world.png;src" ^
  --collect-all cfgrib ^
  --collect-all eccodes ^
  --collect-all PySide6 ^
  main.py

echo.
echo Resultado:
echo %CD%\dist\HydroOceanGRIBStudio
pause
endlocal
