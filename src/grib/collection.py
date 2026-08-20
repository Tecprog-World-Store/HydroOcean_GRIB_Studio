from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
from src.grib.reader import GribFile
from src.analysis.vectors import (
    speed_from_uv,
    meteorological_from_direction,
    oceanographic_to_direction,
)

GRIB_EXTS = {".grib2", ".grb2", ".grib", ".grb"}

def list_gribs(folder):
    folder = Path(folder)
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in GRIB_EXTS)

def _first_record(g, key, lat, lon):
    x = g.extract_scalar(key, lat, lon)
    return x[0] if x else None

def build_product_series(paths, lat, lon, product, progress=None):
    rows = []
    paths = list(paths)
    for n, path in enumerate(paths, start=1):
        if progress:
            progress(n, len(paths), str(path))
        try:
            g = GribFile(path).open()
            base = {"source_file": Path(path).name}

            if product == "Viento":
                u = _first_record(g, "wind_u", lat, lon)
                v = _first_record(g, "wind_v", lat, lon)
                ws = _first_record(g, "wind_speed", lat, lon)
                wd = _first_record(g, "wind_direction", lat, lon)
                ref = u or v or ws or wd
                if not ref:
                    continue
                base["time"] = ref["time"]
                base["grid_lat"] = ref["lat"]
                base["grid_lon"] = ref["lon"]
                if u: base["U_wind_m_s"] = u["value"]
                if v: base["V_wind_m_s"] = v["value"]
                if ws: base["WindSpeed_m_s"] = ws["value"]
                if wd: base["WindDir_from_deg"] = wd["value"]
                if u and v:
                    base["WindSpeed_m_s"] = float(speed_from_uv(u["value"], v["value"]))
                    base["WindDir_from_deg"] = float(
                        meteorological_from_direction(u["value"], v["value"])
                    )

            elif product == "Oleaje":
                hs = _first_record(g, "wave_height", lat, lon)
                tp = _first_record(g, "wave_period", lat, lon)
                dr = _first_record(g, "wave_direction", lat, lon)
                ref = hs or tp or dr
                if not ref:
                    continue
                base["time"] = ref["time"]
                base["grid_lat"] = ref["lat"]
                base["grid_lon"] = ref["lon"]
                if hs: base["Hs_m"] = hs["value"]
                if tp: base["Period_s"] = tp["value"]
                if dr: base["WaveDir_deg"] = dr["value"]

            else:
                u = _first_record(g, "current_u", lat, lon)
                v = _first_record(g, "current_v", lat, lon)
                sp = _first_record(g, "current_speed", lat, lon)
                dr = _first_record(g, "current_direction", lat, lon)
                ref = u or v or sp or dr
                if not ref:
                    continue
                base["time"] = ref["time"]
                base["grid_lat"] = ref["lat"]
                base["grid_lon"] = ref["lon"]
                if u: base["U_current_m_s"] = u["value"]
                if v: base["V_current_m_s"] = v["value"]
                if sp: base["CurrentSpeed_m_s"] = sp["value"]
                if dr: base["CurrentDir_to_deg"] = dr["value"]
                if u and v:
                    base["CurrentSpeed_m_s"] = float(speed_from_uv(u["value"], v["value"]))
                    base["CurrentDir_to_deg"] = float(
                        oceanographic_to_direction(u["value"], v["value"])
                    )
            rows.append(base)
        except Exception as exc:
            rows.append({
                "source_file": Path(path).name,
                "_error": str(exc),
                "time": pd.NaT
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Excluir filas error de la tabla científica, pero conservar log aparte en GUI.
    good = df[df.get("_error", pd.Series(index=df.index, dtype=object)).isna()] if "_error" in df else df
    if good.empty:
        return good

    good = good.copy()
    good["time"] = pd.to_datetime(good["time"], errors="coerce", utc=True)
    # Si no hay valid_time, mantener orden de archivos sin inventar fecha.
    if good["time"].notna().any():
        good = good.sort_values("time").drop_duplicates(subset=["time"], keep="last")
        good = good.set_index("time")
    else:
        good.index = pd.RangeIndex(len(good), name="sample")
    return good
