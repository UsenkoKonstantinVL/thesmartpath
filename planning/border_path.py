import matplotlib.pyplot as plt
from shapely import geometry
from shapely.ops import nearest_points

import constants as const


DEBUG = True


def shrink_or_swell_polygon(coords: list,
                            shrink_dist: float = 1.0,
                            swell: bool = False):
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

    return list(geometry.mapping(polygon_resized)['coordinates'][0])


def nearest_polygon_point(point: tuple,
                          polygon_coords: list):
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
               border_step: float,
               path_name: str = "1") -> list:
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

    path = [entry_point, start_point] + inner_polygon[1:-1]

    # Отрисовка в режиме отладки
    if DEBUG:
        if path_name == '1':
            plt.plot(*geometry.Polygon(border).exterior.xy, label="Границы поля")
            plt.axis('equal')

            plt.scatter(entry_point[0], entry_point[1],
                        marker='o',
                        color="red",
                        label="Точка входа")

        plt.plot(*geometry.Polygon(path).exterior.xy,
                 label="Траектория " + path_name)

    return path


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

    step = const.Geometry.SEEDER_WIDTH / 2

    path1 = build_path(
        border=border_3,
        entry_point=entry_1,
        border_step=step,
        path_name='1'
    )
    path2 = build_path(
        border=path1 + [path1[0]],
        entry_point=entry_1,
        border_step=step,
        path_name='2'
    )

    if DEBUG:
        plt.legend(loc='upper left')
        plt.show()
