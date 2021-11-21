from PyQt5.QtCore import Qt, QMargins, QObject, pyqtSignal, QRunnable, QThreadPool
from mapObjects import Polygon, TractorPath

from utm import Converter
from test_cov_plan import build_path

class Model(QObject):
    geometryLoaded = pyqtSignal()
    pointsChanged = pyqtSignal()
    seedingPathChanged = pyqtSignal()
    sprinklingPathChanged = pyqtSignal()
    startLongOperation = pyqtSignal()
    longOperationFinished = pyqtSignal()

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

    def createTestData(self):
        path = build_path(
            self.givenGeometry.points,
            self.entryPoint,
            self.endPoint,
            20,
            {}
        )
        print(path)
        if path:
            self.tractorPathSeeding = TractorPath(path)
            self.seedingPathChanged.emit()
            print('can draw')

    def calculate(self):
        print('core will calculate')
        self.createTestData()

        # when finish calculating, call:
        # self.seedingPathChanged.emit()
        # self.sprinklingPathChanged.emit()
        # this will let me know that geometry is ready to be displayed


