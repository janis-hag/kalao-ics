import os

from astropy.io import fits

import skimage

from kalao.cacao import telemetry
from kalao.interfaces import fake_data
from kalao.utils import database, file_handling, image, kalao_time


def streams(shm_cache={}, real_data=True):
    if real_data:
        return telemetry.streams(shm_cache)
    else:
        return fake_data.fake_streams()


def tip_tilt(nb_points, real_data=True):
    if real_data:
        return database.get_telemetry(['pi_tip', 'pi_tilt'], nb_points)
    else:
        return fake_data.fake_tip_tilt(nb_points)


def get_all_last_monitoring(real_data=True):
    if real_data:
        return database.get_all_last_monitoring()
    else:
        return None


def get_all_last_telemetry(real_data=True):
    if real_data:
        return database.get_all_last_telemetry()
    else:
        return fake_data.fake_all_last_telemetry()


def latest_obs_log_entry(real_data=True):
    """
    Queries the latest entry in the *obs_log* mongo database,

    :param real_data:
    :return: Text string with the latest entry
    """

    if real_data:
        latest_record = database._get_data('obs_log')
        if latest_record is None:
            formatted_entry_text = 'Obs logs empty'
        else:
            key_name = list(latest_record.keys())[0]
            time_string = latest_record[key_name][0]['timestamp'].isoformat(
                    timespec='milliseconds')
            record_text = latest_record[key_name][0]['value']

            formatted_entry_text = str(time_string) + ' ' + str(
                    key_name) + ': ' + str(record_text)

        return formatted_entry_text
    else:
        return fake_data.fake_latest_obs_log_entry()


def get_fli_image(x=None, y=None, percentile=99, last_file_date=None,
                  binfactor=4, real_data=True):
    if not real_data:
        img = fake_data.fake_fli_image()
        file_date = kalao_time.now()
        manual_centering_needed = False
    else:
        fli_image_path, file_date = file_handling.get_last_image_path()
        manual_centering_needed = database.get_last_record_value(
                'obs_log', key='tracking_manual_centering')

        if fli_image_path is None or file_date is None or not os.path.isfile(
                fli_image_path):
            return False, None, None

        file_date = file_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        if last_file_date == file_date:
            return False, None, None

        img = fits.getdata(fli_image_path)

    img, min_value, max_value = image.percentile_clip(img, percentile)

    if x is None or y is None:
        img = skimage.transform.resize(img, (img.shape[0] // binfactor,
                                             img.shape[1] // binfactor),
                                       anti_aliasing=True, preserve_range=True)

    else:
        img = image.cut(img, 256, (x, y))

    img = img.transpose()

    return manual_centering_needed, img, file_date
