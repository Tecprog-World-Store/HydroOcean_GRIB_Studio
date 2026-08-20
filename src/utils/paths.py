from pathlib import Path
import sys

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).resolve().parents[2] / relative

def project_path(relative):
    # Para ejecución desde código fuente.
    return Path(__file__).resolve().parents[2] / relative

def user_data_dir():
    p = Path.home() / "Documents" / "HydroOcean GRIB Studio"
    p.mkdir(parents=True, exist_ok=True)
    return p
