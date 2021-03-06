from PyQt5.QtCore import Qt, QMargins, QObject, pyqtSignal, QRunnable, QThreadPool
from mapObjects import Polygon, TractorPath

from utm import Converter
from test_cov_plan import build_path
import shapefile
from shapefile import Writer


import constants as const
from border_path import build_path2



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

        self.seederWidth = const.Geometry.SEEDER_WIDTH
        self.sprinklerWidth = const.Geometry.SPRINKLER_WIDTH

        self.rowWidth = const.Geometry.SEEDER_ROW_WIDTH

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

    def exportF(self):
        print("SHOULD EXPORT")
        poly = self.tractorPathSeeding.points
        with shapefile.Writer("export_data.shp", shapefile.POLYGON) as shp:
            shp.field('Track', 'C')

            shp.poly([poly])
            shp.record('Seeding')


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
        # self.createTestData()

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

        seeder_border_step = self.seederWidth / 2 + 0.05  # ?????? ???????????? ???????????? + 5 ???? ??????????
        # seeder_path = build_path2(
        #     border=self.givenGeometry.points,
        #     entry_point=self.entryPoint,
        #     exit_point=self.endPoint,
        #     border_step=seeder_border_step,
        #     params={},
        #     debug_data={},
        # )

        sprinkler_border_step = seeder_border_step + 5 * self.rowWidth  # +5 ?????????? ?? ?????????????? ????????????
        sprinkler_path = build_path2(
            border=self.givenGeometry.points,
            entry_point=self.entryPoint,
            exit_point=self.endPoint,
            border_step=sprinkler_border_step,
            params={},
            debug_data={},
        )

        # self.tractorPathSeeding = TractorPath(points=seeder_path)
        # self.seedingPathChanged.emit()

        self.tractorPathSprinkling = TractorPath(points=sprinkler_path)
        self.sprinklingPathChanged.emit()
