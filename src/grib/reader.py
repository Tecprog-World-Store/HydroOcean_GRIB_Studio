from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import cfgrib

LAT_NAMES = ("latitude", "lat", "y")
LON_NAMES = ("longitude", "lon", "x")

class GribReader:
    def __init__(self):
        self.path = None
        self.datasets = []

    def open(self, path):
        self.path = Path(path)
        self.datasets = cfgrib.open_datasets(
            str(self.path),
            backend_kwargs={"indexpath": ""}
        )
        return self.datasets

    def inventory(self):
        rows = []
        for i, ds in enumerate(self.datasets):
            for name, da in ds.data_vars.items():
                rows.append({
                    "dataset": i,
                    "variable": name,
                    "shortName": da.attrs.get("GRIB_shortName", ""),
                    "long_name": da.attrs.get("long_name", da.attrs.get("GRIB_name", "")),
                    "units": da.attrs.get("units", ""),
                    "dims": ", ".join(da.dims),
                    "shape": str(tuple(da.shape))
                })
        return pd.DataFrame(rows)

    def _coord_name(self, ds, candidates):
        for n in candidates:
            if n in ds.coords:
                return n
        for n in candidates:
            if n in ds.dims:
                return n
        return None

    @staticmethod
    def _normalize_query_names(names):
        return {str(n).lower() for n in names}

    def find_variable(self, names):
        targets = self._normalize_query_names(names)
        for ds_i, ds in enumerate(self.datasets):
            for var, da in ds.data_vars.items():
                options = {
                    var.lower(),
                    str(da.attrs.get("GRIB_shortName", "")).lower(),
                    str(da.attrs.get("GRIB_name", "")).lower(),
                    str(da.attrs.get("standard_name", "")).lower(),
                }
                if targets.intersection(options):
                    return ds_i, var
        return None

    def extract_point(self, ds_i, var_name, lat, lon):
        ds = self.datasets[ds_i]
        da = ds[var_name]

        lat_name = self._coord_name(ds, LAT_NAMES)
        lon_name = self._coord_name(ds, LON_NAMES)

        if lat_name is None or lon_name is None:
            raise ValueError(
                f"No se identificaron coordenadas lat/lon en dataset {ds_i}. "
                f"Coords: {list(ds.coords)}"
            )

        lon_coord = ds[lon_name]
        requested_lon = float(lon)

        try:
            lon_min = float(lon_coord.min())
            lon_max = float(lon_coord.max())
            if lon_min >= 0 and requested_lon < 0:
                requested_lon = requested_lon % 360
        except Exception:
            pass

        # Caso común: lat/lon 1D.
        if ds[lat_name].ndim == 1 and ds[lon_name].ndim == 1:
            point = da.sel(
                {lat_name: float(lat), lon_name: requested_lon},
                method="nearest"
            )
            actual_lat = float(point[lat_name].values)
            actual_lon = float(point[lon_name].values)
        else:
            # Grilla curvilínea: localización por distancia euclidiana aproximada.
            latv = np.asarray(ds[lat_name].values)
            lonv = np.asarray(ds[lon_name].values)
            dlon = ((lonv - requested_lon + 180) % 360) - 180
            dist2 = (latv - float(lat))**2 + dlon**2
            idx = np.unravel_index(np.nanargmin(dist2), dist2.shape)
            spatial_dims = ds[lat_name].dims
            indexers = {d: idx[j] for j, d in enumerate(spatial_dims)}
            point = da.isel(indexers)
            actual_lat = float(ds[lat_name].isel(indexers).values)
            actual_lon = float(ds[lon_name].isel(indexers).values)

        return point.squeeze(drop=True), actual_lat, actual_lon

    def extract_series(self, aliases, lat, lon):
        found = self.find_variable(aliases)
        if not found:
            return None
        ds_i, var = found
        da, actual_lat, actual_lon = self.extract_point(ds_i, var, lat, lon)

        # Convertir DataArray a Series intentando preservar eje temporal.
        time_coord = None
        for candidate in ("valid_time", "time", "step"):
            if candidate in da.coords and da[candidate].ndim > 0:
                time_coord = candidate
                break

        values = np.asarray(da.values).reshape(-1)

        if "valid_time" in da.coords:
            t = np.asarray(da["valid_time"].values).reshape(-1)
            if len(t) == len(values):
                index = pd.to_datetime(t)
            else:
                index = pd.RangeIndex(len(values), name="sample")
        elif "time" in da.coords and da["time"].size == len(values):
            index = pd.to_datetime(np.asarray(da["time"].values).reshape(-1))
        elif "step" in da.coords and da["step"].size == len(values):
            index = pd.Index(np.asarray(da["step"].values).reshape(-1), name="step")
        else:
            index = pd.RangeIndex(len(values), name="sample")

        return {
            "series": pd.Series(values, index=index, name=var),
            "variable": var,
            "dataset": ds_i,
            "units": da.attrs.get("units", ""),
            "actual_lat": actual_lat,
            "actual_lon": actual_lon,
            "attrs": dict(da.attrs),
        }
