from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import time
import requests

FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"

@dataclass
class GFSWaveRequest:
    date: str
    cycle: str
    forecast_hour: int
    north: float
    south: float
    west: float
    east: float
    parameters: tuple[str, ...] = (
        "WIND", "WDIR", "UGRD", "VGRD",
        "HTSGW", "PERPW", "DIRPW"
    )

    @property
    def forecast(self):
        return f"{int(self.forecast_hour):03d}"

    @property
    def filename_candidates(self):
        # NOAA ha empleado más de una convención de nombre a lo largo del tiempo.
        # Se prueban las variantes más comunes sin raspar HTML.
        c = self.cycle
        f = self.forecast
        return (
            f"gfswave.t{c}z.global.0p25.f{f}.grib2",
            f"gfswave.t{c}z.0p25.f{f}.grib2",
        )

    @property
    def directory_candidates(self):
        return (
            f"/gfs.{self.date}/{self.cycle}/wave/gridded",
            f"/gfs.{self.date}/{self.cycle}/wave/gridded/",
        )

def build_params(req: GFSWaveRequest, filename, directory):
    p = {
        "file": filename,
        "lev_surface": "on",
        "subregion": "",
        "toplat": str(req.north),
        "leftlon": str(req.west),
        "rightlon": str(req.east),
        "bottomlat": str(req.south),
        "dir": directory,
    }
    for var in req.parameters:
        p[f"var_{var}"] = "on"
    return p

def download_gfswave(req: GFSWaveRequest, output_dir, timeout=120):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    errors = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "HydroOcean-GRIB-Studio/0.1 (+engineering research client)"
    })

    first = True
    for directory in req.directory_candidates:
        for filename in req.filename_candidates:
            if not first:
                # NOAA recomienda espaciar solicitudes automatizadas.
                time.sleep(10)
            first = False

            try:
                r = session.get(
                    FILTER_URL,
                    params=build_params(req, filename, directory),
                    timeout=timeout,
                    stream=True,
                )
                r.raise_for_status()

                ctype = r.headers.get("Content-Type", "").lower()
                head = r.raw.read(4)
                # GRIB comienza normalmente con ASCII 'GRIB'.
                if head != b"GRIB":
                    sample = head + r.raw.read(200)
                    errors.append(
                        f"{filename} en {directory}: respuesta no GRIB "
                        f"({ctype}) {sample[:120]!r}"
                    )
                    continue

                out = output_dir / filename
                with out.open("wb") as fh:
                    fh.write(head)
                    for chunk in iter(lambda: r.raw.read(1024 * 1024), b""):
                        fh.write(chunk)
                return out
            except Exception as exc:
                errors.append(f"{filename} en {directory}: {exc}")

    raise RuntimeError(
        "No se pudo descargar el archivo GFS-Wave.\n" +
        "\n".join(errors[-6:]) +
        "\nVerifique disponibilidad de fecha/ciclo en NOMADS."
    )
