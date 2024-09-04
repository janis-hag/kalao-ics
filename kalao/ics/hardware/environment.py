from opcua import Client

from kalao.ics.hardware import plc

import config


@plc.autoconnect
def get_readings(beck: Client = None) -> dict[str, float]:
    return {
        'bench_air_temp':
            config.PLC.bench_air_temp_offset +
            beck.get_node(config.PLC.Node.BENCH_AIR_TEMP).get_value(),
        'bench_board_temp':
            config.PLC.bench_board_temp_offset +
            beck.get_node(config.PLC.Node.BENCH_BOARD_TEMP).get_value(),
        'bench_air_hygro':
            beck.get_node(config.PLC.Node.BENCH_AIR_HYGRO).get_value(),
    }