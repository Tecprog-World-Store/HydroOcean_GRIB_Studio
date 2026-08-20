from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import cfgrib

LAT_NAMES = ("latitude", "lat", "y")
LON_NAMES = ("longitude", "lon", "x")

ALIASES = {
    "wind_u": ["u", "ugrd", "u10"],
    "wind_v": ["v", "vgrd", "v10"],
    "wind_speed": ["ws", "wind", "si10"],
    "wind_direction": ["wdir"],
    "wave_height": ["swh", "htsgw"],
    "wave_period": ["perpw", "mwp"],
    "wave_direction": ["dirpw", "mwd"],
    "current_u": ["uo", "uogrd", "eastcur"],
    "current_v": ["vo", "vogrd", "nrthcur"],
    "current_speed": ["spc"],
    "current_direction": ["dirc"],
}

class GribFile:
    def __init__(self, path):
        self.path = Path(path)
        self.datasets = []

    def open(self):
        self.datasets = cfgrib.open_datasets(
            str(self.path),
            backend_kwargs={"indexpath": ""}
        )
        return self

    def inventory(self):
        rows = []
        for i, ds in enumerate(self.datasets):
            for var, da in ds.data_vars.items():
                rows.append({
                    "file": self.path.name,
                    "dataset": i,
                    "variable": var,
                    "shortName": da.attrs.get("GRIB_shortName", ""),
                    "long_name": da.attrs.get("long_name", da.attrs.get("GRIB_name", "")),
                    "units": da.attrs.get("units", ""),
                    "dims": ", ".join(da.dims),
                    "shape": str(tuple(da.shape)),
                })
        return pd.DataFrame(rows)

    @staticmethod
    def _norm(x):
        return str(x or "").strip().lower()

    def find(self, aliases):
        targets = {self._norm(x) for x in aliases}
        for di, ds in enumerate(self.datasets):
            for var, da in ds.data_vars.items():
                names = {
                    self._norm(var),
                    self._norm(da.attrs.get("GRIB_shortName")),
                    self._norm(da.attrs.get("GRIB_name")),
                    self._norm(da.attrs.get("standard_name")),
                }
                if names & targets:
                    return di, var
        return None

    def _coord(self, ds, candidates):
        for name in candidates:
            if name in ds.coords or name in ds.dims:
                return name
        return None

    def extract_dataarray(self, dataset_index, variable, lat, lon):
        ds = self.datasets[dataset_index]
        da = ds[variable]
        lat_name = self._coord(ds, LAT_NAMES)
        lon_name = self._coord(ds, LON_NAMES)
        if not lat_name or not lon_name:
            raise ValueError(f"Sin coordenadas lat/lon en {self.path.name}")

        query_lon = float(lon)
        lons = np.asarray(ds[lon_name].values)
        try:
            if np.nanmin(lons) >= 0 and query_lon < 0:
                query_lon %= 360.0
        except Exception:
            pass

        if ds[lat_name].ndim == 1 and ds[lon_name].ndim == 1:
            point = da.sel(
                {lat_name: float(lat), lon_name: query_lon},
                method="nearest"
            )
            used_lat = float(point[lat_name].values)
            used_lon = float(point[lon_name].values)
        else:
            latv = np.asarray(ds[lat_name].values)
            lonv = np.asarray(ds[lon_name].values)
            dlon = ((lonv - query_lon + 180.0) % 360.0) - 180.0
            d2 = (latv - float(lat))**2 + dlon**2
            idx = np.unravel_index(np.nanargmin(d2), d2.shape)
            indexers = {d: idx[j] for j, d in enumerate(ds[lat_name].dims)}
            point = da.isel(indexers)
            used_lat = float(ds[lat_name].isel(indexers).values)
            used_lon = float(ds[lon_name].isel(indexers).values)
        return point.squeeze(drop=True), used_lat, used_lon

    @staticmethod
    def _valid_time(point):
        # Captura también coordenadas escalares; esto corrige el problema f000.
        for name in ("valid_time", "time"):
            if name in point.coords:
                val = np.asarray(point.coords[name].values)
                if val.size == 1:
                    try:
                        return pd.Timestamp(val.reshape(-1)[0])
                    except Exception:
                        pass
        return None

    def extract_scalar(self, alias_key, lat, lon):
        found = self.find(ALIASES[alias_key])
        if not found:
            return None
        di, var = found
        point, used_lat, used_lon = self.extract_dataarray(di, var, lat, lon)
        values = np.asarray(point.values).reshape(-1)

        if values.size != 1:
            # Si el propio archivo ya tiene tiempo, devolver registros.
            recs = []
            if "valid_time" in point.coords:
                times = np.asarray(point.coords["valid_time"].values).reshape(-1)
            elif "time" in point.coords and np.asarray(point.coords["time"].values).size == values.size:
                times = np.asarray(point.coords["time"].values).reshape(-1)
            else:
                times = [None] * values.size
            for t, value in zip(times, values):
                recs.append({
                    "time": pd.Timestamp(t) if t is not None else None,
                    "value": float(value),
                    "variable": var,
                    "units": point.attrs.get("units", ""),
                    "lat": used_lat,
                    "lon": used_lon,
                })
            return recs

        return [{
            "time": self._valid_time(point),
            "value": float(values[0]),
            "variable": var,
            "units": point.attrs.get("units", ""),
            "lat": used_lat,
            "lon": used_lon,
        }]
