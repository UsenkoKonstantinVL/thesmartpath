import numpy as np
from scipy import optimize

class PathSmoother(object):
    def __init__(self, max_curv, tol=1e-8, method='CG'):
        self.MAX_CURV = max_curv

        self.TOL = tol
        self.OPT_METHOD = method

 
    def calc_curvatire(self, x):
        dx_dt = np.gradient(x[:, 0])
        dy_dt = np.gradient(x[:, 1])
        # velocity = np.array([ [dx_dt[i], dy_dt[i]] for i in range(dx_dt.size)])

        # ds_dt = np.sqrt(dx_dt * dx_dt + dy_dt * dy_dt)

        # d2s_dt2 = np.gradient(ds_dt)
        d2x_dt2 = np.gradient(dx_dt)
        d2y_dt2 = np.gradient(dy_dt)

        curvature = np.abs(d2x_dt2 * dy_dt - dx_dt * d2y_dt2) / (dx_dt * dx_dt + dy_dt * dy_dt)**1.5
        return curvature, dx_dt, dy_dt, d2x_dt2, d2y_dt2

    def objective(self, x, x0):

        cost = 0
        curvature, dx_dt, dy_dt, d2x_dt2, d2y_dt2 = self.calc_curvatire(x.reshape(-1, 2))

        l = len(x)

        x_0 = np.array([x[0], x[1]])
        x0_0 = np.array([x0[0], x0[1]])

        x_last = np.array([x[l - 2], x[l - 1]])
        x0_last = np.array([x0[l - 2], x0[l - 1]])

        cost += 100 * (x_0 - x0_0).T.dot(x_0 - x0_0)
        cost += 100 * (x_last - x0_last).T.dot(x_last - x0_last)

        for i in range(1, int(len(x) / 2) - 1):
            x_i = np.array([x[2*i], x[2*i + 1]])
            x_1i = np.array([x[2*(i-1)], x[2*(i-1) + 1]])
            x_i1 = np.array([x[2*(i+1)], x[2*(i+1) + 1]])

            dx1 = x_i - x_1i
            dx2 = x_i1 - x_i

            theta = np.arctan2(dx2[1], dx2[0]) - np.arctan2(dx1[1], dx1[0])

            # theta_dif = np.math.atan2(np.sin(theta), np.cos(theta))
            # if ()
            cost += 0.0001 * (np.math.atan2(np.sin(theta), np.cos(theta))) ** 2
            # max_a = max(max_a, np.math.atan2(np.sin(theta), np.cos(theta)))

            d = x_i - (x_1i + x_i1) / 2.0

            x0_i = np.array([
                x0[2*i],
                x0[2*i + 1]
            ])

            # print((x0_i - x_i).T.dot(x0_i - x_i))
            cost += 5.0 * (x0_i - x_i).T.dot(x0_i - x_i)
            cost += 15.0 * d.T.dot(d)

            # cost += 1 * dx_dt[i] * dx_dt[i]
            # cost += 1 * dy_dt[i] * dy_dt[i]

            # cost += 1 * d2x_dt2[i] * d2x_dt2[i]
            # cost += 1 * d2y_dt2[i] * d2y_dt2[i]

            if curvature[i] > self.MAX_CURV:
                cost += 0.0001 * curvature[i] * curvature[i]

        return cost

    def smooth(self, path):
        u"""
        Path smoothing algorythms.

        Args:
            path (np.ndarray): матрица nx2.

        Return:
            np.ndarray: матрица nx2.
        """
        
        solution = optimize.minimize(self.objective, 
                                     x0=path, 
                                     method=self.OPT_METHOD,
                                     args=(path,),
                                     #  method='SLSQP',
                                     tol=self.TOL)#,

        return np.array(solution.x).reshape((-1, 2))


if __name__ == '__main__':
    # x0 = [[2, 0], [2.0, 0.4], [0.4, 0.4], [0.4, 4.6], [4.6, 4.6], [4.6, 0.4], [3.0, 0.4]]
    x0 = [[2, 0], [2.0, 8.0], [-5, 8.0]]
    big_x0 = list()
    for i in range(1, len(x0)):
        p1 = np.array(x0[i-1])
        p2 = np.array(x0[i])
        ds = np.linalg.norm(p1-p2)

        s = np.linspace(p1, p2, num=int(ds / 0.5))
        big_x0.extend(s.tolist())
    x0 = np.array(big_x0)

    x0 = x0.reshape((-1))

    smoother = PathSmoother(1.0 / 5.0, tol=1e-2)
    res = smoother.smooth(x0)

    import matplotlib.pyplot as plt

    _x, _y = list(), list()

    for i in range(int(len(x0) / 2)):
        _x.append(x0[i*2])
        _y.append(x0[i*2 + 1])

    # plt.plot(_x, _y)

    _x, _y = list(), list()

    print(res)

    for p in res:
        _x.append(p[0])
        _y.append(p[1])

    plt.plot(_x, _y)
    plt.show()