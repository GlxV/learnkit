from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from app.ui.theme import COLORS

BASE_LINE_ICON_KINDS = {
    "home", "search", "subjects", "studies", "flashcards", "blocks", "questions",
    "progress", "database", "import", "settings", "activity", "community",
}

try:
    from app.ui.icon_catalog import SUBJECT_ICONS

    LINE_ICON_KINDS = BASE_LINE_ICON_KINDS | set(SUBJECT_ICONS)
except Exception:
    LINE_ICON_KINDS = set(BASE_LINE_ICON_KINDS)


def supports_line_icon(kind: str) -> bool:
    return kind in LINE_ICON_KINDS


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
        elif kind in {"database", "data", "sql"}:
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
        elif kind in {"calculator", "stats"}:
            painter.drawRoundedRect(QRectF(5, 4, 14, 16), 2, 2)
            painter.drawLine(QPointF(8, 8), QPointF(16, 8))
            for x in (8, 12, 16):
                for y in (12, 16):
                    painter.drawPoint(QPointF(x, y))
        elif kind in {"ruler", "axis"}:
            painter.drawLine(QPointF(5, 18), QPointF(19, 6))
            for offset in (0, 4, 8, 12):
                painter.drawLine(QPointF(7 + offset, 15 - offset), QPointF(9 + offset, 17 - offset))
        elif kind in {"compass", "geometry"}:
            painter.drawLine(QPointF(12, 5), QPointF(6, 19))
            painter.drawLine(QPointF(12, 5), QPointF(18, 19))
            painter.drawArc(QRectF(6, 11, 12, 8), 205 * 16, 130 * 16)
        elif kind in {"triangle"}:
            path = QPainterPath()
            path.moveTo(12, 5)
            path.lineTo(20, 19)
            path.lineTo(4, 19)
            path.closeSubpath()
            painter.drawPath(path)
        elif kind in {"function", "sigma"}:
            painter.drawLine(QPointF(5, 18), QPointF(9, 18))
            painter.drawLine(QPointF(9, 18), QPointF(13, 6))
            painter.drawLine(QPointF(13, 6), QPointF(19, 6))
            painter.drawLine(QPointF(8, 12), QPointF(16, 12))
        elif kind in {"chart", "chart-up", "finance", "marketing"}:
            painter.drawLine(QPointF(5, 18), QPointF(5, 6))
            painter.drawLine(QPointF(5, 18), QPointF(20, 18))
            painter.drawLine(QPointF(7, 15), QPointF(11, 12))
            painter.drawLine(QPointF(11, 12), QPointF(14, 14))
            painter.drawLine(QPointF(14, 14), QPointF(19, 8))
        elif kind in {"atom", "molecule"}:
            painter.drawEllipse(QRectF(10, 10, 4, 4))
            painter.drawEllipse(QRectF(5, 9, 14, 6))
            painter.drawEllipse(QRectF(7, 5, 10, 14))
            painter.drawLine(QPointF(7, 7), QPointF(17, 17))
        elif kind in {"flask", "lab"}:
            painter.drawLine(QPointF(10, 5), QPointF(10, 11))
            painter.drawLine(QPointF(14, 5), QPointF(14, 11))
            path = QPainterPath()
            path.moveTo(10, 11)
            path.lineTo(6, 19)
            path.lineTo(18, 19)
            path.lineTo(14, 11)
            painter.drawPath(path)
            painter.drawLine(QPointF(8, 16), QPointF(16, 16))
        elif kind == "microscope":
            painter.drawLine(QPointF(14, 5), QPointF(9, 10))
            painter.drawLine(QPointF(9, 10), QPointF(14, 15))
            painter.drawArc(QRectF(6, 9, 10, 10), 250 * 16, 190 * 16)
            painter.drawLine(QPointF(6, 20), QPointF(19, 20))
        elif kind == "dna":
            painter.drawArc(QRectF(8, 4, 8, 16), 90 * 16, 180 * 16)
            painter.drawArc(QRectF(8, 4, 8, 16), 270 * 16, 180 * 16)
            for y in (8, 12, 16):
                painter.drawLine(QPointF(9, y), QPointF(15, y))
        elif kind in {"cell", "ecology"}:
            painter.drawEllipse(QRectF(5, 5, 14, 14))
            painter.drawEllipse(QRectF(10, 10, 5, 5))
        elif kind in {"leaf", "anatomy"}:
            path = QPainterPath()
            path.moveTo(6, 17)
            path.cubicTo(7, 7, 16, 4, 19, 6)
            path.cubicTo(18, 16, 10, 20, 6, 17)
            painter.drawPath(path)
            painter.drawLine(QPointF(7, 17), QPointF(17, 7))
        elif kind in {"globe", "language"}:
            painter.drawEllipse(QRectF(5, 5, 14, 14))
            painter.drawLine(QPointF(5, 12), QPointF(19, 12))
            painter.drawArc(QRectF(8, 5, 8, 14), 90 * 16, 180 * 16)
            painter.drawArc(QRectF(8, 5, 8, 14), 270 * 16, 180 * 16)
        elif kind == "map":
            painter.drawLine(QPointF(5, 7), QPointF(10, 5))
            painter.drawLine(QPointF(10, 5), QPointF(15, 7))
            painter.drawLine(QPointF(15, 7), QPointF(20, 5))
            painter.drawLine(QPointF(5, 7), QPointF(5, 19))
            painter.drawLine(QPointF(10, 5), QPointF(10, 17))
            painter.drawLine(QPointF(15, 7), QPointF(15, 19))
            painter.drawLine(QPointF(20, 5), QPointF(20, 17))
        elif kind in {"landmark", "building"}:
            painter.drawLine(QPointF(5, 10), QPointF(12, 5))
            painter.drawLine(QPointF(12, 5), QPointF(19, 10))
            painter.drawLine(QPointF(6, 19), QPointF(18, 19))
            for x in (8, 12, 16):
                painter.drawLine(QPointF(x, 11), QPointF(x, 18))
        elif kind in {"timeline", "project"}:
            painter.drawLine(QPointF(7, 6), QPointF(7, 18))
            for y in (6, 12, 18):
                painter.drawEllipse(QRectF(5, y - 2, 4, 4))
                painter.drawLine(QPointF(10, y), QPointF(19, y))
        elif kind in {"scroll", "dictionary"}:
            painter.drawRoundedRect(QRectF(6, 5, 12, 15), 2, 2)
            painter.drawLine(QPointF(9, 9), QPointF(15, 9))
            painter.drawLine(QPointF(9, 13), QPointF(15, 13))
            painter.drawLine(QPointF(9, 17), QPointF(13, 17))
        elif kind in {"scale", "law"}:
            painter.drawLine(QPointF(12, 5), QPointF(12, 19))
            painter.drawLine(QPointF(7, 8), QPointF(17, 8))
            painter.drawArc(QRectF(4, 9, 6, 7), 180 * 16, 180 * 16)
            painter.drawArc(QRectF(14, 9, 6, 7), 180 * 16, 180 * 16)
            painter.drawLine(QPointF(8, 20), QPointF(16, 20))
        elif kind in {"politics", "flag"}:
            painter.drawLine(QPointF(7, 5), QPointF(7, 20))
            path = QPainterPath()
            path.moveTo(7, 6)
            path.lineTo(18, 8)
            path.lineTo(7, 12)
            painter.drawPath(path)
        elif kind in {"society", "community"}:
            painter.drawEllipse(QRectF(5, 7, 5, 5))
            painter.drawEllipse(QRectF(14, 7, 5, 5))
            painter.drawArc(QRectF(4, 12, 16, 8), 0, 180 * 16)
        elif kind in {"philosophy", "brain", "psychology"}:
            painter.drawArc(QRectF(5, 7, 8, 8), 90 * 16, 220 * 16)
            painter.drawArc(QRectF(11, 7, 8, 8), 230 * 16, 220 * 16)
            painter.drawLine(QPointF(8, 16), QPointF(8, 19))
            painter.drawLine(QPointF(16, 16), QPointF(16, 19))
        elif kind in {"book", "bookmark"}:
            painter.drawRoundedRect(QRectF(5, 5, 7, 15), 1, 1)
            painter.drawRoundedRect(QRectF(12, 5, 7, 15), 1, 1)
            painter.drawLine(QPointF(12, 6), QPointF(12, 20))
        elif kind in {"pen", "grammar", "paragraph"}:
            painter.drawLine(QPointF(6, 18), QPointF(17, 7))
            painter.drawLine(QPointF(14, 5), QPointF(19, 10))
            painter.drawLine(QPointF(5, 19), QPointF(10, 18))
        elif kind == "quote":
            painter.drawArc(QRectF(5, 8, 6, 8), 90 * 16, 220 * 16)
            painter.drawArc(QRectF(14, 8, 6, 8), 90 * 16, 220 * 16)
        elif kind in {"palette", "brush", "design"}:
            painter.drawEllipse(QRectF(5, 6, 14, 12))
            for point in ((9, 10), (13, 9), (16, 12), (11, 15)):
                painter.drawPoint(QPointF(point[0], point[1]))
        elif kind == "music":
            painter.drawLine(QPointF(14, 5), QPointF(14, 16))
            painter.drawLine(QPointF(14, 5), QPointF(19, 7))
            painter.drawEllipse(QRectF(8, 14, 6, 5))
        elif kind in {"camera", "photo"}:
            painter.drawRoundedRect(QRectF(5, 8, 14, 10), 2, 2)
            painter.drawEllipse(QRectF(10, 11, 5, 5))
            painter.drawLine(QPointF(8, 8), QPointF(10, 5))
        elif kind in {"film", "image"}:
            painter.drawRoundedRect(QRectF(5, 6, 14, 12), 2, 2)
            painter.drawLine(QPointF(8, 6), QPointF(8, 18))
            painter.drawLine(QPointF(16, 6), QPointF(16, 18))
        elif kind in {"layers"}:
            painter.drawRoundedRect(QRectF(7, 5, 10, 7), 1, 1)
            painter.drawRoundedRect(QRectF(5, 10, 14, 7), 1, 1)
            painter.drawRoundedRect(QRectF(7, 15, 10, 5), 1, 1)
        elif kind in {"spark", "star"}:
            painter.drawLine(QPointF(12, 4), QPointF(12, 20))
            painter.drawLine(QPointF(4, 12), QPointF(20, 12))
            painter.drawLine(QPointF(7, 7), QPointF(17, 17))
            painter.drawLine(QPointF(17, 7), QPointF(7, 17))
        elif kind in {"terminal", "code", "api", "web"}:
            painter.drawLine(QPointF(8, 8), QPointF(4, 12))
            painter.drawLine(QPointF(4, 12), QPointF(8, 16))
            painter.drawLine(QPointF(16, 8), QPointF(20, 12))
            painter.drawLine(QPointF(20, 12), QPointF(16, 16))
            painter.drawLine(QPointF(14, 6), QPointF(10, 18))
        elif kind == "git":
            painter.drawLine(QPointF(7, 7), QPointF(17, 17))
            painter.drawLine(QPointF(12, 12), QPointF(17, 8))
            for point in ((7, 7), (12, 12), (17, 17), (17, 8)):
                painter.drawEllipse(QRectF(point[0] - 2, point[1] - 2, 4, 4))
        elif kind in {"network", "graph", "ai", "model"}:
            points = [(6, 8), (17, 7), (10, 17), (19, 16)]
            painter.drawLine(QPointF(6, 8), QPointF(17, 7))
            painter.drawLine(QPointF(6, 8), QPointF(10, 17))
            painter.drawLine(QPointF(17, 7), QPointF(19, 16))
            painter.drawLine(QPointF(10, 17), QPointF(19, 16))
            for x, y in points:
                painter.drawEllipse(QRectF(x - 2, y - 2, 4, 4))
        elif kind in {"server", "cloud"}:
            painter.drawRoundedRect(QRectF(5, 6, 14, 5), 2, 2)
            painter.drawRoundedRect(QRectF(5, 14, 14, 5), 2, 2)
            painter.drawPoint(QPointF(16, 8))
            painter.drawPoint(QPointF(16, 16))
        elif kind in {"shield", "lock", "security"}:
            path = QPainterPath()
            path.moveTo(12, 5)
            path.lineTo(19, 8)
            path.lineTo(17, 17)
            path.lineTo(12, 20)
            path.lineTo(7, 17)
            path.lineTo(5, 8)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(9, 12), QPointF(11, 15))
            painter.drawLine(QPointF(11, 15), QPointF(16, 9))
        elif kind in {"chip", "circuit", "binary"}:
            painter.drawRoundedRect(QRectF(7, 7, 10, 10), 2, 2)
            for x in (5, 19):
                for y in (8, 12, 16):
                    painter.drawLine(QPointF(x, y), QPointF(7 if x == 5 else 17, y))
            for y in (5, 19):
                for x in (9, 12, 15):
                    painter.drawLine(QPointF(x, y), QPointF(x, 7 if y == 5 else 17))
        elif kind == "robot":
            painter.drawRoundedRect(QRectF(6, 8, 12, 9), 2, 2)
            painter.drawLine(QPointF(12, 5), QPointF(12, 8))
            painter.drawPoint(QPointF(10, 12))
            painter.drawPoint(QPointF(14, 12))
            painter.drawLine(QPointF(9, 16), QPointF(15, 16))
        elif kind == "gamepad":
            painter.drawRoundedRect(QRectF(4, 10, 16, 8), 4, 4)
            painter.drawLine(QPointF(8, 12), QPointF(8, 16))
            painter.drawLine(QPointF(6, 14), QPointF(10, 14))
            painter.drawPoint(QPointF(15, 13))
            painter.drawPoint(QPointF(17, 15))
        elif kind == "mobile":
            painter.drawRoundedRect(QRectF(8, 4, 8, 16), 2, 2)
            painter.drawPoint(QPointF(12, 17))
        elif kind == "bug":
            painter.drawEllipse(QRectF(8, 7, 8, 10))
            painter.drawLine(QPointF(6, 10), QPointF(18, 10))
            painter.drawLine(QPointF(5, 15), QPointF(19, 15))
        elif kind in {"wrench", "gear", "mechanics", "engineering"}:
            painter.drawEllipse(QRectF(6, 5, 6, 6))
            painter.drawLine(QPointF(10, 10), QPointF(18, 18))
            painter.drawLine(QPointF(16, 20), QPointF(20, 16))
        elif kind == "tree":
            painter.drawLine(QPointF(12, 5), QPointF(12, 19))
            painter.drawLine(QPointF(12, 9), QPointF(7, 14))
            painter.drawLine(QPointF(12, 9), QPointF(17, 14))
            painter.drawLine(QPointF(12, 13), QPointF(8, 18))
            painter.drawLine(QPointF(12, 13), QPointF(16, 18))
        elif kind in {"list", "checklist"}:
            for y in (7, 12, 17):
                painter.drawEllipse(QRectF(5, y - 1, 2, 2))
                painter.drawLine(QPointF(10, y), QPointF(19, y))
        elif kind in {"stack", "queue"}:
            painter.drawRoundedRect(QRectF(6, 6, 12, 4), 1, 1)
            painter.drawRoundedRect(QRectF(6, 11, 12, 4), 1, 1)
            painter.drawRoundedRect(QRectF(6, 16, 12, 4), 1, 1)
        elif kind == "hash":
            painter.drawLine(QPointF(9, 5), QPointF(7, 19))
            painter.drawLine(QPointF(16, 5), QPointF(14, 19))
            painter.drawLine(QPointF(5, 10), QPointF(19, 10))
            painter.drawLine(QPointF(5, 15), QPointF(19, 15))
        elif kind in {"briefcase"}:
            painter.drawRoundedRect(QRectF(5, 9, 14, 10), 2, 2)
            painter.drawLine(QPointF(9, 9), QPointF(9, 7))
            painter.drawLine(QPointF(15, 9), QPointF(15, 7))
            painter.drawLine(QPointF(9, 7), QPointF(15, 7))
        elif kind in {"coins"}:
            painter.drawEllipse(QRectF(5, 12, 8, 5))
            painter.drawEllipse(QRectF(11, 7, 8, 5))
            painter.drawEllipse(QRectF(11, 13, 8, 5))
        elif kind == "target":
            painter.drawEllipse(QRectF(5, 5, 14, 14))
            painter.drawEllipse(QRectF(9, 9, 6, 6))
            painter.drawPoint(QPointF(12, 12))
        elif kind == "calendar":
            painter.drawRoundedRect(QRectF(5, 6, 14, 13), 2, 2)
            painter.drawLine(QPointF(5, 10), QPointF(19, 10))
            painter.drawLine(QPointF(9, 4), QPointF(9, 8))
            painter.drawLine(QPointF(15, 4), QPointF(15, 8))
        elif kind == "clock":
            painter.drawEllipse(QRectF(5, 5, 14, 14))
            painter.drawLine(QPointF(12, 12), QPointF(12, 8))
            painter.drawLine(QPointF(12, 12), QPointF(16, 14))
        elif kind == "heart":
            path = QPainterPath()
            path.moveTo(12, 19)
            path.cubicTo(4, 13, 5, 6, 10, 7)
            path.cubicTo(12, 7, 12, 9, 12, 9)
            path.cubicTo(12, 9, 12, 7, 14, 7)
            path.cubicTo(19, 6, 20, 13, 12, 19)
            painter.drawPath(path)
        elif kind in {"stethoscope", "nursing"}:
            painter.drawArc(QRectF(6, 5, 8, 10), 180 * 16, 180 * 16)
            painter.drawLine(QPointF(6, 10), QPointF(6, 14))
            painter.drawLine(QPointF(14, 10), QPointF(14, 14))
            painter.drawLine(QPointF(14, 14), QPointF(18, 18))
            painter.drawEllipse(QRectF(17, 17, 3, 3))
        elif kind in {"pill", "pharmacy"}:
            painter.drawRoundedRect(QRectF(5, 9, 14, 6), 3, 3)
            painter.drawLine(QPointF(12, 9), QPointF(12, 15))
        elif kind == "tooth":
            path = QPainterPath()
            path.moveTo(8, 6)
            path.cubicTo(5, 8, 6, 18, 10, 20)
            path.cubicTo(11, 16, 13, 16, 14, 20)
            path.cubicTo(18, 18, 19, 8, 16, 6)
            path.cubicTo(13, 8, 11, 8, 8, 6)
            painter.drawPath(path)
        elif kind == "bolt":
            path = QPainterPath()
            path.moveTo(13, 4)
            path.lineTo(7, 14)
            path.lineTo(12, 14)
            path.lineTo(10, 20)
            path.lineTo(18, 10)
            path.lineTo(13, 10)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            self._draw_abstract_icon(painter, kind)

    def _draw_abstract_icon(self, painter: QPainter, kind: str) -> None:
        seed = sum(ord(char) for char in kind)
        variant = seed % 6
        if variant == 0:
            painter.drawRoundedRect(QRectF(6, 6, 12, 12), 3, 3)
            painter.drawLine(QPointF(9, 12), QPointF(15, 12))
            painter.drawLine(QPointF(12, 9), QPointF(12, 15))
        elif variant == 1:
            points = [(6, 15), (10, 7), (16, 9), (19, 17)]
            for start, end in zip(points, points[1:]):
                painter.drawLine(QPointF(*start), QPointF(*end))
            for x, y in points:
                painter.drawEllipse(QRectF(x - 2, y - 2, 4, 4))
        elif variant == 2:
            painter.drawEllipse(QRectF(5, 5, 14, 14))
            painter.drawLine(QPointF(8, 16), QPointF(16, 8))
        elif variant == 3:
            painter.drawRoundedRect(QRectF(5, 7, 14, 10), 2, 2)
            painter.drawLine(QPointF(8, 10), QPointF(16, 10))
            painter.drawLine(QPointF(8, 14), QPointF(13, 14))
        elif variant == 4:
            path = QPainterPath()
            path.moveTo(12, 5)
            path.lineTo(19, 12)
            path.lineTo(12, 19)
            path.lineTo(5, 12)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.drawLine(QPointF(5, 18), QPointF(10, 8))
            painter.drawLine(QPointF(10, 8), QPointF(14, 15))
            painter.drawLine(QPointF(14, 15), QPointF(19, 6))
