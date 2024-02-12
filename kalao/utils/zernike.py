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
        elif norm == 'P2P' or norm == 'P2V':
            return 0.5

        # Coeffs will be wavefront Amplitude
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


def generate_pattern_mask(shape):
    rx = 1 - 1 / shape[0]
    ry = 1 - 1 / shape[1]

    x = np.linspace(-rx, rx, shape[0])
    y = np.linspace(-ry, ry, shape[1])

    X, Y = np.meshgrid(x, y, indexing='ij')

    R = np.sqrt(X**2 + Y**2)

    return R > 1


def _slopes_mask_from_pattern_mask(mask):
    mask = mask[0:-1, 0:-1] | mask[1:, 0:-1] | mask[0:-1, 1:] | mask[1:, 1:]
    return np.hstack([mask, mask])


def generate_slopes_mask(shape):
    mask = generate_pattern_mask((shape[0] + 1, shape[1] // 2 + 1))
    return _slopes_mask_from_pattern_mask(mask)


def generate_pattern(coeffs, shape, indices_inverse=Zernike.standard_inverse):
    rx = 1 - 1 / shape[0]
    ry = 1 - 1 / shape[1]

    x = np.linspace(-rx, rx, shape[0])
    y = np.linspace(-ry, ry, shape[1])

    X, Y = np.meshgrid(x, y, indexing='ij')

    R = np.sqrt(X**2 + Y**2)
    Theta = np.arctan2(Y, X)

    pattern = np.zeros(shape)

    for i, coeff in enumerate(coeffs):
        n, m = indices_inverse(i)
        pattern += coeff * Zernike.Z(n, m, R, Theta, norm='RMS')

    return np.ma.masked_array(pattern, mask=generate_pattern_mask(shape),
                              fill_value=np.nan)


def _slopes_from_pattern(pattern):
    dx = 2 / pattern.shape[0]
    dy = 2 / pattern.shape[1]

    # Differentiate
    slopes = np.gradient(pattern, dx, dy)

    return np.hstack(slopes)


def generate_slopes(coeffs, shape, upsampling=2,
                    indices_inverse=Zernike.standard_inverse):
    pattern = generate_pattern(coeffs, (shape[0] * upsampling,
                                        shape[1] // 2 * upsampling),
                               indices_inverse)

    slopes = _slopes_from_pattern(pattern.data)

    # Downsample
    slopes = block_reduce(slopes, upsampling, np.mean)

    return np.ma.masked_array(slopes, mask=generate_slopes_mask(shape),
                              fill_value=np.nan)


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

    # Generate the basis
    slopes_basis = []
    for i in range(orders):
        coeffs = np.zeros((orders, ))
        coeffs[i] = 1

        _slopes = generate_slopes(coeffs, slopes.shape)
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
    return generate_slopes(fit_coeffs,
                           (pattern.shape[0] - 1, 2 * pattern.shape[1] - 2))


def slopes_from_pattern_interp(pattern, upsampling=4):
    pattern_ = block_replicate(pattern.data, upsampling)

    x = np.arange(pattern_.shape[0])
    y = np.arange(pattern_.shape[1])

    interp = RegularGridInterpolator((x, y), pattern_)

    x = (x[upsampling:] + x[:-upsampling]) / 2
    y = (y[upsampling:] + y[:-upsampling]) / 2

    X, Y = np.meshgrid(x, y, indexing='ij')

    pattern_ = interp((X, Y))

    slopes = _slopes_from_pattern(pattern_)
    slopes = block_reduce(slopes, upsampling)

    slopes[0:slopes.shape[0],
           0:slopes.shape[1] // 2] *= 1 + 1 / slopes.shape[0]
    slopes[0:slopes.shape[0], slopes.shape[1] //
           2:slopes.shape[1]] *= 1 + 1 / (slopes.shape[1] // 2)

    return np.ma.masked_array(
        slopes, mask=_slopes_mask_from_pattern_mask(pattern.mask),
        fill_value=pattern.fill_value)


def get_coeff_name(i, indices_inverse=Zernike.standard_inverse):
    n, m = indices_inverse(i)

    return coeff_names.get((n, m), "Higher order"), (n, m)


def print_coeffs(coeffs, unit='', indices_inverse=Zernike.standard_inverse):
    for coeff, value in enumerate(coeffs):
        name, (n, m) = get_coeff_name(coeff, indices_inverse)

        print(f'({n: 2},{m: 2}) {value: f}{unit} {name}')
