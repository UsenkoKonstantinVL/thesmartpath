import PySide2
from PySide2.QtWidgets import (QApplication, QDialog, QLineEdit, QPushButton, QMainWindow,
                               QVBoxLayout, QHBoxLayout, QWidget, QGroupBox, QFrame, QOpenGLWidget)
from PySide2.QtGui import QPainter, QPalette, QColor, QBrush, QPen, QPolygonF
from PySide2.QtCore import (QRect, QRectF, QPoint, QPointF, QSize, QMargins, Qt,
                            Property, Signal, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
                            )

import math
import itertools
import time

class MapObject(QWidget):
    def __init__(self, points = []):
        super().__init__()
        self.points = points

    def addPoint(self, p: list):
        self.points.append(p)


class Polygon(MapObject):
    def __init__(self, points = []):
        super().__init__()

    def drawItself(self, painter: QPainter, sc: float, color=QColor(0, 200, 0)):
        # create points array:
        fillColor = color
        fillColor.setAlpha(10)
        strokeColor = color
        strokeColor.setAlpha(100)
        pen = QPen(strokeColor, 1, Qt.SolidLine)
        painter.setPen(pen)
        brush = QBrush(fillColor, Qt.SolidPattern)
        painter.setBrush(brush)
        pointsToDraw = QPolygonF()
        for p in self.points:
            pointsToDraw.append(QPointF(p[0]*sc, p[1]*sc))

        painter.drawPolygon(pointsToDraw, Qt.OddEvenFill)

class TractorPath(MapObject):
    def __init__(self, points = []):
        super().__init__()
        self.points = points

    def addPoint(self, p: list):
        self.points.append(p)

    def drawItself(self, painter: QPainter, sc: float, color=QColor(10, 10, 210)):
        strokeColor = color
        pen = QPen(strokeColor, 1, Qt.SolidLine)
        painter.setPen(pen)
        pointsToDraw = QPolygonF()
        for p in self.points:
            pointsToDraw.append(QPointF(p[0]*sc, p[1]*sc))
        painter.drawPolyline(pointsToDraw)


