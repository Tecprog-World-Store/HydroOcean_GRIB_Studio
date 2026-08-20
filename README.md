# HydroOcean GRIB Studio

Aplicación de escritorio en Python/Tkinter para análisis hidro-oceanográfico a partir de archivos GRIB2 y fuentes NOAA/NCEP.

## Objetivo

El proyecto permite:

- Abrir archivos `.grib2`, `.grb2`, `.grib` y `.grb`.
- Inspeccionar variables disponibles.
- Extraer la serie temporal del punto de malla más cercano a una coordenada.
- Procesar viento:
  - U/V.
  - velocidad.
  - dirección meteorológica "desde".
  - rosa de vientos.
  - serie temporal.
- Procesar oleaje:
  - altura significativa (`HTSGW`).
  - periodo primario (`PERPW`).
  - dirección primaria (`DIRPW`).
  - rosa direccional de oleaje.
  - series temporales.
- Procesar corrientes cuando el GRIB2 contiene:
  - `UOGRD/VOGRD`,
  - `EASTCUR/NRTHCUR`,
  - u otros nombres equivalentes configurables.
- Calcular velocidad y dirección oceanográfica de la corriente.
- Descargar subconjuntos de GFS-Wave mediante NOAA/NCEP NOMADS Grib Filter.
- Exportar datos extraídos a CSV.
- Exportar figuras PNG.

## Decisión de arquitectura

Se utiliza un enfoque híbrido:

1. **Lectura local GRIB2** como núcleo estable y reproducible.
2. **Descarga automatizada por NOMADS Grib Filter** para adquirir GFS-Wave.
3. Conector independiente preparado para fuentes de corrientes como RTOFS.
4. No se depende de scraping frágil de HTML.

NOAA documenta que WAVEWATCH III/GFS-Wave se distribuye en GRIB y que NOMADS permite descargar subconjuntos regionales y por parámetros.

Referencias oficiales:
- https://polar.ncep.noaa.gov/waves/download.shtml
- https://nomads.ncep.noaa.gov/
- https://nomads.ncep.noaa.gov/info.php?page=gribfilter
- https://www.nco.ncep.noaa.gov/pmb/products/wave/
- https://www.nco.ncep.noaa.gov/pmb/products/rtofs/
- https://codes.wmo.int/

## Instalación recomendada: Anaconda Prompt

Ubícate en esta carpeta.

```bat
cd C:\RUTA\HydroOcean_GRIB_Studio
conda env create -f environment.yml
conda activate hydroocean-grib
python main.py
```

También puedes ejecutar:

```bat
setup_env.bat
```

y luego:

```bat
run_gui.bat
```

## ¿Por qué Conda?

La lectura GRIB2 con `cfgrib` utiliza la biblioteca ECMWF ecCodes. En Windows suele ser más simple y reproducible instalar `eccodes` y `cfgrib` desde `conda-forge` que gestionar bibliotecas binarias manualmente.

## Flujo recomendado de uso

### A. Archivo GRIB2 local

1. Ejecuta `python main.py`.
2. Pulsa **Abrir GRIB2**.
3. Selecciona el archivo.
4. Revisa la pestaña **Inventario**.
5. Define latitud y longitud.
6. Pulsa **Extraer punto**.
7. Selecciona el producto:
   - viento,
   - oleaje,
   - corrientes.
8. Genera la rosa o serie temporal.
9. Exporta CSV/PNG.

### B. Descargar GFS-Wave

1. Abre la pestaña **NOAA / GFS-Wave**.
2. Indica:
   - fecha `YYYYMMDD`,
   - ciclo `00`, `06`, `12` o `18`,
   - hora de pronóstico,
   - límites geográficos.
3. Selecciona parámetros.
4. Descarga.
5. El archivo queda en `data/downloads/`.
6. Ábrelo desde la GUI.

## Región Perú sugerida

Como punto inicial para pruebas:

- Norte: 1.0°
- Sur: -20.0°
- Oeste: -90.0°
- Este: -68.0°

Para estudios de ingeniería se recomienda descargar únicamente el dominio necesario para reducir volumen y tiempo de procesamiento.

## Variables de referencia GFS-Wave

- `WIND`: velocidad del viento.
- `WDIR`: dirección meteorológica, desde donde sopla.
- `UGRD`, `VGRD`: componentes del viento.
- `HTSGW`: altura significativa combinada.
- `PERPW`: periodo medio de la ola primaria.
- `DIRPW`: dirección de ola primaria.
- `WVHGT`: altura significativa de mar de viento.
- `WVPER`: periodo medio de mar de viento.
- `WVDIR`: dirección de mar de viento.
- `SWELL`: altura de swell.
- `SWPER`: periodo de swell.
- `SWDIR`: dirección de swell.

## Corrientes

GFS-Wave no debe asumirse como fuente general de corrientes oceánicas. Para corrientes se recomienda usar productos oceanográficos, por ejemplo RTOFS/HYCOM. NCEP define en GRIB2:

- `UOGRD`: componente U de corriente.
- `VOGRD`: componente V de corriente.
- `DIRC`: dirección de corriente.
- `SPC`: velocidad de corriente.
- `EASTCUR`: corriente hacia el Este.
- `NRTHCUR`: corriente hacia el Norte.

La versión inicial puede leer esas variables si están presentes en un GRIB2 local.

## Convenciones direccionales

- Viento: dirección meteorológica **desde donde viene**.
- Corriente: dirección oceanográfica **hacia donde se desplaza**.
- Oleaje: se conserva la dirección reportada por el producto y se etiqueta de forma explícita en las salidas.

No intercambiar automáticamente estas convenciones en informes técnicos.

## Estructura

```text
HydroOcean_GRIB_Studio/
├─ main.py
├─ environment.yml
├─ setup_env.bat
├─ run_gui.bat
├─ config/
│  └─ default.yaml
├─ data/
│  ├─ downloads/
│  ├─ input/
│  └─ output/
├─ docs/
│  ├─ arquitectura.md
│  └─ variables_grib2.md
├─ src/
│  ├─ analysis/
│  ├─ acquisition/
│  ├─ grib/
│  ├─ gui/
│  ├─ plots/
│  └─ utils/
└─ tests/
```

## Alcance de esta versión

Esta entrega es un MVP técnico funcional y extensible. Antes de usar resultados para un estudio contractual, debe verificarse:

- fuente y versión del modelo,
- resolución espacial y temporal,
- zona horaria,
- datum/coordenadas,
- convención direccional,
- periodo de análisis,
- datos faltantes,
- representatividad del punto virtual,
- validación contra observaciones cuando existan.

