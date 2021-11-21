# python3.7+

import typing as t
import json
import numpy as np

import matplotlib.pyplot as plt
from shapely import geometry
from shapely.ops import nearest_points

import constants as const
from coverage_planning import AreaPolygon


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


def nearest_polygon_point(point: t.Tuple[float, float],
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


def build_n_offset_paths(path: t.List[t.Tuple[float, float]], 
                         nright_offset: int, 
                         nleft_offset: int, 
                         offset: float, 
                         join_style: int = 2) -> t.List[t.List[t.Tuple[float, float]]]:
    """
    Построение n рядов со смещение влево и впрово на offset.

    Args:
        path (t.List[t.Tuple[float, float]]): путь.
        nright_offset (int): количество траекторий слева.
        nleft_offset (int): количество траекторий справа.
        offset (float): смещение в метрах.
        join_style (int): тип углов, могут быть:
            1 - round;
            2 - mitre;
            3 - bevel;
            (https://shapely.readthedocs.io/en/stable/manual.html#shapely.geometry.JOIN_STYLE)
            По дефолту - 2.
    """
    ls_path = geometry.LineString(path)

    offset_paths = list()

    for i in range(nright_offset):
        dist = offset * i
        new_path = ls_path.parallel_offset(dist, 'right', join_style=join_style)
        offset_paths.append(new_path.coords)


    for i in range(nleft_offset):
        dist = offset * i
        new_path = ls_path.parallel_offset(dist, 'left', join_style=join_style)
        offset_paths.append(new_path.coords)

    return offset_paths


def build_n_tracks(border: t.List[t.Tuple[float, float]],
                   width: float,
                   n_rows: int) -> t.List[t.List[t.Tuple[float, float]]]:
    """
    Строит N треков рядков насаждений.

    Args:
        border (t.List[t.Tuple[float, float]]): граница.
        width (float): ширина отступа между входной границей и последним рядом грядков.
        n_rows (int): количество грядок.

    Return:
        t.List[t.List[t.Tuple[float, float]]]: список грядок в порядке уменьшения периметра границы.

    """
    dwidth = width / n_rows

    temp_border = border
    borders = list()
    for i in range(n_rows):
        shrinked_border = __shrink_or_swell_polygon(temp_border, dwidth)
        borders.append(shrinked_border)
        temp_border = shrinked_border

    return borders 
    

def build_path(border: t.List[t.Tuple[float, float]],
               entry_point: t.Tuple[float, float],
               exit_point: t.Tuple[float, float],
               border_step: float,
               params: dict,
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
        start_point = nearest_polygon_point(entry_point, inner_polygon)
        path = [entry_point, start_point] + inner_polygon[:-1]

    
    coverage_polygon = None
    coverage_path, cov_start_point, cov_end_point = find_best_config(coverage_polygon, 20)

    path_to_coverage_start_point = None
    path_to_end_point = None

    full_path = stitch_path(path, path_to_coverage_start_point, path_to_end_point)


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


def stitch_path(*args):
    pass


def find_best_config(coverage_polygon, ft):
    conf = list()
    for angle in np.linspace(-90.0, 90.0, num=90):
        polygon = AreaPolygon(coverage_polygon, coverage_polygon[0], interior=[], ft=ft, angle=angle)
        ll = polygon.get_area_coverage()
        conf.append((ll.length, angle))

    return sorted(conf)[0]


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
