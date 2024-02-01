from enum import Enum
from pathlib import Path

from PySide6.QtGui import QColor

from kalao.utils.image import (LinearScale, LogScale, MinMaxCut, PercentileCut,
                               SigmaCut, SquaredScale, SquareRootScale)

from kalao.definitions.enums import StrEnum


class Color():
    TRANSPARENT = QColor(0, 0, 0, 0)

    BLACK = QColor('#000000')
    DARK_GREY = QColor('#666666')
    GREY = QColor('#808080')
    LIGHT_GREY = QColor('#eeeeee')
    WHITE = QColor('#ffffff')

    RED = QColor('#ed1515')
    ORANGE = QColor('#f67400')
    GREEN = QColor('#11d116')
    BLUE = QColor('#1d99f3')
    YELLOW = QColor('#fdbc4b')
    PURPLE = QColor('#8e44ad')


ColorPalette = [
    Color.BLUE,
    Color.RED,
    Color.GREEN,
    Color.PURPLE,
    Color.YELLOW,
    Color.ORANGE,
]


class Scale(Enum):
    LINEAR = LinearScale
    LOG = LogScale
    SQUARE_ROOT = SquareRootScale
    SQUARED = SquaredScale


class Cuts(Enum):
    MINMAX = MinMaxCut()

    PERCENTILE_0_01 = PercentileCut(0.01)
    PERCENTILE_0_1 = PercentileCut(0.1)
    PERCENTILE_0_5 = PercentileCut(0.5)
    PERCENTILE_1 = PercentileCut(1)
    PERCENTILE_2_5 = PercentileCut(2.5)
    PERCENTILE_5 = PercentileCut(5)
    PERCENTILE_10 = PercentileCut(10)

    SIGMA_1 = SigmaCut(1)
    SIGMA_2 = SigmaCut(2)
    SIGMA_3 = SigmaCut(3)
    SIGMA_6 = SigmaCut(6)


class PokeState(StrEnum):
    FLAT = "No poke"
    DOWN = "Poke down"
    UP = "Poke up"


class Logo:
    folder = Path(__file__).absolute().parent.parent.parent / 'logo'
    svg = folder / 'KalAO_logo.svg'
    ico = folder / 'KalAO_icon.ico'


HORI = 0
VERT = 1
