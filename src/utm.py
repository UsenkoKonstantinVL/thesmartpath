import pyproj
import shapefile


_projections = {}


def zone(coordinates):
    if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
        return 32
    if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
        if coordinates[0] < 9:
            return 31
        elif coordinates[0] < 21:
            return 33
        elif coordinates[0] < 33:
            return 35
        return 37
    return int((coordinates[0] + 180) / 6) + 1


def letter(coordinates):
    return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]


def project(coordinates):
    z = zone(coordinates)
    l = letter(coordinates)
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    x, y = _projections[z](coordinates[0], coordinates[1])
    if y < 0:
        y += 10000000
    return z, l, x, y


def unproject(proj, l, coords):
    if l < 'N':
        for p in coords:
            p[1] -= 10000000
    wgs = [proj(p[0], p[1], inverse=True) for p in coords]
    return wgs


class Converter(object):
    def __init__(self, shp_file):
        u"""
        Args:
            shp_file (str): path to shp file.
        """
        sf = shapefile.Reader(shp_file)
        feature = sf.shapeRecords()[0]
        first = feature.shape.__geo_interface__ 
        polygon = first['coordinates'][0] if isinstance(first['coordinates'][0], list) else first['coordinates']

        
        self.z = zone(polygon[0])
        self.letter = letter(polygon[0])

        self.proj = self.__converter(self.z)

        self.cartesian = [self.proj(p[0], p[1])for p in polygon]
        self.wgs = polygon

    def __converter(self, zone):
        proj = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84')
        return proj

    def transform_to_cartesian(self, coords):
        pass

    def to_wgs(self, coords):
        return unproject(self.proj, self.letter, coords)

    def get_wgs(self):
        u"""
        Return polygon in wgs coordinates.

        Return:
            list.
        """
        return self.wgs

    def get_cartesian(self):
        u"""
        Return polygon in cartesiane coordinates.

        Return:
            list.
        """
        return self.cartesian


if __name__ == '__main__':
    import sys
    import matplotlib.pyplot as plt

    converter = Converter(sys.argv[1])

    x, y = list(), list()

    for p in converter.get_wgs():
        x.append(p[0])
        y.append(p[1])

    plt.plot(x, y)
    plt.show()

    x, y = list(), list()

    for p in converter.get_cartesian():
        x.append(p[0])
        y.append(p[1])

    plt.plot(x, y)
    plt.show()
