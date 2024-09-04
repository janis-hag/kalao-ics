import time
from abc import abstractmethod
from datetime import datetime
from functools import wraps
from typing import Any, Callable

import numpy as np

from PySide6.QtCore import QObject, Signal

from kalao.common.dataclasses import LogEntry


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
    def name(self) -> str:
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

    @abstractmethod
    def wfs_emgainoff(self) -> None:
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
