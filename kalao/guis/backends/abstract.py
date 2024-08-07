import time
from abc import abstractmethod
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import numpy as np

from astropy.io import fits

from PySide6.QtCore import QObject, Signal

from kalao.cacao import toolbox

from kalao.definitions.dataclasses import LogEntry

import config


def emit(fun: Callable) -> Callable:
    @wraps(fun)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        data = fun(self, *args, **kwargs)

        getattr(self, fun.__name__ + '_updated').emit(data)

        return data

    return wrapper


def timeit(fun: Callable) -> Callable:
    @wraps(fun)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        start = time.monotonic()

        data = fun(self, *args, **kwargs)

        end = time.monotonic()

        data['metadata'] = {
            'duration': end - start,
            'timestamp': time.time(),
        }

        return data

    return wrapper


def name_to_url(name: str) -> str:
    return '/' + name.replace('_', '/')


class AbstractBackend(QObject):
    streams_all_updated = Signal(object)
    camera_image_updated = Signal(object)
    all_updated = Signal(object)
    monitoring_updated = Signal(object)
    streams_channels_dm_updated = Signal(object)
    streams_channels_ttm_updated = Signal(object)
    focusing_sequence_fits_updated = Signal(object)
    calibration_sequence_updated = Signal(object)
    centering_spiral_data_updated = Signal(object)

    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def streams_all(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def camera_image(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def all(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def monitoring(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def streams_channels_dm(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def streams_channels_ttm(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def focusing_sequence_fits(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def calibration_sequence(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def centering_spiral_data(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def sequencer_abort(self) -> None:
        pass

    @abstractmethod
    def plots_data_db(self, *, since: datetime, until: datetime,
                      monitoring_keys: list[str],
                      obs_keys: list[str]) -> dict[str, Any]:
        pass

    @abstractmethod
    def plots_data_live(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_ready(self, *, conf: str, loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_data(self, *, conf: str, loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_reload(self, *, conf: str, loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_prepare(self, *, conf: str,
                               loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_mlat(self, *, conf: str, loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_mkDMpokemodes(self, *, conf: str,
                                     loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_takeref(self, *, conf: str,
                               loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_acqlinResp(self, *, conf: str,
                                  loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_RMHdecode(self, *, conf: str,
                                 loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_RMmkmask(self, *, conf: str,
                                loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_compCM(self, *, conf: str, loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_load(self, *, conf: str, loop: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def ao_calibration_save(self, *, conf: str, loop: int,
                            comment: str) -> dict[str, Any]:
        pass

    ##### Science Camera

    @abstractmethod
    def centering_manual_offsets(self, *, dx: float, dy: float) -> None:
        pass

    @abstractmethod
    def centering_manual_validate(self) -> None:
        pass

    ##### Loop controls

    # DM Loop

    @abstractmethod
    def ao_dmloop_on(self, *, state: bool) -> None:
        pass

    @abstractmethod
    def ao_dmloop_gain(self, *, gain: float) -> None:
        pass

    @abstractmethod
    def ao_dmloop_mult(self, *, mult: float) -> None:
        pass

    @abstractmethod
    def ao_dmloop_limit(self, *, limit: float) -> None:
        pass

    @abstractmethod
    def ao_dmloop_zero(self) -> None:
        pass

    # TTM Loop

    @abstractmethod
    def ao_ttmloop_on(self, *, state: bool) -> None:
        pass

    @abstractmethod
    def ao_ttmloop_gain(self, *, gain: float) -> None:
        pass

    @abstractmethod
    def ao_ttmloop_mult(self, *, mult: float) -> None:
        pass

    @abstractmethod
    def ao_ttmloop_limit(self, *, limit: float) -> None:
        pass

    @abstractmethod
    def ao_ttmloop_zero(self) -> None:
        pass

    # Wavefront Sensor

    @abstractmethod
    def wfs_emgain(self, *, emgain: int) -> None:
        pass

    @abstractmethod
    def wfs_exposuretime(self, *, exposuretime: float) -> None:
        pass

    @abstractmethod
    def wfs_autogain_on(self, *, state: bool) -> None:
        pass

    @abstractmethod
    def wfs_autogain_setting(self, *, setting: int) -> None:
        pass

    # Deformable Mirror

    @abstractmethod
    def dm_maxstroke(self, *, stroke: float) -> None:
        pass

    @abstractmethod
    def dm_strokemode(self, *, mode: int) -> None:
        pass

    @abstractmethod
    def dm_targetstroke(self, *, target: float) -> None:
        pass

    # Observation

    @abstractmethod
    def adc_synchronisation(self, *, state: bool) -> None:
        pass

    @abstractmethod
    def ttm_offloading(self, *, state: bool) -> None:
        pass

    # Modal gains

    @abstractmethod
    def ao_dmloop_modalgains(self, *, modalgains: list) -> None:
        pass

    ##### Engineering

    # PLC / Misc. hardware

    @abstractmethod
    def hardware_shutter_status(self, *, status: str) -> None:
        pass

    @abstractmethod
    def hardware_shutter_init(self) -> None:
        pass

    @abstractmethod
    def hardware_flipmirror_status(self, *, status: str) -> None:
        pass

    @abstractmethod
    def hardware_flipmirror_init(self) -> None:
        pass

    @abstractmethod
    def hardware_calibunit_position(self, *, position: float) -> None:
        pass

    @abstractmethod
    def hardware_calibunit_init(self) -> None:
        pass

    @abstractmethod
    def hardware_calibunit_stop(self) -> None:
        pass

    @abstractmethod
    def hardware_calibunit_laser(self) -> None:
        pass

    @abstractmethod
    def hardware_calibunit_tungsten(self) -> None:
        pass

    @abstractmethod
    def hardware_tungsten_status(self, *, status: bool) -> None:
        pass

    @abstractmethod
    def hardware_tungsten_init(self) -> None:
        pass

    @abstractmethod
    def hardware_laser_status(self, *, status: bool) -> None:
        pass

    @abstractmethod
    def hardware_laser_power(self, *, power: float) -> None:
        pass

    @abstractmethod
    def hardware_laser_init(self) -> None:
        pass

    @abstractmethod
    def hardware_lamps_off(self) -> None:
        pass

    @abstractmethod
    def hardware_filterwheel_filter(self, *, filter: str) -> None:
        pass

    @abstractmethod
    def hardware_filterwheel_init(self) -> None:
        pass

    @abstractmethod
    def hardware_adc1_angle(self, *, position: float) -> None:
        pass

    @abstractmethod
    def hardware_adc1_init(self) -> None:
        pass

    @abstractmethod
    def hardware_adc1_stop(self) -> None:
        pass

    @abstractmethod
    def hardware_adc2_angle(self, *, position: float) -> None:
        pass

    @abstractmethod
    def hardware_adc2_init(self) -> None:
        pass

    @abstractmethod
    def hardware_adc2_stop(self) -> None:
        pass

    @abstractmethod
    def hardware_adc_zerodisp(self) -> None:
        pass

    @abstractmethod
    def hardware_adc_maxdisp(self) -> None:
        pass

    @abstractmethod
    def hardware_adc_angleoffset(self, *, angle: float, offset: float) -> None:
        pass

    @abstractmethod
    def hardware_pump_status(self, *, status: bool) -> None:
        pass

    @abstractmethod
    def hardware_fan_status(self, *, status: bool) -> None:
        pass

    @abstractmethod
    def hardware_heater_status(self, *, status: bool) -> None:
        pass

    # Camera

    @abstractmethod
    def camera_exptime(self, *, exposure_time: float) -> None:
        pass

    @abstractmethod
    def camera_take(self, *, exposure_time: float, frames: int,
                    roi_size: int) -> None:
        pass

    @abstractmethod
    def camera_cancel(self) -> None:
        pass

    # Wavefront Sensor

    @abstractmethod
    def wfs_acquisition_start(self) -> None:
        pass

    @abstractmethod
    def wfs_acquisition_stop(self) -> None:
        pass

    # Deformable Mirror

    @abstractmethod
    def dm_on(self) -> None:
        pass

    @abstractmethod
    def dm_off(self) -> None:
        pass

    # IPPower

    @abstractmethod
    def ippower_rtc_on(self) -> None:
        pass

    @abstractmethod
    def ippower_rtc_off(self) -> None:
        pass

    @abstractmethod
    def ippower_bench_on(self) -> None:
        pass

    @abstractmethod
    def ippower_bench_off(self) -> None:
        pass

    @abstractmethod
    def ippower_dm_on(self) -> None:
        pass

    @abstractmethod
    def ippower_dm_off(self) -> None:
        pass

    @abstractmethod
    def services_action(self, *, unit: str, action: str) -> None:
        pass

    # DM channels
    @abstractmethod
    def channels_resetall(self, *, dm_number: int) -> None:
        pass

    @abstractmethod
    def channels_reset(self, *, dm_number: int, channel: int) -> None:
        pass

    # DM & TTM control

    @abstractmethod
    def dm_pattern(self, *, pattern: np.ndarray) -> None:
        pass

    @abstractmethod
    def ttm_position(self, *, tip: float, tilt: float) -> None:
        pass

    # Centering

    @abstractmethod
    def centering_star(self) -> None:
        pass

    @abstractmethod
    def centering_laser(self) -> None:
        pass

    @abstractmethod
    def centering_spiral(self) -> None:
        pass

    # Focusing

    @abstractmethod
    def focusing_autofocus(self) -> None:
        pass

    @abstractmethod
    def focusing_sequence(self) -> None:
        pass

    # Dead-man

    @abstractmethod
    def deadman(self, *, count: int) -> None:
        pass

    # Instrument / RTC

    @abstractmethod
    def instrument_shutdown(self) -> None:
        pass

    @abstractmethod
    def rtc_poweroff(self) -> None:
        pass

    @abstractmethod
    def rtc_reboot(self) -> None:
        pass

    ##### Logs

    @abstractmethod
    def logs(self, *, timestamp: datetime = None, cursor: str = None,
             lines: int = None) -> list[LogEntry]:
        pass

    @abstractmethod
    def logs_between(self, *, since: datetime,
                     until: datetime) -> list[LogEntry]:
        pass


class SHMFPSBackend(AbstractBackend):
    @staticmethod
    def _update_shm(data: dict[str, Any], shm_name: str,
                    key: str | None = None) -> None:
        if key is None:
            key = shm_name

        shm = toolbox.get_shm(shm_name)

        if shm is None:
            return

        if key not in data:
            data[key] = {}

        data[key].update({
            'cnt0': shm.IMAGE.md.cnt0,
            'data': shm.get_data(check=False),
        })

    @staticmethod
    def _update_shm_keywords(data: dict[str, Any], shm_name: str) -> None:
        shm = toolbox.get_shm(shm_name)

        if shm is None:
            return

        if shm_name not in data:
            data[shm_name] = {}

        data[shm_name]['keywords'] = shm.get_keywords()

    @staticmethod
    def _update_shm_md(data: dict[str, Any], shm_name: str) -> None:
        shm = toolbox.get_shm(shm_name)

        if shm_name not in data:
            data[shm_name] = {}

        if shm is None:
            data[shm_name]['md'] = {'status': 'M'}
        else:
            data[shm_name]['md'] = {
                'status': '',
                'shape': shm.shape,
                'cnt0': shm.IMAGE.md.cnt0,
                'creationtime': shm.IMAGE.md.creationtime,
                'acqtime': shm.IMAGE.md.acqtime,
            }

    @staticmethod
    def _update_fps_param(data: dict[str, Any], fps_name: str,
                          param_name: str) -> None:
        fps = toolbox.get_fps(fps_name)

        if fps is None:
            return

        if fps_name not in data:
            data[fps_name] = {}

        data[fps_name][param_name] = fps.get_param(param_name)

    @staticmethod
    def _update_fps_md(data: dict[str, Any], fps_name: str) -> None:
        fps = toolbox.get_fps(fps_name)

        if fps_name not in data:
            data[fps_name] = {}

        if fps is None:
            data[fps_name]['md'] = {'status': 'M'}
        else:
            data[fps_name]['md'] = {'status': ''}

            if fps.conf_isrunning():
                data[fps_name]['md']['status'] += 'C'

            if fps.run_isrunning():
                data[fps_name]['md']['status'] += 'R'

    @staticmethod
    def _update_dict(data: dict[str, Any], key: str, dict: dict[str,
                                                                Any]) -> None:
        if key not in data:
            data[key] = {}

        data[key].update(dict)

    @staticmethod
    def _update_db(data: dict[str, Any], collection: str,
                   db_data: dict[str, Any]) -> None:
        if collection not in data:
            data[collection] = {}

        data[collection].update(db_data)

    @staticmethod
    def _update_fits(data: dict[str, Any], fits_file: Path | str) -> None:
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        try:
            data[key] = {
                'mtime':
                    datetime.fromtimestamp(fits_file.stat().st_mtime,
                                           tz=timezone.utc),
                'data':
                    fits.getdata(fits_file),
            }
        except (FileNotFoundError, OSError):
            pass

    @staticmethod
    def _update_fits_full(data: dict[str, Any], fits_file: Path | str) -> None:
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        try:
            # Recreate HDU List to avoid "cannot pickle '_io.BufferedReader' object" error
            hdul = fits.open(fits_file)
            hdul_ = fits.HDUList()

            for hdu in hdul:
                hdu_ = type(hdu)()
                hdu_.data = hdu.data
                hdu_.header = hdu.header
                hdul_.append(hdu_)

            data[key] = {
                'mtime':
                    datetime.fromtimestamp(fits_file.stat().st_mtime,
                                           tz=timezone.utc),
                'hdul':
                    hdul_,
            }
        except (FileNotFoundError, OSError):
            pass

    @staticmethod
    def _update_fits_mtime(data: dict[str, Any],
                           fits_file: Path | str) -> None:
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        try:
            if data.get(key) is None:
                data[key] = {}

            data[key]['mtime'] = datetime.fromtimestamp(
                fits_file.stat().st_mtime, tz=timezone.utc)
        except (FileNotFoundError, OSError):
            pass


class FakeSHMFPSBackend(AbstractBackend):
    def __init__(self) -> None:
        super().__init__()

        self.internal_state = {}

    def _update_shm(self, data: dict[str, Any], shm_name: str, stream_data,
                    key: str | None = None) -> None:
        if key is None:
            key = shm_name

        if key not in data:
            data[key] = {}

        cnt0 = self.internal_state.get(f'{shm_name}-cnt0', -1) + 1

        data[key].update({
            'cnt0': cnt0,
            'data': stream_data,
        })

        self.internal_state[f'{shm_name}-cnt0'] = cnt0

    @staticmethod
    def _update_shm_keywords(data: dict[str, Any], shm_name: str,
                             keywords: dict[str, Any]) -> None:
        if shm_name not in data:
            data[shm_name] = {}

        data[shm_name]['keywords'] = keywords

    @staticmethod
    def _update_shm_md(data: dict[str, Any], shm_name: str) -> None:
        if shm_name not in data:
            data[shm_name] = {}

        data[shm_name]['md'] = {
            'status': '',
            'shape': (12, 12),
            'cnt0': 123,
            'creationtime': datetime.fromtimestamp(0),
            'acqtime': datetime.now(),
        }

    @staticmethod
    def _update_fps_param(data: dict[str, Any], fps_name: str, param_name: str,
                          param) -> None:
        if fps_name not in data:
            data[fps_name] = {}

        data[fps_name][param_name] = param

    @staticmethod
    def _update_fps_md(data: dict[str, Any], fps_name: str, md: dict) -> None:
        if fps_name not in data:
            data[fps_name] = {}

        data[fps_name]['md'] = md

    @staticmethod
    def _update_dict(data: dict[str, Any], key: str, dict: dict[str,
                                                                Any]) -> None:
        if key not in data:
            data[key] = {}

        data[key].update(dict)

    @staticmethod
    def _update_db(data: dict[str, Any], collection: str,
                   db_data: dict[str, Any]) -> None:
        if collection not in data:
            data[collection] = {}

        data[collection].update(db_data)

    @staticmethod
    def _update_fits(data: dict[str, Any], fits_file: Path | str,
                     array: dict[str, Any]) -> None:
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        data[key] = {'mtime': datetime.now(timezone.utc), 'data': array}

    def _update_fits_full(self, data: dict[str, Any], fits_file: Path | str,
                          hdul: fits.HDUList) -> None:
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        data[key] = {'mtime': datetime.now(timezone.utc), 'hdul': hdul}

        if fits_file == config.FITS.last_image_all:
            data[key]['mtime'] = self.internal_state.get('fli-mtime')

    @staticmethod
    def _update_fits_mtime(data: dict[str, Any], fits_file: Path | str,
                           mtime: float) -> None:
        if not isinstance(fits_file, Path):
            fits_file = Path(fits_file)

        key = fits_file.stem

        if key not in data:
            data[key] = {}

        data[key]['mtime'] = mtime
