from PyQt5.QtCore import Qt, QMargins, QObject, pyqtSignal, QRunnable, QThreadPool
from mapObjects import Polygon, TractorPath

from utm import Converter
from test_cov_plan import build_path
import shapefile
from shapefile import Writer

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
            self.converter = Converter(filename)
        except IOError as e:
            print("Reading file error. Operation was aborted")
            print(e)
            return
        self.givenGeometry = Polygon()

        for p in self.converter.get_cartesian():
            self.givenGeometry.addPoint(p)

        self.geometryLoaded.emit()

    def exportF(self):
        print("SHOULD EXPORT")
        poly = self.tractorPathSeeding.points
        worldPoly = list(self.converter.to_wgs(poly))
        poly2 = self.tractorPathSprinkling.points
        worldPoly2 = list(self.converter.to_wgs(poly2))

        print('worldPoly')
        print(worldPoly)
        realWorldPoly = []
        realWorldPoly2 = []
        for point in worldPoly:
            realWorldPoly.append([point[0], point[1]])
        for point in worldPoly2:
            realWorldPoly2.append([point[0], point[1]])

        print('real world poly')
        print(realWorldPoly)
        # with shapefile.Writer("export_data.shp", shapefile.POLYLINEZ) as shp:
        #     shp.field('TEXT', "C")
        #     shp.line([realWorldPoly])
        #     shp.record(['Seeding'])
        w = shapefile.Writer('shapefiles/testlines/seeder')
        w.field('name', 'C')

        w.line([realWorldPoly])
        w.line([realWorldPoly2])

        w.record('seeder')
        w.record('sprikler')

        w.close()
        w = shapefile.Writer('shapefiles/testlines/sprikler')
        w.field('name', 'C')

        w.line([realWorldPoly2])

        w.record('sprikler')

        w.close()
        print('finished')

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
            self.tractorPathSprinkling = TractorPath(path)
            self.seedingPathChanged.emit()
            print('can draw')

    def calculate(self):
        print('core will calculate')
        self.createTestData()

        # when finish calculating, call:
        # self.seedingPathChanged.emit()
        # self.sprinklingPathChanged.emit()
        # this will let me know that geometry is ready to be displayed

    def doLongWork(self):
        # create thread and worker
        self.threadPool = QThreadPool()

        self.worker = HalCommunicatorWorker(core=self.core)
        self.killed.connect(self.worker.killMe)


class WorkerSignals(QObject):
    begin = pyqtSignal()
    end = pyqtSignal()


class CalcWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.signals.begin.emit()

    def run(self):
        pass
        # do work here

        # work finished
        self.signals.end.emit()


