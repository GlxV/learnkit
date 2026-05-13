from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from app.ui.theme import COLORS


class LogoMark(QWidget):
    def __init__(self, size: int = 50) -> None:
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(COLORS["purple_soft"]), 7)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(QPointF(14, 12), QPointF(14, 38))
        painter.drawLine(QPointF(23, 25), QPointF(37, 12))
        painter.drawLine(QPointF(23, 25), QPointF(39, 38))

        soft_pen = QPen(QColor(COLORS["blue"]), 7)
        soft_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(soft_pen)
        painter.drawLine(QPointF(8, 36), QPointF(18, 36))


class LineIcon(QWidget):
    def __init__(self, kind: str, color: str = COLORS["muted"], size: int = 24) -> None:
        super().__init__()
        self.kind = kind
        self.color = color
        self.setFixedSize(size, size)

    def set_color(self, color: str) -> None:
        self.color = color
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(self.color), 1.9)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        kind = self.kind
        if kind == "home":
            path = QPainterPath()
            path.moveTo(5, 12)
            path.lineTo(12, 6)
            path.lineTo(19, 12)
            painter.drawPath(path)
            painter.drawRoundedRect(QRectF(7, 12, 10, 8), 2, 2)
        elif kind == "search":
            painter.drawEllipse(QRectF(5, 5, 10, 10))
            painter.drawLine(QPointF(13, 13), QPointF(19, 19))
        elif kind == "subjects":
            for x in (5, 14):
                for y in (5, 14):
                    painter.drawRoundedRect(QRectF(x, y, 6, 6), 1.3, 1.3)
        elif kind == "studies":
            painter.drawRoundedRect(QRectF(6, 5, 12, 14), 2, 2)
            painter.drawLine(QPointF(9, 9), QPointF(15, 9))
            painter.drawLine(QPointF(9, 13), QPointF(15, 13))
        elif kind == "flashcards":
            painter.drawRoundedRect(QRectF(5, 8, 12, 10), 2, 2)
            painter.drawRoundedRect(QRectF(8, 5, 12, 10), 2, 2)
        elif kind == "blocks":
            path = QPainterPath()
            path.moveTo(12, 4)
            path.lineTo(19, 8)
            path.lineTo(19, 16)
            path.lineTo(12, 20)
            path.lineTo(5, 16)
            path.lineTo(5, 8)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(5, 8), QPointF(12, 12))
            painter.drawLine(QPointF(19, 8), QPointF(12, 12))
            painter.drawLine(QPointF(12, 12), QPointF(12, 20))
        elif kind == "questions":
            painter.drawEllipse(QRectF(5, 5, 14, 14))
            painter.drawText(QRectF(5, 4, 14, 15), Qt.AlignmentFlag.AlignCenter, "?")
        elif kind == "progress":
            painter.drawLine(QPointF(5, 17), QPointF(10, 12))
            painter.drawLine(QPointF(10, 12), QPointF(14, 15))
            painter.drawLine(QPointF(14, 15), QPointF(20, 8))
            painter.drawLine(QPointF(17, 8), QPointF(20, 8))
            painter.drawLine(QPointF(20, 8), QPointF(20, 11))
        elif kind == "database":
            painter.drawEllipse(QRectF(5, 4, 14, 6))
            painter.drawLine(QPointF(5, 7), QPointF(5, 17))
            painter.drawLine(QPointF(19, 7), QPointF(19, 17))
            painter.drawEllipse(QRectF(5, 14, 14, 6))
            painter.drawArc(QRectF(5, 9, 14, 6), 180 * 16, 180 * 16)
        elif kind == "import":
            painter.drawRoundedRect(QRectF(6, 7, 12, 12), 2, 2)
            painter.drawLine(QPointF(12, 4), QPointF(12, 14))
            painter.drawLine(QPointF(8, 10), QPointF(12, 14))
            painter.drawLine(QPointF(16, 10), QPointF(12, 14))
        elif kind == "settings":
            painter.drawEllipse(QRectF(8, 8, 8, 8))
            for point in ((12, 3), (12, 21), (3, 12), (21, 12), (6, 6), (18, 18), (18, 6), (6, 18)):
                painter.drawPoint(QPointF(point[0], point[1]))
        elif kind == "activity":
            painter.drawLine(QPointF(4, 13), QPointF(8, 13))
            painter.drawLine(QPointF(8, 13), QPointF(10, 8))
            painter.drawLine(QPointF(10, 8), QPointF(14, 18))
            painter.drawLine(QPointF(14, 18), QPointF(16, 13))
            painter.drawLine(QPointF(16, 13), QPointF(20, 13))
        elif kind == "community":
            painter.drawEllipse(QRectF(5, 6, 6, 6))
            painter.drawEllipse(QRectF(13, 6, 6, 6))
            painter.drawArc(QRectF(4, 12, 16, 8), 0, 180 * 16)
        else:
            painter.drawEllipse(QRectF(6, 6, 12, 12))
