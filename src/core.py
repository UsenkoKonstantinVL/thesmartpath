from PyQt5.QtCore import Qt, QMargins, QObject, pyqtSignal
from mapObjects import Polygon

from utm import Converter
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
        print('core will calculate')


