import numpy as np
from src.analysis.vectors import (
    speed_from_uv,
    meteorological_from_direction,
    oceanographic_to_direction,
)

def test_speed():
    assert np.isclose(speed_from_uv(3,4), 5)

def test_wind_from_north():
    # Viento que se desplaza al sur => viene del norte.
    d = meteorological_from_direction(0, -1)
    assert np.isclose(d, 0)

def test_current_to_north():
    d = oceanographic_to_direction(0, 1)
    assert np.isclose(d, 0)

def test_current_to_east():
    d = oceanographic_to_direction(1, 0)
    assert np.isclose(d, 90)
