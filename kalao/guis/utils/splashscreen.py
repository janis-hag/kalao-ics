from PySide6.QtCore import QEvent, QPoint, QRect, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, Qt
from PySide6.QtWidgets import QApplication, QWidget

from kalao.common.rprint import rprint


class KSplashScreen(QWidget):
    _message = ''

    def __init__(self, pixmap_path: str, font: QFont,
                 font_color: QColor) -> None:
        super().__init__()

        self.setWindowFlag(Qt.WindowType.SplashScreen |
                           Qt.WindowType.FramelessWindowHint |
                           Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._font_color = font_color

        self.setFont(font)

        icon = QIcon(pixmap_path)
        self._pixmap = icon.pixmap(QSize(810, 315))

        # self._pixmap = QPixmap(pixmap_path)
        rect = QRect(QPoint(), self._pixmap.deviceIndependentSize().toSize())
        self.resize(rect.size())
        self.move(self.screen().geometry().center() - rect.center())

        self.repaint()

        self.show()

    def repaint(self) -> None:
        super().repaint()
        QApplication.processEvents()

    def handlePaintEvent(self) -> None:
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing |
                               QPainter.RenderHint.SmoothPixmapTransform)

        painter.drawPixmap(QPoint(), self._pixmap)

        painter.setPen(self._font_color)
        rect = self.rect().adjusted(5, 5, -5, -5)

        painter.drawText(
            rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
            self._message)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Paint:
            self.handlePaintEvent()

        return super().event(event)

    def showMessage(self, message: str) -> None:
        rprint(f'SPLASHSCREEN | [INFO] {message}')

        self._message = message
        self.repaint()
