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

class Polygon(QWidget):
    def __init__(self):
        super().__init__()
        self.points = []

    def addPoint(self, p: list):
        self.points.append(p)

    def drawItself(self, painter: QPainter, sc: float):
        # create points array:
        fillColor = QColor(0, 200, 0)
        fillColor.setAlpha(20)
        strokeColor = QColor(0, 200, 0)
        strokeColor.setAlpha(100)
        pen = QPen(strokeColor, 1, Qt.SolidLine)
        painter.setPen(pen)
        brush = QBrush(fillColor, Qt.SolidPattern)
        painter.setBrush(brush)
        pointsToDraw = QPolygonF()
        for p in self.points:
            # print('draw Point: x: {}, y: {}'.format(p[0], p[1]))
            pointsToDraw.append(QPointF(p[0]*sc, p[1]*sc))

        painter.drawPolygon(pointsToDraw, Qt.OddEvenFill)



