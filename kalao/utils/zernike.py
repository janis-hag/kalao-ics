import math

import numpy as np


class Zernike:

    def Z(n, m, rho, phi):
        if m == 0:
            return Zernike.N(n, m) * Zernike.R(n, m, rho)
        elif m > 0:
            return Zernike.N(n, m) * Zernike.R(n, m, rho) * np.cos(m * phi)
        else:
            return Zernike.N(n, -m) * Zernike.R(n, -m, rho) * np.sin(-m * phi)

    def N(n, m):
        return 1

        # if m == 0:
        #     return np.sqrt(n + 1)
        # else:
        #     return np.sqrt(2 * n + 2)

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
