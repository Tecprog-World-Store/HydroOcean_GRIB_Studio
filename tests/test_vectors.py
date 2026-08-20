import numpy as np
from src.analysis.vectors import (
    speed_from_uv, meteorological_from_direction, oceanographic_to_direction
)

def test_speed():
    assert np.isclose(speed_from_uv(3,4), 5)

def test_north_wind():
    assert np.isclose(meteorological_from_direction(0,-1), 0)

def test_east_current():
    assert np.isclose(oceanographic_to_direction(1,0), 90)
