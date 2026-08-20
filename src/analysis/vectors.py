import numpy as np

def speed_from_uv(u, v):
    return np.hypot(np.asarray(u, float), np.asarray(v, float))

def meteorological_from_direction(u, v):
    # Dirección DESDE donde sopla el viento.
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    return (270.0 - np.degrees(np.arctan2(v, u))) % 360.0

def oceanographic_to_direction(u, v):
    # Dirección HACIA donde se mueve la corriente.
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    return (90.0 - np.degrees(np.arctan2(v, u))) % 360.0
