
import PySide2
from PySide2.QtWidgets import (QApplication, QDialog, QLineEdit, QPushButton, QMainWindow,
                               QVBoxLayout, QHBoxLayout, QWidget, QGroupBox, QFrame, QOpenGLWidget)
from PySide2.QtGui import QPainter, QPalette, QColor, QBrush, QPen
from PySide2.QtCore import (QRect, QRectF, QPoint, QPointF, QSize, QMargins, Qt,
                            Property, Signal, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup)
from border_path import nearest_polygon_point
import math
import itertools
import time


class NavButtons(QFrame):
    """ Button for map control. Plus - Minus - Center """
    scaleButtonPressed = Signal(bool)
    centerButtonPressed = Signal()
    def __init__(self, *args, **kwargs):
        super(NavButtons, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)
        self.initUI()

    def initUI(self):
        # CREATE LAYOUTS
        mainLayout = QVBoxLayout()
        # CREATE WIDGETS
        self.plusButton = QPushButton(text="+")
        self.plusButton.setAccessibleName("Plus")
        self.minusButton = QPushButton(text="–")
        self.minusButton.setAccessibleName("Minus")
        self.centerButton = QPushButton(text="∆")
        self.centerButton.setAccessibleName("Center")

        # WIRING

        # STYLING
        for button in (self.plusButton, self.minusButton, self.centerButton):
            button.setFixedSize(64, 64)
            button.setFlat(True)
            button.clicked.connect(self.buttonPressed)

        mainLayout.setSpacing(2)
        mainLayout.setContentsMargins(QMargins(2, 2, 2, 2))

        # COMPOSING
        self.setLayout(mainLayout)
        mainLayout.addWidget(self.plusButton)
        mainLayout.addWidget(self.centerButton)
        mainLayout.addWidget(self.minusButton)

    def buttonPressed(self):
        if self.sender().accessibleName() == "Plus":
            self.scaleButtonPressed.emit(True)
        elif self.sender().accessibleName() == "Minus":
            self.scaleButtonPressed.emit(False)
        else:
            self.centerButtonPressed.emit()


class Map(QWidget):
    moved = Signal()
    # Класс, описывающий поведение карты колхоза
    def __init__(self, core, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self.model = core
        self.initUI()
        self._delta = QPointF(100, 0)
        self._sc = 10
        self.cursor_pos = QPoint(0, 0)
        self.borderCursor = None
        self.startDragging = None
        self.dragging = False
        self._mapLineColorLight = None
        self._mapLineColorBold = None
        self._auxObjectsColor = None
        self.needToRepaint = False
        self.underHover = False

        # repaint timer
        self.repaintTimer = QTimer(self)
        self.repaintTimer.setInterval(16)
        self.repaintTimer.timeout.connect(self.repaintEvent)
        self.repaintTimer.start()

    def initUI(self):
        # CREATE OVERLAYING WIDGET
        self.buttons = NavButtons(parent=self)

        # WIRING
        self.buttons.scaleButtonPressed.connect(self.zoom)
        self.buttons.centerButtonPressed.connect(self.findField)
        self.model.geometryLoaded.connect(self.findField)
        self.model.pointsChanged.connect(self.callForRepaint)
        self.model.seedingPathChanged.connect(self.callForRepaint)
        self.model.sprinklingPathChanged.connect(self.callForRepaint)

    def resizeEvent(self, event: PySide2.QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        # find position for navButtons
        buttonsWidth = self.buttons.sizeHint().width()
        buttonsHeight = self.buttons.sizeHint().height()
        buttonsX = self.width() - buttonsWidth - 15
        buttonsY = self.height()/2 - buttonsHeight
        self.buttons.move(buttonsX, self.height()/2 - buttonsHeight/2)

    def callForRepaint(self):
        self.needToRepaint = True

    def repaintEvent(self):
        if self.needToRepaint:
            self.update()

    def zoom(self, up):
        oldValue = self.sc
        # calculate scaling after zoom
        if up:
            delta = 1.3
        else:
            if self._sc > 0.5:
                delta = 0.7
            else:
                delta = 1
        sc = oldValue*delta

        # create animation for zooming the map to new scale
        zoomAnimation = QPropertyAnimation(self, b"sc", self)
        zoomAnimation.setDuration(200)
        zoomAnimation.setEasingCurve(QEasingCurve.InOutCubic)
        zoomAnimation.setEndValue(sc)

        # create animation for sliding the map into new center point
        wCenter = self.getWorldCoords(self.rect().center())
        dx = (self.width() - 2 * wCenter.x() * sc) / 2
        dy = (self.height() - 2 * wCenter.y() * sc) / 2
        slideAnimation = QPropertyAnimation(self, b"delta", self)
        slideAnimation.setDuration(200)
        slideAnimation.setEasingCurve(QEasingCurve.InOutCubic)
        slideAnimation.setEndValue(QPointF(dx, dy))

        # create group of animations to play them one time
        animationGroup = QParallelAnimationGroup(self)
        animationGroup.addAnimation(zoomAnimation)
        animationGroup.addAnimation(slideAnimation)

        # start all the animations
        animationGroup.start()

    def findField(self):
        if self.model.givenGeometry is not None:
            pointsCount = len(self.model.givenGeometry.points)
            if pointsCount > 0 :
                print("Polygon length = ", len(self.model.givenGeometry.points))

                # find field leftes point
                minX = self.model.givenGeometry.points[0][0]
                minY = self.model.givenGeometry.points[0][1]
                maxX = self.model.givenGeometry.points[0][0]
                maxY = self.model.givenGeometry.points[0][1]

                for p in self.model.givenGeometry.points:
                    if p[0] < minX:
                        minX = p[0]
                    if p[1] < minY:
                        minY = p[1]
                    if p[0] > maxX:
                        maxX = p[0]
                    if p[1] > maxY:
                        maxY = p[1]
                print('MIN X, Y')
                print(minX)
                print(minY)
                sc = max(self.width()/(maxX-minX), self.height()/(maxY-minY))
                self.setSc(sc*0.8)
                self.setDelta(QPointF(-minX*self.sc, -minY*self.sc))

    def drawWireNet(self, painter):
        mapTopLeft = self.getWorldCoords(self.rect().topLeft())
        mapBottomRight = self.getWorldCoords(self.rect().bottomRight())
        # expand to round hundred
        mapTopLeft.setX(mapTopLeft.x() - mapTopLeft.x() % 100)
        mapTopLeft.setY(mapTopLeft.y() - mapTopLeft.y() % 100)
        # create horizontal bold lines
        boldPen = QPen(self.getMapLineColorBold(), 0.6, Qt.SolidLine)
        thinPen = QPen(self.getMapLineColorLight(), 0.2, Qt.SolidLine)

        painter.setPen(boldPen)
        for n in range(int(mapTopLeft.x()), int(mapBottomRight.x()) + 100, 100):
            P1 = QPoint(n * self._sc + self.delta.x(), mapTopLeft.y() * self._sc + self.delta.y())
            P2 = QPoint(n * self._sc + self.delta.x(), mapBottomRight.y() * self._sc + self.delta.y())
            painter.drawLine(P1, P2)
        # create horizontal thin lines
        painter.setPen(thinPen)
        for n in range(int(mapTopLeft.x()) + 50, int(mapBottomRight.x()) + 50, 50):
            P1 = QPoint(n * self._sc + self.delta.x(), mapTopLeft.y() * self._sc + self.delta.y())
            P2 = QPoint(n * self._sc + self.delta.x(), mapBottomRight.y() * self._sc + self.delta.y())
            painter.drawLine(P1, P2)

        # create vertical bold lines
        painter.setPen(boldPen)
        for n in range(int(mapTopLeft.y()), int(mapBottomRight.y()) + 100, 100):
            P1 = QPoint(mapTopLeft.x() * self._sc + self.delta.x(), n * self._sc + self.delta.y())
            P2 = QPoint(mapBottomRight.x() * self._sc + self.delta.x(), n * self._sc + self.delta.y())
            painter.drawLine(P1, P2)

        # create vertical thin lines
        painter.setPen(thinPen)
        for n in range(int(mapTopLeft.y()) + 50, int(mapBottomRight.y()) + 50, 50):
            P1 = QPoint(mapTopLeft.x() * self._sc + self.delta.x(), n * self._sc + self.delta.y())
            P2 = QPoint(mapBottomRight.x() * self._sc + self.delta.x(), n * self._sc + self.delta.y())
            painter.drawLine(P1, P2)

    def getWorldCoords(self, point, sc=None, inversed=False) -> QPointF:
        """
        return words coords
        :QPoint -
        """
        if sc is None:
            sc = self.sc
        if -0.001 < sc < 0.001:
            sc = 0.001
            # logger.error('Scale equal zero, can\'t devide by zero!')
            # return None

        _x = (point.x() - self.delta.x()) / sc
        if inversed:
            _y = ((self.height() - point.y()) - self.delta.y()) / sc
        else:
            _y = (point.y() - self.delta.y()) / sc
        return QPointF(_x, _y)

    def getMapCoords(self, point, inverted=False):
        """ return map coords from world coords """
        sc = self.sc
        x = self.delta.x() + point.x()*sc
        if inverted:
            y = self.height() - (self._delta.y() + point.y()*sc)
        else:
            y = self._delta.y() + point.y()*sc

        return QPointF(x, y)

    def drawScaleMark(self, painter):
        # draw map scale bar
        _pen = QPen()
        _brush = QBrush(self.getAuxObjectsColor(), Qt.SolidPattern)
        _pen.setColor(self.getAuxObjectsColor())
        _pen.setWidth(1)
        painter.setBrush(_brush)
        painter.setPen(_pen)
        _font = self.font()
        _font.setPixelSize(12)
        painter.setFont(_font)
        barWidth = 50 * self._sc
        startPoint = QPoint(self.rect().center().x() - barWidth/2, self.rect().bottom() - 20)
        painter.drawRect(QRect(startPoint, QSize(barWidth / 2, 5)))
        painter.fillRect(QRect(startPoint, QSize(barWidth / 2, 5)), _brush)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRect(startPoint, QSize(barWidth, 5)))
        painter.drawText(QPointF(startPoint.x(), startPoint.y() - 12), '0')
        painter.drawText(QPointF(startPoint.x() + barWidth / 2, startPoint.y() - 12), '50')
        painter.drawText(QPointF(startPoint.x() + barWidth, startPoint.y() - 12), self.tr('100 meters'))

    def drawCrossLines(self, painter: QPainter, pos):
        pen = QPen(Qt.white, 0.75, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(0, pos.y(), self.width(), pos.y())
        painter.drawLine(pos.x(), 0, pos.x(), self.height())

        # draw coords DEBUG
        mapPos = self.getWorldCoords(pos)
        # painter.drawText(QPoint(pos.x()+5, pos.y()+20), "x: {}\ny:{}".format(mapPos.x(), mapPos.y()))
        painter.drawText(QPoint(pos.x()+5, pos.y()+20), "x: {}\ny:{}".format(pos.x(), pos.y()))
        if self.model.entryPoint is None:
            # draw "enter entry point" near the cursor
            painter.drawText(QPoint(pos.x()+5, pos.y()-5), "Set Entry Point" )
        elif self.model.endPoint is None:
            # draw "enter end point" near the cursor
            painter.drawText(QPoint(pos.x()+5, pos.y()-5), "Set Exit Point" )

        if self.borderCursor is not None:
            painter.drawPoint(self.borderCursor)
            pen.setColor(Qt.yellow)
            painter.setPen(pen)
            painter.drawLine(self.borderCursor.x()-15, self.borderCursor.y(), self.borderCursor.x()+15, self.borderCursor.y())
            painter.drawLine(self.borderCursor.x(), self.borderCursor.y()-15, self.borderCursor.x(), self.borderCursor.y()+15)

    def drawEntryAndEndPoints(self, painter: QPainter):
        if self.model.entryPoint is not None:
            pen = QPen(Qt.green, 5, Qt.SolidLine)
            painter.setPen(pen)

            entryPointDisplayPos = self.getMapCoords(QPointF(self.model.entryPoint[0], self.model.entryPoint[1]), False)
            painter.drawPoint(entryPointDisplayPos)
            self.invertYAxis(painter)
            painter.drawPoint(20, 50)
            pen.setColor(Qt.lightGray)
            painter.setPen(pen)
            painter.drawText(QPoint(25, 55), "Entry Point")
            self.invertYAxis(painter)

        if self.model.endPoint is not None:
            pen = QPen(Qt.red, 5, Qt.SolidLine)
            painter.setPen(pen)
            endPointDisplayPos = self.getMapCoords(QPointF(self.model.endPoint[0],
                                                           self.model.endPoint[1]),
                                                   False)
            painter.drawPoint(endPointDisplayPos)
            self.invertYAxis(painter)
            painter.drawPoint(20, 70)
            pen.setColor(Qt.lightGray)
            painter.setPen(pen)
            painter.drawText(QPoint(25, 75), "End Point")
            self.invertYAxis(painter)

    def invertYAxis(self, painter):
        painter.translate(0, self.height())
        painter.scale(1, -1)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # draw warning if no field is loaded yet
        if self.model.givenGeometry is None:
            painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter, "Open field file to begin")
        # draw cursor lines if hover
        if self.underHover:
            self.drawCrossLines(painter, self.cursor_pos)
        # invert Y axis
        self.invertYAxis(painter)

        # draw scale net
        self.drawWireNet(painter)

        # draw points
        self.drawEntryAndEndPoints(painter)

        # draw all site objects
        painter.translate(self.delta.x(), self.delta.y())

        if self.model.givenGeometry is not None:
            self.model.givenGeometry.drawItself(painter, self.sc)

        if self.model.tractorPathSeeding is not None:
            self.model.tractorPathSeeding.drawItself(painter, self.sc, color=QColor(255, 114, 12))

        if self.model.tractorPathSprinkling is not None:
            self.model.tractorPathSprinkling.drawItself(painter, self.sc, color=QColor(12, 240, 255))

        # TODO: add drawing for calculated geometry

        painter.translate(-self.delta.x(), -self.delta.y())
        # invert Y axis back
        self.invertYAxis(painter)
        self.drawScaleMark(painter)
        # finish drawing
        painter.end()

    def update(self) -> None:
        super().update()
        self.needToRepaint = False

    def mouseMoveEvent(self, e: PySide2.QtGui.QMouseEvent):
        self.cursor_pos = e.pos()
        wordPos = self.getWorldCoords(e.localPos(), self.sc, inversed=True)
        # print("cursor pos: x={}, y={}".format(wordPos.x(), wordPos.y()))
        if self.model.givenGeometry is not None:
            # get map coords:
            nearestPoint = nearest_polygon_point((wordPos.x(), wordPos.y()), self.model.givenGeometry.points)
            self.borderCursor = self.getMapCoords(QPointF(nearestPoint[0], nearestPoint[1]), True)

        if e.buttons() == Qt.LeftButton:
            # check if control not grab the movement:
            # self.touchControl.mouseMoveEvent(e)
            # if not self.dragging:
            point = e.localPos() - self.startDragging
            delta = point.manhattanLength()
            if delta > 10 or self.dragging:
                self.dragging = True
                self.pinned = False

                mouseShift = QPoint(e.localPos().x() - self.startDragging.x(),
                                    e.localPos().y() - self.startDragging.y())
                self.delta = QPointF(self.delta.x() + (e.localPos().x() - self.startDragging.x()),
                                     self.delta.y() - (e.localPos().y() - self.startDragging.y()))



                self.startDragging = e.localPos()
        self.callForRepaint()

    def leaveEvent(self, event:PySide2.QtCore.QEvent) -> None:
        self.underHover = False
        self.borderCursor = None

    def enterEvent(self, event:PySide2.QtCore.QEvent) -> None:
        self.underHover = True

    def mousePressEvent(self, e):
        self.startDragging = e.localPos()
        self.callForRepaint()

    def mouseReleaseEvent(self, e):
        # check if there was no dragging
        # and if wasn't - calculate click on objects
        if not self.dragging:
            if self.model.givenGeometry is not None:
                # get map coords:
                clickCoords = self.getWorldCoords(e.localPos(), inversed=True)
                nearestPoint = nearest_polygon_point((clickCoords.x(), clickCoords.y()), self.model.givenGeometry.points)
                if self.model.entryPoint is not None:
                    if self.model.endPoint is None:
                        # self.model.endPoint = nearestPoint
                        self.model.setEndPoint(nearestPoint)
                        # self.model.endPoint = [clickCoords.x(), clickCoords.y()]
                        print('set endPoint: x: {}, y: {}'.format(nearestPoint[0], nearestPoint[1]))
                else:
                    # self.model.entryPoint = nearestPoint
                    self.model.setEntryPoint(nearestPoint)
                    # self.model.entryPoint = [clickCoords.x(), clickCoords.y()]
                    print('set entryPoint: x: {}, y: {}'.format(nearestPoint[0], nearestPoint[1]))

        self.dragging = False
        self.startDragging = None
        self.callForRepaint()

    # region Properties
    def setMapLineColorLight(self, value):
        self._mapLineColorLight = value

    def getMapLineColorLight(self):
        return self._mapLineColorLight

    def setMapLineColorBold(self, value):
        self._mapLineColorBold = value

    def getMapLineColorBold(self):
        return self._mapLineColorBold

    def setAuxObjectsColor(self, value):
        self._auxObjectsColor = value

    def getAuxObjectsColor(self):
        return self._auxObjectsColor

    def setSc(self, value):
        self._sc = value
        self.moved.emit()
        self.update()

    def getSc(self):
        return self._sc

    def setDelta(self, value):
        self._delta = value
        self.moved.emit()
        self.update()

    def getDelta(self):
        return self._delta


    mapLineColorLight = Property(QColor, getMapLineColorLight, setMapLineColorLight)
    mapLineColorBold = Property(QColor, getMapLineColorBold, setMapLineColorBold)
    auxObjectsColor = Property(QColor, getAuxObjectsColor, setAuxObjectsColor)
    sc = Property(float, getSc, setSc)
    delta = Property(QPointF, getDelta, setDelta)

    # endregion


