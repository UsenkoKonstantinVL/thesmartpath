import sys
import shapefile
import matplotlib.pyplot as plt


if __name__ == '__main__':
    sf = shapefile.Reader(sys.argv[1])
    feature = sf.shapeRecords()[0]
    first = feature.shape.__geo_interface__  
    print(first['coordinates'][0]) # (GeoJSON format)

    x, y = list(), list()

    for p in first['coordinates'][0]:
        x.append(p[0])
        y.append(p[1])

    plt.plot(x, y)
    plt.show()
