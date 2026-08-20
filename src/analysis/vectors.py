import numpy as np

def speed_from_uv(u, v):
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    return np.hypot(u, v)

def meteorological_from_direction(u, v):
    '''
    Dirección DESDE donde viene el vector de viento.
    0=N, 90=E, 180=S, 270=O.
    '''
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    return (270.0 - np.degrees(np.arctan2(v, u))) % 360.0

def oceanographic_to_direction(u, v):
    '''
    Dirección HACIA donde se mueve la corriente.
    0=N, 90=E, 180=S, 270=O.
    '''
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    return (90.0 - np.degrees(np.arctan2(v, u))) % 360.0

def compass_label(deg):
    labels = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
              "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = int(((float(deg) % 360) + 11.25) // 22.5) % 16
    return labels[idx]
