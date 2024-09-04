from dataclasses import dataclass

import numpy as np

import config


@dataclass
class SpiralCoord:
    radius: int
    theta: float
    dx: float
    dy: float


def generate_grid(overlap: float, radius: int):
    dx = config.Camera.size_x * (1-overlap)
    dy = config.Camera.size_y * (1-overlap)

    dxs = np.arange(-radius, radius + 1)
    dys = np.arange(-radius, radius + 1)

    dxs_grid, dys_grid = np.meshgrid(dxs, dys)

    radius_grid = np.rint(np.sqrt(dxs_grid**2 + dys_grid**2)).astype(int)
    thetas_grid = np.arctan2(dys_grid, dxs_grid) % (2 * np.pi)

    coords = []
    for i in range(radius_grid.shape[0]):
        for j in range(radius_grid.shape[1]):
            if radius_grid[i, j] <= radius:
                coords.append(
                    SpiralCoord(radius=radius_grid[i, j], theta=thetas_grid[i,
                                                                            j],
                                dx=dxs_grid[i, j] * dx,
                                dy=dys_grid[i, j] * dy))

    return sorted(coords, key=lambda c: (c.radius, c.theta))
