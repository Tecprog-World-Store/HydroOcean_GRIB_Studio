from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import time
import requests

FILTER_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"

DEFAULT_VARS = (
    "WIND", "WDIR", "UGRD", "VGRD", "HTSGW", "PERPW", "DIRPW"
)

@dataclass
class Domain:
    north: float = 1.0
    south: float = -20.0
    west: float = -90.0
    east: float = -68.0

def filename(cycle, fh):
    return f"gfswave.t{cycle}z.global.0p25.f{fh:03d}.grib2"

def directory(day, cycle):
    return f"/gfs.{day:%Y%m%d}/{cycle}/wave/gridded"

def build_params(day, cycle, fh, domain, variables):
    p = {
        "file": filename(cycle, fh),
        "lev_surface": "on",
        "subregion": "",
        "toplat": str(domain.north),
        "leftlon": str(domain.west),
        "rightlon": str(domain.east),
        "bottomlat": str(domain.south),
        "dir": directory(day, cycle),
    }
    for var in variables:
        p[f"var_{var}"] = "on"
    return p

def download_one(day, cycle, fh, domain, variables, out_dir, timeout=180):
    out_dir = Path(out_dir)
    target_dir = out_dir / f"{day:%Y%m%d}" / cycle
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename(cycle, fh)
    if target.exists() and target.stat().st_size > 4:
        return target, "cached"

    headers = {"User-Agent": "HydroOcean-GRIB-Studio/0.2 Tecprog-World"}
    with requests.get(
        FILTER_URL,
        params=build_params(day, cycle, fh, domain, variables),
        headers=headers,
        timeout=timeout,
        stream=True,
    ) as r:
        r.raise_for_status()
        first = r.raw.read(4)
        if first != b"GRIB":
            sample = first + r.raw.read(250)
            raise RuntimeError(
                f"NOAA no devolvió GRIB para {day} {cycle} f{fh:03d}. "
                f"Respuesta: {sample[:180]!r}"
            )
        with target.open("wb") as f:
            f.write(first)
            for chunk in iter(lambda: r.raw.read(1024*1024), b""):
                f.write(chunk)
    return target, "downloaded"

def forecast_hours(start, end, step):
    if step <= 0 or end < start:
        raise ValueError("Rango de pronóstico inválido.")
    return list(range(start, end + 1, step))

def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def download_forecast_run(day, cycle, f_start, f_end, step, domain,
                          variables, out_dir, pause=10, callback=None):
    hrs = forecast_hours(f_start, f_end, step)
    results = []
    for i, fh in enumerate(hrs, 1):
        if callback:
            callback(i, len(hrs), f"{day:%Y-%m-%d} {cycle}Z f{fh:03d}")
        try:
            p, status = download_one(day, cycle, fh, domain, variables, out_dir)
            results.append((p, status, None))
        except Exception as exc:
            results.append((None, "error", str(exc)))
        if i < len(hrs):
            time.sleep(pause)
    return results

def download_analysis_range(start_day, end_day, cycles, domain,
                            variables, out_dir, pause=10, callback=None):
    # Para una serie cronológica operacional descargamos f000 de cada ciclo.
    jobs = [(d, c) for d in daterange(start_day, end_day) for c in cycles]
    results = []
    for i, (d, c) in enumerate(jobs, 1):
        if callback:
            callback(i, len(jobs), f"{d:%Y-%m-%d} {c}Z f000")
        try:
            p, status = download_one(d, c, 0, domain, variables, out_dir)
            results.append((p, status, None))
        except Exception as exc:
            results.append((None, "error", str(exc)))
        if i < len(jobs):
            time.sleep(pause)
    return results
