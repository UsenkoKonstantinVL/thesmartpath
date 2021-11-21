from PyQt5.QtCore import Qt, QMargins, QObject, pyqtSignal
from mapObjects import Polygon

from utm import Converter

import constants
from border_path import build_path



class Model(QObject):
    geometryLoaded = pyqtSignal()
    pointsChanged = pyqtSignal()
    def __init__(self):
        super().__init__()

        self.givenGeometry = None
        self.tractorPathSeeding = None
        self.tractorPathSprinkling = None

        self.tractorWidth = None
        self.tractorWheelBase = None
        self.seederWidth = None
        self.sprinklerWidth = None
        self.rowWidth = None
        self.turnRadius = None

        self.entryPoint = None
        self.endPoint = None


    def pullGeometryFromFile(self, filename):
        try:
            converter = Converter(filename)
        except IOError as e:
            print("Reading file error. Operation was aborted")
            print(e)
            return
        self.givenGeometry = Polygon()

        for p in converter.get_cartesian():
            self.givenGeometry.addPoint(p)

        self.geometryLoaded.emit()

    def setEntryPoint(self, point):
        self.entryPoint = point
        self.pointsChanged.emit()

    def setEndPoint(self, point):
        self.endPoint = point
        self.pointsChanged.emit()

    def calculate(self):

        seeder_border_step = self.seederWidth / 2 + 0.05  # 5 см запас
        seeder_path = build_path(
            border=self.givenGeometry.points,
            entry_point=self.entryPoint,
            exit_point=self.exitPoint,
            border_step=seeder_border_step,
            params={},
            debug_data={},
        )

        sprinkler_border_step = seeder_border_step + 5 * self.rowWidth
        sprinkler_path = build_path(
            border=self.givenGeometry.points,
            entry_point=self.entryPoint,
            exit_point=self.exitPoint,
            border_step=sprinkler_border_step,
            params={},
            debug_data={},
        )

        self.tractorPathSeeding = seeder_path
        self.tractorPathSprinkling = sprinkler_path
