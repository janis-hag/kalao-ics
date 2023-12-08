from pathlib import Path

from PySide6.QtGui import QColor

from kalao.definitions.enums import StrEnum


class Color():
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


class Scale(StrEnum):
    LINEAR = 'Linear'
    LOG = 'Logarithmic'


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
