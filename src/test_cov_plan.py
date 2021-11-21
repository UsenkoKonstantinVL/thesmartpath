import sys
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


from coverage_planning import AreaPolygon
from utm import Converter
from border_path import build_path, build_path2

def plot_coords(ax, ob):
    x, y = ob.xy
    plt.plot(x, y, 'o', color='#999999', zorder=1)
    
def plot_bounds(ax, ob):
    x, y = zip(*list((p.x, p.y) for p in ob.boundary))
    plt.plot(x, y, 'o', color='#000000', zorder=1)

def plot_line(ax, ob):
    x, y = ob.xy
    plt.plot(x, y, alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)

def shift(seq, n=0):
    a = n % len(seq)
    return seq[-a:] + seq[:-a]


def plot_poly():
    conv = Converter(sys.argv[1])
    ext = shift(conv.get_cartesian(), 50)
    holes = [] #[[(0, 3), (2, 3), (1, 6), (-3, 5)]]
    polygon = AreaPolygon(ext, ext[0], interior=holes, ft=10, angle=22.0)
    ll = polygon.get_area_coverage()


    fig, _ = plt.subplots()
    # ax = fig.add_subplot(121)
    # plt.plot(*polygon.rP.exterior.xy)
    plot_coords(None, ll)
    plot_bounds(None, ll)
    plot_line(None, ll)
    plt.plot(*polygon.P.exterior.xy)
    # plt.gca().set_aspect('equal', adjustable='box')
    # plt.rcParams['figure.figsize'] = [50, 50]
    plt.show()
    # list(ll.coords)
    # print(ll)


def test_build_plan():
    conv = Converter(sys.argv[1])
    border = conv.get_cartesian()

    debug_data = {}

    path = build_path2(
        border,
        border[0],
        border[-5],
        5,
        {},
        debug_data
    )

    wgs_path = conv.to_wgs(path)

    # import json
    # with open('test.txt', 'w') as f:
    #     json.dump(wgs_path, f, ensure_ascii=False)


    _x, _y = list(), list()

    for p in border:
        _x.append(p[0])
        _y.append(p[1])

    plt.plot(_x, _y)

    _x, _y = list(), list()

    for p in path:
        _x.append(p[0])
        _y.append(p[1])

    plt.plot(_x, _y)
    plt.scatter(_x, _y,
                marker='o',
                color="red",
                label="Точка выхода")

    _x, _y = list(), list()

    for p in debug_data['cov_poly']:
        _x.append(p[0])
        _y.append(p[1])

    plt.plot(_x, _y)
    plt.show()


def find_best():
    conv = Converter(sys.argv[1])
    ext = shift(conv.get_cartesian(), 50)
    holes = [] #[[(0, 3), (2, 3), (1, 6), (-3, 5)]]
    
    angles = list()
    for angle in np.linspace(0.0, 90.0, num=90):
        polygon = AreaPolygon(ext, ext[0], interior=holes, ft=20, angle=angle)
        ll = polygon.get_area_coverage()
        angles.append((ll.length, angle))

    print(sorted(angles)[0])


if __name__ == '__main__':
    test_build_plan()
    # find_best()