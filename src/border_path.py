# python3.7+

import typing as t
import json
import numpy as np
from scipy import spatial

import matplotlib.pyplot as plt
from shapely import geometry
from shapely.ops import nearest_points

import constants as const
from coverage_planning import AreaPolygon
from smoother import PathSmoother


DEBUG = False

# Нужно ли проходить второй (внутренний) круг вдоль границ
GO_AROUND_TWICE = False

# Растояние на котором надо остановиться перед точкой старка,
# после прохождения круга вдоль границ, метры
# (выставить в 0 чтобы круг полностью замкнулся)
STOP_DIST = 0.3


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
        offset_paths.append(list(new_path.coords))


    for i in range(nleft_offset):
        dist = offset * i
        new_path = ls_path.parallel_offset(dist, 'left', join_style=join_style)
        offset_paths.append(list(new_path.coords))

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
    print('Here')

def find_point_and_index_of_nearest_point(point, poly):
    np_point = np.array(point)
    np_poly = np.array(poly)

    distance, index = spatial.KDTree(np_poly).query(np_point)

    return poly[index], index

def dist_between_points(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)

    return np.linalg.norm(p1 - p2)

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
    start1, start1_idx = find_point_and_index_of_nearest_point(p1, poly)
    end1, end1_idx = find_point_and_index_of_nearest_point(p2, poly)

    if start1_idx == end1_idx:
        return [], 0.0

    if start1_idx > end1_idx:
        p_l = len(poly)
        poly = poly[:] + poly[:]
        end1_idx += p_l

    full_path = []
    last_p = start1
    dist = 0
    for i in range(start1_idx, end1_idx + 1):
        cur_p = poly[i]
        full_path.append(cur_p)
        dist += dist_between_points(last_p, cur_p)
        last_p = cur_p

    return full_path, dist


def build_path(border: t.List[t.Tuple[float, float]],
               entry_point: t.Tuple[float, float],
               exit_point: t.Tuple[float, float],
               border_step: float,
               params: dict = {},
               debug_data = {},
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
        circle_path = []
    else:
        start_point = nearest_polygon_point(entry_point, inner_polygon)
        circle_path = [entry_point, start_point] + inner_polygon[:-1] + [start_point]
        # circle_path = smooth_data(circle_path)

    exit_point_at_cp = nearest_polygon_point(exit_point, circle_path)

    coverage_polygon = __shrink_or_swell_polygon(
        coords=inner_polygon,
        shrink_dist=border_step
    )
    coverage_path, cov_start_point, cov_end_point = find_best_coverage_path(
        coverage_polygon,
        circle_path,
        start_point,
        exit_point_at_cp,
        border_step * 2
    )


    start_point_at_cp = nearest_polygon_point(cov_start_point, circle_path)
    end_point_at_cp = nearest_polygon_point(cov_end_point, circle_path)

    path_to_coverage_start_point, _ = polygon_perimeter_between_points(start_point,
                                                                       start_point_at_cp,
                                                                       circle_path)
    path_to_end_point, _ = polygon_perimeter_between_points(end_point_at_cp,
                                                            exit_point_at_cp, 
                                                            circle_path)

    coverage_path = smooth_coverage_path(path_to_coverage_start_point + coverage_path + path_to_end_point + [exit_point])

    full_path = stitch_path(circle_path, coverage_path)

    debug_data['cov_poly'] = coverage_polygon

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

        if full_path:
            plt.plot([p[0] for p in full_path],
                     [p[1] for p in full_path],
                     label="Траектория " + path_name)

    return full_path



def build_path2(border: t.List[t.Tuple[float, float]],
                entry_point: t.Tuple[float, float],
                exit_point: t.Tuple[float, float],
                border_step: float,
                params: dict,
                debug_data = {},
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

    # inner_polygon = smooth_data(inner_polygon)
    if not inner_polygon:
        print("border_step is too big! Choose smaller value.")
        circle_path = []
    else:
        start_point = nearest_polygon_point(entry_point, inner_polygon)
        circle_path = add_points(inner_polygon[:-1])
        # circle_path = smooth_data(circle_path)
        circle_path2 =  __shrink_or_swell_polygon(
            coords=border,
            shrink_dist=border_step * 3
        )
        start_point2 = nearest_polygon_point(entry_point, circle_path2)

    exit_point_at_cp = nearest_polygon_point(exit_point, circle_path)
    exit_point_at_cp2 = nearest_polygon_point(exit_point, circle_path2)

    smoothed_circle_path = smooth_coverage_path(circle_path[len(circle_path) - 4: len(circle_path) - 1] + circle_path2[:4])
    full_circle_path = smooth_data([entry_point, start_point] + circle_path[:5]) + circle_path[5: len(circle_path) - 4] + smoothed_circle_path + circle_path2[4:]

    coverage_polygon = __shrink_or_swell_polygon(
        coords=border,
        shrink_dist=border_step * 5
    )
    coverage_path, cov_start_point, cov_end_point = find_best_coverage_path(
        coverage_polygon,
        circle_path2,
        start_point,
        exit_point_at_cp,
        border_step * 2
    )


    start_point_at_cp = nearest_polygon_point(cov_start_point, circle_path2)
    end_point_at_cp = nearest_polygon_point(cov_end_point, circle_path2)

    path_to_coverage_start_point, _ = polygon_perimeter_between_points(start_point2,
                                                                       start_point_at_cp,
                                                                       circle_path2)
    path_to_end_point, _ = polygon_perimeter_between_points(end_point_at_cp,
                                                            exit_point_at_cp2, 
                                                            circle_path2)

    path_to_end_point = path_to_end_point + [end_point_at_cp] #+ add_points([exit_point_at_cp2, end_point_at_cp, exit_point])

    coverage_path = smooth_coverage_path(path_to_coverage_start_point + coverage_path + path_to_end_point)

    full_path = stitch_path(full_circle_path, coverage_path)

    debug_data['cov_poly'] = coverage_polygon

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

        if full_path:
            plt.plot([p[0] for p in full_path],
                     [p[1] for p in full_path],
                     label="Траектория " + path_name)

    return full_path 



def smooth_data(path):
    smoother = PathSmoother(1.0 / 5.0, tol=1e-2)
    x0 = np.array(path)

    x0 = x0.reshape((-1))
    res = smoother.smooth(x0)
    return res.tolist()


def add_points(poly):
    big_x0 = list()
    for i in range(1, len(poly)):
        p1 = np.array(poly[i-1])
        p2 = np.array(poly[i])
        ds = np.linalg.norm(p1-p2)

        if ds < 10:
            s = [p1.tolist(), p2.tolist()]
            big_x0.extend(s)
        else:
            s = np.linspace(p1, p2, num=int(ds / 10.0))
            big_x0.extend(s.tolist())
    return big_x0


def smooth_coverage_path(path):
    big_x0 = list()
    for i in range(1, len(path)):
        p1 = np.array(path[i-1])
        p2 = np.array(path[i])
        ds = np.linalg.norm(p1-p2)

        s = np.linspace(p1, p2, num=int(ds / 10.0))
        big_x0.extend(s.tolist())
    
    # for i in range(5, len(path)):
    #     p1 = np.array(path[i-1])
    #     p2 = np.array(path[i])
    #     ds = np.linalg.norm(p1-p2)

    #     s = np.linspace(p1, p2, num=int(ds / 1.0))
    #     big_x0.extend(s.tolist())
    x0 = np.array(big_x0)

    x0 = x0.reshape((-1))
    smoother = PathSmoother(1.0 / 5.0, tol=1e-2)
    res = smoother.smooth(x0).tolist()
    return res


def stitch_path(*args):
    full_path = list()
    for p in args:
        full_path.extend(p)
    return full_path

def find_best_coverage_path(
    coverage_polygon,
    circle_path,
    start_point,
    exit_point,
    ft=20
):
    conf = list()
    for angle in np.linspace(0.0, 90.0, num=91):
        try:
            polygon = AreaPolygon(coverage_polygon, coverage_polygon[0], interior=[], ft=ft, angle=angle)
            ll = polygon.get_area_coverage()

            start_path = list(ll.coords)[0]
            end_path = list(ll.coords)[-1]

            start_path_on_cp = nearest_polygon_point(start_path, circle_path)
            end_path_on_cp = nearest_polygon_point(end_path, circle_path)



            _, l1 = polygon_perimeter_between_points(start_point,
                                                    start_path_on_cp,
                                                    circle_path)
            _, l2 = polygon_perimeter_between_points(end_path_on_cp,
                                                    exit_point, 
                                                    circle_path)

            conf.append((ll.length + l1 + l2, angle))
        except:
            pass

    best_angle = sorted(conf)[0][1]
    polygon = AreaPolygon(coverage_polygon, coverage_polygon[0], interior=[], ft=ft, angle=best_angle)
    ll = polygon.get_area_coverage()

    path = list(ll.coords)
    path = path[: len(path) - 1]

    return path, path[0], path[-1]


def find_best_config(coverage_polygon, ft=20):
    conf = list()
    for angle in np.linspace(-90.0, 90.0, num=90):
        polygon = AreaPolygon(coverage_polygon, coverage_polygon[0], interior=[], ft=ft, angle=angle)
        ll = polygon.get_area_coverage()
        conf.append((ll.length, angle))

    best_angle = sorted(conf)[0][1]
    polygon = AreaPolygon(coverage_polygon, coverage_polygon[0], interior=[], ft=ft, angle=best_angle)
    ll = polygon.get_area_coverage()

    path = list(zip(ll.xy))
    path = path[: len(path) - 2]

    return path, path[0], path[-1]


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
