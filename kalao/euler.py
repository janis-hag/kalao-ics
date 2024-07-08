from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time

from kalao.interfaces import etcs

import config


def outside_pressure() -> float:
    # Might be updated to take actual value from weather station
    return config.Euler.default_pressure


def outside_temperature() -> float:
    # Might be updated to take actual value from weather station
    return config.Euler.default_temperature


def outside_hygrometry() -> float:
    # Might be updated to take actual value from weather station
    return config.Euler.default_hygrometry


def sun_elevation() -> float:
    time = Time.now()
    altaz_frame = AltAz(location=observing_location(), obstime=time)

    return get_sun(time).transform_to(altaz_frame).alt.deg


def observing_location() -> EarthLocation:
    return EarthLocation(lat=config.Euler.latitude, lon=config.Euler.longitude,
                         height=config.Euler.altitude * u.m)


def telescope_coord_altaz() -> SkyCoord:
    time = Time.now()
    altaz_frame = AltAz(location=observing_location(), obstime=time)

    altitude, azimut = etcs.get_altaz()

    return SkyCoord(alt=altitude * u.degree, az=azimut * u.degree,
                    frame=altaz_frame)


def telescope_zenith_angle(coord: SkyCoord | None = None) -> float:
    if coord is None:
        return 90 - telescope_coord_altaz().alt.deg
    else:
        time = Time.now()
        altaz_frame = AltAz(location=observing_location(), obstime=time)

        return 90 - coord.transform_to(altaz_frame).alt.deg


def telescope_is_tracking() -> bool:
    return etcs.get_tracking()


def telescope_on_kalao() -> bool:
    return etcs.get_instrument() == 3
