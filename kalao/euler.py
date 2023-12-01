from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time

from kalao.utils import database

import config


def outside_pressure():
    # Might be updated to take actual value from weather station
    return config.Euler.default_pressure


def outside_temperature():
    # Might be updated to take actual value from weather station
    return config.Euler.default_temperature


def outside_hygrometry():
    # Might be updated to take actual value from weather station
    return config.Euler.default_hygrometry


def sun_elevation():
    time = Time.now()
    altaz_frame = AltAz(location=observing_location(), obstime=time)

    return get_sun(time).transform_to(altaz_frame).alt.deg


def observing_location():
    return EarthLocation(lat=config.Euler.latitude, lon=config.Euler.longitude,
                         height=config.Euler.altitude * u.m)


def star_coord():
    star_ra = database.get_last_value('obs', 'target_ra')
    star_dec = database.get_last_value('obs', 'target_dec')

    # TODO verify star_ra and star_dec validity

    c = SkyCoord(ra=star_ra * u.degree, dec=star_dec * u.degree, frame='icrs')

    return c


def telescope_coord():
    tel_ra = database.get_last_value('obs', 'telescope_ra')
    tel_dec = database.get_last_value('obs', 'telescope_dec')

    # TODO verify tel_ra and tel_dec validity

    c = SkyCoord(ra=tel_ra * u.degree, dec=tel_dec * u.degree, frame='icrs')

    return c


def telescope_coord_altaz():
    altaz_frame = AltAz(location=observing_location(), obstime=Time.now())

    return telescope_coord().transform_to(altaz_frame)


def telescope_zenith_angle():
    return 90 - telescope_coord_altaz().alt.deg


def telescope_tracking():
    return database.get_last_value('obs', 'tracking_status')


def compute_altaz_offset(alt_offset_arcsec, az_offset_arcsec):
    return telescope_coord_altaz().spherical_offsets_by(
        alt_offset_arcsec * u.arcsec,
        az_offset_arcsec * u.arcsec).transform_to('icrs')
