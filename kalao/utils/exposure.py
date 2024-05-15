import numpy as np

import config


def magnitude_to_exposure_time(mag: float, target_adu: float, filter: str,
                               fwhm: float = 1) -> float:
    exptime = 10**((mag - config.Exposure.Star.mag_ref) /
                   2.5) * config.Exposure.Star.exptime_ref

    # Adjust for target ADUs
    exptime *= target_adu / config.Exposure.Star.adu_ref

    # Adjust taking into account filters transmission, camera QE
    exptime /= config.Exposure.filters_relative_flux[filter]

    # Adjust for FWHM
    exptime *= (fwhm / config.Exposure.Star.fwhm_ref)**2

    return exptime


def magnitude_to_adu(mag: float, exptime: float, filter: str,
                     fwhm: float = 1) -> float:
    adu = 10**((config.Exposure.Star.mag_ref - mag) /
               2.5) * config.Exposure.Star.adu_ref

    # Adjust for exposure time
    adu *= exptime / config.Exposure.Star.exptime_ref

    # Adjust taking into account filters transmission, camera QE
    adu *= config.Exposure.filters_relative_flux[filter]

    # Adjust for FWHM
    adu /= (fwhm / config.Exposure.Star.fwhm_ref)**2

    return adu


def optimal_exposure_time_and_filter(
        mag: float, min_exptime: float,
        min_adu: float = config.Exposure.Star.min_adu,
        max_adu: float = config.Exposure.Star.max_adu,
        filter_list: list[str] = config.Exposure.Star.filter_list,
        fwhm: float = 1) -> tuple[float, str]:
    return _try_filter(filter_list, mag, min_exptime, min_adu, max_adu, fwhm)


def _try_filter(filter_list: list[str], mag: float, min_exptime: float,
                min_adu: float, max_adu: float,
                fwhm: float) -> tuple[float, str]:
    # Note: this function assume filters are ordered by decreasing transmission

    filter = filter_list[0]

    adu = magnitude_to_adu(mag, min_exptime, filter, fwhm=fwhm)

    if min_adu <= adu <= max_adu:
        return min_exptime, filter
    elif adu < min_adu:
        # Increase exposure time, keeping current filter
        exptime = magnitude_to_exposure_time(mag, min_adu, filter, fwhm=fwhm)
        return exptime, filter
    else:  # adu > max_adu
        if len(filter_list) == 1:
            return min_exptime, filter
        else:
            # Try next filter
            return _try_filter(filter_list[1:], mag, min_exptime, min_adu,
                               max_adu, fwhm)


def flat_exptime(target_adu: float, filter: str) -> float:
    exptime = config.Exposure.SkyFlat.exptime_ref

    # Adjust for target ADUs
    exptime *= target_adu / config.Exposure.SkyFlat.adu_ref

    # Adjust taking into account filters transmission, camera QE
    exptime /= config.Exposure.filters_relative_flux[filter]

    return exptime


def next_flat_exptime(target_adu: float, prev_img: np.ndarray,
                      prev_exptime: float, prev_filter: str,
                      next_filter: str) -> float:
    prev_adu = prev_img.median()

    # Start with previous exposure time
    exptime = prev_exptime

    # Adjust for ADUs
    exptime *= (target_adu - config.Camera.median_bias) / (
        prev_adu - config.Camera.median_bias)

    # Adjust for filters transmission, camera QE
    exptime *= config.Exposure.filters_relative_flux[
        prev_filter] / config.Exposure.filters_relative_flux[next_filter]

    return exptime
