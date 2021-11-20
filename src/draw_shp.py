import sys
import shapefile
import matplotlib.pyplot as plt


if __name__ == '__main__':
    sf = shapefile.Reader(sys.argv[1])
    feature = sf.shapeRecords()[0]
    first = feature.shape.__geo_interface__ 
    polygon = first['coordinates'] if isinstance(first['coordinates'], list) else first['coordinates'][0]
    print(polygon) # (GeoJSON format)

    x, y = list(), list()

    for p in polygon:
        x.append(p[0])
        y.append(p[1])

    plt.plot(x, y)
    plt.show()
