# python3.7+

import typing as t
import json

import matplotlib.pyplot as plt
from shapely import geometry
from shapely.ops import nearest_points

import constants as const


DEBUG = True

# Нужно ли проходить второй (внутренний) круг вдоль границ
GO_AROUND_TWICE = False

# Растояние на котором надо остановиться перед точкой старка,
# после прохождения круга вдоль границ, метры
# (выставить в 0 чтобы круг полностью замкнулся)
STOP_DIST = 0.3


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
                            poly: t.List[t.Tuple[float, float]]):
    """
    Находит ближайшую к заданной *вне полигона* точке точку на границе полигона.

    Args:
        point: Заданная *вне* границы полигона точка
        poly: Координаты полигона

    Returns:
        Ближайшая точка
    """
    poly = geometry.Polygon(poly)
    point = geometry.Point(point)
    p1 = nearest_points(poly, point)[0]
    return p1.x, p1.y


def __nearest_polygon_points(point, poly) -> t.Tuple[t.Tuple[float, float],
                                                     t.Tuple[float, float]]:
    """
    Находит две ближайшие точки (преломления) к заданной *на* полигоне точке.

    Args:
        point: Заданная *на* гранце полигона точка
        poly: Координаты полигона
    """
    for p1 in poly[:-1]:
        for p2 in poly[1:]:
            line = geometry.LineString([p1, p2])
            point = geometry.Point(point)
            if line.distance(point) < 1e-8:
                return p1, p2


def polygon_perimeter_between_points(p1: t.Tuple[float, float],
                                     p2: t.Tuple[float, float],
                                     poly: t.List[t.Tuple[float, float]]) -> t.Tuple[t.List[t.Tuple[float, float]], float]:
    """
    Находит *кратчайший* (из двух) отрезок периметра полигона
    между двумя точками на этом периметре.
    Другими словами: с какой стороны (левой или правой) обходить периметр,
    чтобы быстрее всега добраться до целевой точки на нем

    Args:
        p1: точка старта обхода
        p2: целевая точка
        poly: полигон
    """
    start1, start2 = __nearest_polygon_points(p1, poly)
    end1, end2 = __nearest_polygon_points(p2, poly)

    start1_idx = poly.index(start1)
    start2_idx = poly.index(start2)

    end1_idx = poly.index(end1)
    end2_idx = poly.index(end2)

    # Длина по часовой
    cw_len = 0

    # Идем по часовой
    cur_idx = start1_idx
    cw_path = [p1, poly[cur_idx]]
    cw_len += geometry.Point(p1).distance(geometry.Point(start1))
    while cur_idx != end1_idx:
        cur_p = poly[cur_idx]
        next_p = poly[cur_idx + 1]
        cw_path.append(next_p)
        cw_len += geometry.Point(cur_p).distance(geometry.Point(next_p))

        if cur_idx == len(poly) - 1:
            cur_idx = 0
        else:
            cur_idx += 1
    cw_len += geometry.Point(end1).distance(geometry.Point(p2))
    cw_path.append(p2)

    return cw_path, cw_len


def __build_final_path(start: t.Tuple[float, float],
                       border_path: t.List[t.Tuple[float, float]],
                       exit_point: t.Tuple[float, float]) -> t.List[t.Tuple[float, float]]:
    """
    Строит финишную траекторию до точки выхода

    Args:
        start:
        border_path:
        exit_point:

    Returns: Координаты финишной траектории
    """
    path = [start]

    nearest_border_path_point = __nearest_polygon_point(
        start,
        border_path
    )
    path.append(nearest_border_path_point)

    nearest_to_exit = __nearest_polygon_point(
        exit_point,
        border_path
    )

    # TODO main logic

    if DEBUG:
        pass
    return path


def build_path(border: t.List[t.Tuple[float, float]],
               entry_point: t.Tuple[float, float],
               exit_point: t.Tuple[float, float],
               border_step: float,
               path_name: str = "1") -> list:
    """
    Строит маршрут вдоль границ площадки

    border: Координаты границ поля в формате масива пар x, y.
            Пример: [(0, 0), (0, 5), (5, 5), (5, 0)]
    entry_point: Координаты точки входа.
                 Пример: (0, 0)
    exit_point: Координаты точки выхода.
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

        path = [entry_point, start_point] + inner_polygon[:-1] + [start_point]

    # Отрисовка в режиме отладки
    if DEBUG:
        if path_name == '1':
            plt.plot([p[0] for p in border],
                     [p[1] for p in border],
                     label="Границы поля")
            plt.axis('equal')

            plt.scatter(entry_point[0], entry_point[1],
                        marker='o',
                        color="green",
                        label="Точка входа")

            plt.scatter(exit_point[0], exit_point[1],
                        marker='o',
                        color="red",
                        label="Точка выхода")

        if path:
            plt.plot([p[0] for p in path],
                     [p[1] for p in path],
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

    # test final path
    poly = [
        (0, 0),
        (0, 10),
        (10, 10),
        (10, 0),
        (0, 0)
    ]
    a = (4, 0)
    b = (7, 10)

    path, path_len = polygon_perimeter_between_points(b, a, poly)
    print("path: ", path)
    print("path len: ", path_len)

    ###########
    border_0 = [
        (0, 0),
        (0, 10),
        (10, 0),
        (0, 0)
    ]

    border_1 = [
        (0, 0),
        (0, 5),
        (5, 5),
        (5, 0),
        (0, 0)
    ]
    border_2 = [
        (0, 0),
        (0, 10),
        (10, 10),
        (10, 0),
        (0, 0)
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
        (20, 10),
        (0, 0)
    ]

    entry = (2, 0)

    exit = (4, 5)

    step = 0.2
    step_1 = const.Geometry.SEEDER_WIDTH / 2

    path1 = build_path(
        border=border_1,
        entry_point=entry,
        exit_point=exit,
        border_step=step,
        path_name='1'
    )

    if GO_AROUND_TWICE and path1:
        path2 = build_path(
            border=path1 + [path1[0]],
            entry_point=entry,
            exit_point=exit,
            border_step=step,
            path_name='2'
        )

        print(path2)

        write_path_to_json(path=path2)

    if DEBUG:
        plt.legend(loc='upper left')
        plt.show()
