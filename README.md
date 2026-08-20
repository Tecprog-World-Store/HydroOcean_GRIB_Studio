# HydroOcean GRIB Studio v0.2.0
## Tecprog World E.I.R.L.

Aplicación de escritorio profesional para Windows orientada a la adquisición,
lectura y análisis de datos GRIB2 de NOAA/NCEP WAVEWATCH III / GFS-Wave.

### Cambio principal respecto de v0.1

Un archivo `f000.grib2` contiene normalmente **un solo instante**. Por ello no
puede producir por sí solo una serie temporal. Esta versión incorpora:

1. Apertura de un GRIB2 individual.
2. Apertura/procesamiento de una **carpeta completa de GRIB2**.
3. Descarga de una **corrida completa de pronóstico** (`f000...f384`) para
   construir una serie temporal.
4. Descarga operacional por **rango de fechas/ciclos** dentro de la retención
   disponible de NOMADS.
5. Agregación de múltiples archivos en una sola tabla temporal.
6. Exportación CSV.
7. Rosas de viento, oleaje y corriente.
8. GUI responsive con **PySide6/Qt**.
9. Menú Archivo / Adquisición / Análisis / Ayuda.
10. Branding Tecprog World E.I.R.L.
11. Base preparada para PyInstaller.
12. Script Inno Setup para crear instalador.

---

## Importante sobre datos por años

### GFS-Wave operacional / NOMADS
NOAA mantiene únicamente una ventana corta de datos recientes. No debe usarse
NOMADS como si fuera un archivo multianual.

### WAVEWATCH III históricos
Para estudios históricos deben utilizarse los archivos de hindcast/reanalysis:

- CFSR/CFSRR WAVEWATCH III: 1979–2009, homogéneo y apropiado para climatología.
- Production Hindcast: 2005-02 a 2019-05, archivo mensual GRIB2, pero
  estadísticamente inhomogéneo debido a cambios de los modelos operacionales.

La pestaña **Histórico** incluye el planificador y accesos oficiales. Una futura
versión puede incorporar descarga automática de los paquetes NCEI, pero debe
evitarse prometer "descarga de cualquier año desde NOMADS", porque la fuente
operacional no lo permite.

Fuentes oficiales:
- https://polar.ncep.noaa.gov/waves/download2.shtml
- https://polar.ncep.noaa.gov/waves/CFSR_hindcast.shtml
- https://www.ncei.noaa.gov/archive/accession/NCEP-WAVEWATCH
- https://nomads.ncep.noaa.gov/

---

## Crear environment

Desde **Anaconda Prompt**:

```bat
cd C:\RUTA\HydroOcean_GRIB_Studio_v0.2.0
conda env create -f environment.yml
conda activate hydroocean-grib
python main.py
```

Si ya existe el environment:

```bat
conda env update -n hydroocean-grib -f environment.yml --prune
```

---

## Identidad de la empresa

El programa carga el logo desde:

```text
src/logo-tecprog-world.png
```

Esta entrega contiene un marcador de identidad para que el programa siempre
arranque. Reemplace ese archivo por el logo oficial de Tecprog World E.I.R.L.
manteniendo exactamente el mismo nombre.

Datos mostrados en Ayuda > Acerca de:

- Tecprog World E.I.R.L.
- grupotecprog@gmail.com
- WhatsApp: +51 952 354 282
- Yape Perú: +51 952 354 282
- Donaciones internacionales: coordinación por correo para PayPal.

---

## Crear EXE

```bat
conda activate hydroocean-grib
build_exe.bat
```

Salida:

```text
dist\HydroOceanGRIBStudio\
```

La aplicación se genera en modo `onedir`, recomendado para Qt + ecCodes/cfgrib.

---

## Crear instalador Inno Setup

Después de generar `dist`:

1. Abra `installer\HydroOceanGRIBStudio.iss` con Inno Setup.
2. Pulse **Compile**.
3. El instalador aparecerá en:
   `installer\Output\`

Nota: la versión gratuita/no comercial de Inno Setup mostrada en la captura
debe utilizarse respetando sus condiciones de licencia y el uso comercial
correspondiente.

---

## Flujo para generar una serie temporal

### Opción A — carpeta de archivos
Descargue varios GRIB2 y use:

**Archivo > Abrir carpeta GRIB2**

Luego:
- defina latitud/longitud,
- seleccione Oleaje/Viento,
- pulse `Construir serie`.

### Opción B — corrida de pronóstico
En **Adquisición > GFS-Wave operacional**:
- fecha,
- ciclo,
- `f inicial = 0`,
- `f final = 120`,
- paso = 3,
- región,
- Descargar corrida.

Se descargan varios archivos y pueden agregarse automáticamente.

### Opción C — observaciones/estudio histórico
Para años completos se debe trabajar con hindcast/reanalysis; no con f000 de
NOMADS.

---

## Convenciones

- Viento: dirección meteorológica **desde donde viene**.
- Corriente: dirección oceanográfica **hacia donde va**.
- Oleaje: se conserva la dirección reportada por el producto y se etiqueta.
- Longitudes NOAA 0–360 se convierten automáticamente para coordenadas -180–180
  cuando es necesario.

---

## Licencia del código

MIT para el código de esta plantilla. Los datos NOAA conservan sus propios
avisos y condiciones. Tecprog World E.I.R.L. no garantiza disponibilidad de
servicios remotos de terceros.
