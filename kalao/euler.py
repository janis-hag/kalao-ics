from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time

from kalao import database
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


def star_coord() -> SkyCoord:
    star_ra = database.get_last_value('obs', 'target_ra')
    star_dec = database.get_last_value('obs', 'target_dec')

    # TODO verify star_ra and star_dec validity

    coord = SkyCoord(ra=star_ra * u.degree, dec=star_dec * u.degree,
                     frame=config.Euler.frame, equinox=config.Euler.equinox)

    return coord


def telescope_coord_altaz() -> SkyCoord:
    time = Time.now()
    altaz_frame = AltAz(location=observing_location(), obstime=time)

    altitude, azimut = etcs.get_altaz()

    return SkyCoord(alt=altitude * u.degree, az=azimut * u.degree,
                    frame=altaz_frame)


def telescope_zenith_angle() -> float:
    return 90 - telescope_coord_altaz().alt.deg


def telescope_future_zenith_angle(coord: SkyCoord) -> float:
    time = Time.now()
    altaz_frame = AltAz(location=observing_location(), obstime=time)

    return 90 - coord.transform_to(altaz_frame).alt.deg


def telescope_tracking() -> bool:
    return etcs.get_tracking()


def telescope_on_kalao() -> bool:
    return etcs.get_instrument() == 3
