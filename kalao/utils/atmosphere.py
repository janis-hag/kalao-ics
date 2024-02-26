from typing import Callable

import numpy as np

# Conventions:
# Temperature in K
# Pressure in Pa
# Hygrometry between 0 and 1


# Owens 1967 formula
def air_refractive_index_OWENS(lambda0_: float, T: float, P: float,
                               H: float) -> float:
    sig = 1. / (lambda0_*1e6)
    P = P / 100
    t = T - 273.15

    Pw_sat = 6.11 * 10**((7.5*t) / (t+237.7))
    Pw = Pw_sat * H
    Ps = P - Pw

    Ds = Ps / T * (1 + Ps * (57.90e-8 - 9.3250e-4/T + 0.25844 / T**2))
    Dw = Pw / T * (
        1 + Pw * (1 + 3.70e-4*Pw) *
        (-2.37321e-3 + 2.23366/T - 710.792 / T**2 + 7.75141e4 / T**3))

    n = (2371.34 + 683939.7 / (130. - sig**2) + 4547.3 /
         (38.9 - sig**2)) * Ds + (6487.31 + 58.058 * sig**2 -
                                  0.71150 * sig**4 + 0.08851 * sig**6) * Dw

    return 1 + n*1e-8


# Edlen 1966 formula
def air_refractive_index_EDLEN(lambda0_: float, T: float, P: float,
                               _) -> float:
    sig = 1. / (lambda0_*1e6)
    p = P / 101325 * 760
    t = T - 273.15

    n = 8342.13 + 2406030 / (130. - sig**2) + 15997. / (38.9 - sig**2)
    n *= 0.00138823 * p / (1 + 0.003671*t)

    return 1 + n*1e-8


def air_dispersion(
    zenith_angle: float, wavelength: float, T: float, P: float, H: float,
    air_refractive_index: Callable[[float, float, float, float],
                                   float] = air_refractive_index_EDLEN
) -> float:
    return np.tan(zenith_angle * np.pi / 180) * air_refractive_index(
        wavelength, T, P, H) * 180 / np.pi * 3600
