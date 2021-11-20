# python3.7+

import typing as t
import json

import matplotlib.pyplot as plt
from shapely import geometry
from shapely.ops import nearest_points

import constants as const


DEBUG = True


# TODO учет органичений:
#  - расчет отступов для избежания повторных посевов/поливов, затаптывания посева, выездов за границы и т.д.
#  - мин. радиус поворота - 5 м.


def __shrink_or_swell_polygon(coords: t.List[t.Tuple[float, float]],
                              shrink_dist: float = 1.0,
                              swell: bool = False):
    """
    Сжимает или расширяет полигон на заданный отступ.

    Args:
        coords: Координаты полигона
        swell: Флаг растягивания/сжатия
        shrink_dist: Растояние отступа от границы исходного полигона

    Returns:
        Координаты полученного полигона
    """
    polygon = geometry.Polygon(coords)

    if swell:
        polygon_resized = polygon.buffer(shrink_dist)  # Растянуть
    else:
        polygon_resized = polygon.buffer(-shrink_dist)  # Сжать

    if polygon_resized.is_empty:
        return []

    return list(geometry.mapping(polygon_resized)['coordinates'][0])


def __nearest_polygon_point(point: t.Tuple[float, float],
                            polygon_coords: t.List[t.Tuple[float, float]]):
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


def build_path(border: t.List[t.Tuple[float, float]],
               entry_point: t.Tuple[float, float],
               border_step: float,
               path_name: str = "1") -> list:
    """
    Строит маршрут вдоль границ площадки

    border: Координаты границ поля в формате масива пар x, y.
            Пример: [(0, 0), (0, 5), (5, 5), (5, 0)]
    entry_point: Координаты точки входа.
                 Пример: (0, 0)
    border_step: Необходимое растояние от границы поля до траектории в метрах.
                 Должно быть равно половине длины агрегата (сеялки/поливалки)
    """
    inner_polygon = __shrink_or_swell_polygon(
        coords=border,
        shrink_dist=border_step
    )
    if not inner_polygon:
        print("border_step is too big! Choose smaller value.")
        path = []
    else:
        start_point = __nearest_polygon_point(entry_point, inner_polygon)
        path = [entry_point, start_point] + inner_polygon[:-1]

    # Отрисовка в режиме отладки
    if DEBUG:
        if path_name == '1':
            plt.plot(*geometry.Polygon(border).exterior.xy, label="Границы поля")
            plt.axis('equal')

            plt.scatter(entry_point[0], entry_point[1],
                        marker='o',
                        color="red",
                        label="Точка входа")
        if path:
            plt.plot(*geometry.Polygon(path).exterior.xy,
                     label="Траектория " + path_name)

    return path


def write_path_to_json(
        path: t.List[t.Tuple[float, float]],
        filename: str = 'path.json'
):
    with open(filename, 'w') as f:
        json.dump(path, f, ensure_ascii=False)


# test
if __name__ == "__main__":
    border_0 = [
        (0, 0),
        (0, 10),
        (10, 0)
    ]

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

    entry_1 = (2, 0)

    step = 0.2
    step_1 = const.Geometry.SEEDER_WIDTH / 2

    path1 = build_path(
        border=border_1,
        entry_point=entry_1,
        border_step=step,
        path_name='1'
    )

    if path1:
        path2 = build_path(
            border=path1 + [path1[0]],
            entry_point=entry_1,
            border_step=step,
            path_name='2'
        )

        print(path2)

        write_path_to_json(path=path2)

    if DEBUG:
        plt.legend(loc='upper left')
        plt.show()
