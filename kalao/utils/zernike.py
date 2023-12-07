import math

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from astropy.nddata import block_reduce, block_replicate

coeff_names = {
    (0, 0): 'Piston',
    (1, -1): 'Tip',
    (1, 1): 'Tilt',
    (2, -2): 'Oblique astigmatism',
    (2, 0): 'Defocus',
    (2, 2): 'Vertical astigmatism',
    (3, -3): 'Vertical trefoil',
    (3, -1): 'Vertical coma',
    (3, 1): 'Horizontal coma',
    (3, 3): 'Oblique trefoil',
    (4, -4): 'Oblique quadrafoil',
    (4, -2): 'Oblique secondary astigmatism',
    (4, 0): 'Primary spherical',
    (4, 2): 'Vertical secondary astigmatism',
    (4, 4): 'Vertical quadrafoil',
}


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
        # Coeffs will be wavefront RMS
        if norm == 'orthonormal' or norm == 'RMS':
            if m == 0:
                return np.sqrt(n + 1)
            else:
                return np.sqrt(2*n + 2)

        # Coeffs will be wavefront Peak-to-Peak
        else:
            return 1

    def R(n, m, rho):
        if (n-m) % 2 == 1:
            return np.zeros_like(rho)

        R = 0

        for k in range((n-m) // 2 + 1):
            R += (-1)**k * np.math.factorial(n - k) / (
                np.math.factorial(k) * np.math.factorial((n+m) // 2 - k) *
                np.math.factorial((n-m) // 2 - k)) * rho**(n - 2*k)

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
        return (n * (n+1)) // 2 + np.abs(l) + Zernike.noll_complement(n, l)

    def noll_inverse(j):
        n = math.ceil((-3 + np.sqrt(8*j + 1)) / 2)

        l_sign = 1 if j % 2 == 0 else -1
        l = l_sign * (j - n * (n+1) / 2 - Zernike.noll_complement(n, l_sign))

        return n, l

    def standard(n, l):
        return (n * (n+2) + l) // 2

    def standard_inverse(j):
        n = math.ceil((-3 + np.sqrt(8*j + 9)) / 2)
        l = 2*j - n * (n+2)

        return n, l


def generate_pattern(coeffs, shape, indices_inverse=Zernike.standard_inverse):
    x = np.linspace(-1, 1, shape[0])
    y = np.linspace(-1, 1, shape[1])

    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)

    pattern = np.zeros(shape)

    for i, coeff in enumerate(coeffs):
        n, m = indices_inverse(i)
        pattern += coeff * Zernike.Z(n, m, R, Theta)

    return pattern


def _slopes_from_pattern(pattern):
    # Differentiate
    slopes = np.gradient(pattern, 2 / (pattern.shape[0] - 1),
                         2 / (pattern.shape[1] - 1))

    return np.hstack(slopes)


def generate_slopes(coeffs, shape, upsampling=4,
                    indices_inverse=Zernike.standard_inverse):
    pattern = generate_pattern(coeffs,
                               np.array(shape) * upsampling, indices_inverse)

    slopes = _slopes_from_pattern(pattern)

    # Downsample
    return block_reduce(slopes, upsampling, np.mean)


def fit_pattern(pattern, orders=None, mask=None):
    if orders is None:
        orders = 2 * pattern.size + 1

    # Generate the basis
    pattern_basis = []
    for i in range(orders):
        coeffs = np.zeros((orders, ))
        coeffs[i] = 1

        _pattern = generate_pattern(coeffs, pattern.shape)
        _pattern_masked = np.ma.masked_array(_pattern, mask=mask)

        pattern_basis.append(_pattern_masked)

    pattern_basis = np.ma.stack(pattern_basis)
    pattern = np.ma.masked_array(pattern, mask=mask)

    fit_coeffs, residuals, rank, s = np.linalg.lstsq(
        pattern_basis.compressed().reshape(orders,
                                           pattern.compressed().size).T,
        pattern.compressed())

    return fit_coeffs


def fit_slopes(slopes, orders=None, mask=None):
    if orders is None:
        orders = slopes.size + 1

    shape = (slopes.shape[0], slopes.shape[1] // 2)

    # Generate the basis
    slopes_basis = []
    for i in range(orders):
        coeffs = np.zeros((orders, ))
        coeffs[i] = 1

        _slopes = generate_slopes(coeffs, shape)
        _slopes_masked = np.ma.masked_array(_slopes, mask=mask)

        slopes_basis.append(_slopes_masked)

    slopes_basis = np.ma.stack(slopes_basis)
    slopes = np.ma.masked_array(slopes, mask=mask)

    fit_coeffs, residuals, rank, s = np.linalg.lstsq(
        slopes_basis.compressed().reshape(orders,
                                          slopes.compressed().size).T,
        slopes.compressed())

    return fit_coeffs


def slopes_from_pattern_fit(pattern, orders=None):
    fit_coeffs = fit_pattern(pattern, orders=orders)
    shape = np.array(pattern.shape) - 1

    return generate_slopes(fit_coeffs, shape)


def slopes_from_pattern_interp(pattern, upsampling=4):
    pattern = block_replicate(pattern, upsampling)

    x = np.arange(pattern.shape[0])
    y = np.arange(pattern.shape[1])

    interp = RegularGridInterpolator((x, y), pattern)

    x = (x[upsampling:] + x[:-upsampling]) / 2
    y = (y[upsampling:] + y[:-upsampling]) / 2

    X, Y = np.meshgrid(x, y, indexing='ij')

    pattern = interp((X, Y))

    slopes = _slopes_from_pattern(pattern)

    slopes = block_reduce(slopes, upsampling)

    return slopes


def get_coeff_name(i, indices_inverse=Zernike.standard_inverse):
    n, m = indices_inverse(i)

    return coeff_names.get((n, m), "Higher order"), (n, m)


def print_coeffs(coeffs, unit='', indices_inverse=Zernike.standard_inverse):
    for coeff, value in enumerate(coeffs):
        name, (n, m) = get_coeff_name(coeff, indices_inverse)

        print(f'({n: 2},{m: 2}) {value: f}{unit} {name}')


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    coeffs = [1, 0.5, 4, 0.2, -0.4, -2]

    fig, axs = plt.subplots(2, 2)

    pattern = generate_pattern(coeffs, (12, 12))
    slopes = generate_slopes(coeffs, (11, 11))

    #fit_coeffs = fit_pattern(pattern)
    #fit_pattern = generate_pattern(fit_coeffs, (12, 12))
    #fit_slopes = generate_slopes(fit_coeffs, (11, 11))

    #mask = kalao_tools.generate_slopes_mask_from_subaps(config.AO.masked_subaps)
    #coeffs = fit_slopes(slopes, 25, mask)

    fit_slopes = slopes_from_pattern_interp(pattern)

    axs[0, 0].imshow(pattern, cmap='gray')
    #axs[1, 0].imshow(fit_pattern, cmap='gray')
    axs[0, 1].imshow(slopes, cmap='gray')
    axs[1, 1].imshow(fit_slopes, cmap='gray')

    print(slopes.min(), slopes.max())
    print(fit_slopes.min(), fit_slopes.max())

    plt.show()
