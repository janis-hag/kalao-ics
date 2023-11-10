from kalao.cacao import telemetry
from kalao.interfaces import fake_data
from kalao.utils import database


def streams(shm_cache = {}, real_data=True):
    if real_data:
        return telemetry.streams(shm_cache)
    else:
        return fake_data.fake_streams()


def tip_tilt(nb_points, real_data=True):
    if real_data:
        return database.get_telemetry(['pi_tip', 'pi_tilt'], nb_points)
    else:
        return fake_data.fake_tip_tilt(nb_points)


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