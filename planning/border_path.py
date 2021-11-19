import shapely

from shapely import geometry
from shapely.ops import nearest_points
import matplotlib.pyplot as plt


DEBUG = True


def shrink_or_swell_polygon(coords, shrink_dist=1.0, swell=False):
    """
    Сжимает или расширяет полигон на заданный отступ.

    Args:
        coords:
        swell:
        shrink_dist:

    Returns:
        Координаты полученного полигона
    """
    polygon = geometry.Polygon(coords)

    if swell:
        polygon_resized = polygon.buffer(shrink_dist)  # Растянуть
    else:
        polygon_resized = polygon.buffer(-shrink_dist)  # Сжать

    # Отрисовка в режиме отладки
    if DEBUG:
        x, y = polygon.exterior.xy
        plt.plot(x, y, label="Границы поля")
        x, y = polygon_resized.exterior.xy
        plt.plot(x, y, label="Маршрут")
        plt.axis('equal')

    return geometry.mapping(polygon_resized)['coordinates'][0]


def nearest_polygon_point(point, polygon_coords):
    """
    Находит ближайшую к заданной точке точку на границе полигона.

    Args:
        point: Заданная точка
        polygon_coords: Координаты полигона

    Returns:
        Ближайшая точка
    """
    poly = geometry.Polygon(polygon_coords)
    point = geometry.Point(point)
    p1 = nearest_points(poly, point)[0]
    return p1.x, p1.y


def build_path(border: list,
               entry_point: tuple,
               border_step: float) -> list:
    """
    border: Координаты границ поля в формате масива пар x, y.
            Пример: [(0, 0), (0, 5), (5, 5), (5, 0)]
    entry_point: Координаты точки входа.
                 Пример: (0, 0)
    border_step: Необходимое растояние от границы поля до траектории в метрах.
                 Должно быть равно половине длины агрегата (сеялки/поливалки)
    """
    inner_polygon = shrink_or_swell_polygon(coords=border,
                                            shrink_dist=border_step)

    start_point = nearest_polygon_point(entry_point, inner_polygon)

    start_line = geometry.LineString(
        [entry_point, start_point]
    )

    if DEBUG:
        plt.scatter(entry_point[0], entry_point[1],
                    marker='o',
                    color="red",
                    label="Точка входа")

        plt.plot(start_line.xy[0], start_line.xy[1])

    return []


# test
if __name__ == "__main__":
    border_1 = [
        (0, 0),
        (0, 5),
        (5, 5),
        (5, 0)
    ]
    border_2 = [
        (0, 0),
        (0, 10),
        (10, 10),
        (10, 0)
    ]
    border_3 = [
        (0, 0),
        (0, 100),
        (20, 100),
        (30, 60),
        (40, 100),
        (60, 100),
        (60, 0),
        (40, 10),
        (40, 40),
        (20, 40),
        (20, 10)
    ]
    entry_1 = (3, 2)

    path = build_path(
        border=border_3,
        entry_point=entry_1,
        border_step=5
    )

    if DEBUG:
        plt.legend(loc='upper left')
        plt.show()
