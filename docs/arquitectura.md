# Arquitectura técnica

## Capas

### 1. Adquisición
`src/acquisition/`

Responsable de descargar datos desde fuentes oficiales.

La versión inicial implementa GFS-Wave mediante NOMADS Grib Filter.

### 2. Lectura GRIB
`src/grib/`

Usa `xarray + cfgrib + ecCodes`.

Un mismo GRIB2 puede contener mensajes incompatibles dentro de un único hipercubo. Por ello el lector utiliza `cfgrib.open_datasets()` y conserva varios datasets cuando es necesario.

### 3. Extracción espacial
El usuario ingresa latitud/longitud y el software localiza el punto de malla más cercano.

### 4. Análisis
`src/analysis/`

Incluye:
- magnitud de vectores,
- dirección meteorológica,
- dirección oceanográfica,
- binning para rosas.

### 5. Visualización
`src/plots/`

Genera:
- rosa polar,
- serie temporal.

### 6. GUI
`src/gui/`

Tkinter/ttk para minimizar dependencias y permitir operación local rápida.

## Expansiones propuestas

- RTOFS/HYCOM automático para corrientes.
- NDBC/boyas físicas.
- series históricas por rangos de fechas;
- climatologías mensuales;
- percentiles y extremos;
- tablas de persistencia;
- joint probability Hs-Tp;
- exportación XLSX;
- mapas;
- generación de reportes PDF/DOCX;
- empaquetado EXE con PyInstaller;
- backend web/API para incorporar al sitio comercial.
