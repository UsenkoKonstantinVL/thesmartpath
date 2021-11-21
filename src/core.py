from PySide2.QtCore import Qt, QMargins, QObject
from mapObjects import Polygon

from utm import Converter
class Model(QObject):
    def __init__(self):
        super().__init__()

        self.givenGeometry = None
        self.tractorPathSeeding = None
        self.tractorPathSprinkling = None

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

        print(self.givenGeometry)