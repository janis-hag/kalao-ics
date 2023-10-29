import math

import numpy as np


class Zernike:

    def Z(n, m, rho, phi, norm=None):
        if m == 0:
            return Zernike.N(n, m, norm) * Zernike.R(n, m, rho)
        elif m > 0:
            return Zernike.N(n, m, norm) * Zernike.R(n, m, rho) * np.cos(
                    m * phi)
        else:
            return Zernike.N(n, -m, norm) * Zernike.R(n, -m, rho) * np.sin(
                    -m * phi)

    def N(n, m, norm=None):
        if norm == 'orthonormal':
            if m == 0:
                return np.sqrt(n + 1)
            else:
                return np.sqrt(2 * n + 2)

        else:
            return 1

    def R(n, m, rho):
        if (n - m) % 2 == 1:
            return np.zeros_like(rho)

        R = 0

        for k in range((n - m) // 2 + 1):
            R += (-1)**k * np.math.factorial(n - k) / (
                    np.math.factorial(k) * np.math.factorial((n + m) // 2 - k)
                    * np.math.factorial((n - m) // 2 - k)) * rho**(n - 2 * k)

        return R

    def noll_complement(n, l):
        if l > 0 and (n % 4 == 0 or n % 4 == 1):
            return 0
        elif l < 0 and (n % 4 == 2 or n % 4 == 3):
            return 0
        elif l >= 0 and (n % 4 == 2 or n % 4 == 3):
            return 1
        elif l <= 0 and (n % 4 == 0 or n % 4 == 1):
            return 1

    def noll(n, l):
        return (n * (n + 1)) // 2 + np.abs(l) + Zernike.noll_complement(n, l)

    def noll_inverse(j):
        n = math.ceil((-3 + np.sqrt(8 * j + 1)) / 2)

        l_sign = 1 if j % 2 == 0 else -1
        l = l_sign * (j - n * (n + 1) / 2 - Zernike.noll_complement(n, l_sign))

        return n, l

    def standard(n, l):
        return (n * (n + 2) + l) // 2

    def standard_inverse(j):
        n = math.ceil((-3 + np.sqrt(8 * j + 9)) / 2)
        l = 2 * j - n * (n + 2)

        return n, l


def generate_pattern(zernike_coeffs, sampling,
                     indices_inverse=Zernike.standard_inverse):
    x = np.linspace(-1, 1, sampling[0])
    y = np.linspace(-1, 1, sampling[1])

    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)

    pattern = np.zeros(sampling)

    for i, coeff in enumerate(zernike_coeffs):
        n, m = indices_inverse(i)
        pattern += coeff * Zernike.Z(n, m, R, Theta)

    return pattern


def generate_slopes(zernike_coeffs, sampling, upsampling_factor=4,
                    indices_inverse=Zernike.standard_inverse):
    sampling_up = np.array(sampling) * upsampling_factor

    pattern = generate_pattern(zernike_coeffs, sampling_up, indices_inverse)

    slopes = np.hstack(
            np.gradient(pattern, 2 / (sampling_up[0] - 1),
                        2 / (sampling_up[1] - 1)))

    # Downsample
    slopes = np.mean(
            slopes.reshape((sampling[0], upsampling_factor, 2 * sampling[1],
                            upsampling_factor)).transpose((0, 2, 1, 3)),
            (2, 3))

    return slopes
