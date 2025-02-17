import numpy as np
from scipy.interpolate import griddata, RectBivariateSpline
import pandas as pd
import xarray as xr  # conda install -c conda-forge xarray dask netCDF4 bottleneck
from const import *


class DrawPoint:
    def __init__(self, x, y, ax):
        self.x = x
        self.y = y
        self.ax = ax
        self.scat = None

    def draw(self):
        self.scat = self.ax.scatter(self.x, self.y, c="b")

    def clean(self):
        if self.scat:
            self.scat.remove()
            self.scat = None


class Point:
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y


class Ellipse:
    def __init__(self, t, x0, y0, p1, p2, p3, ax=None):
        self.t = t
        self.x0 = x0
        self.y0 = y0
        if isinstance(p1, DrawPoint):
            self.p1 = np.array([p1.x, p1.y])
            self.p2 = np.array([p2.x, p2.y])
            self.p3 = np.array([p3.x, p3.y])
        else:
            self.p1 = p1
            self.p2 = p2
            self.p3 = p3
        self.center = (self.p1 + self.p2) / 2
        self.a = np.linalg.norm(self.p1 - self.p2) / 2
        self.b, self.angle = self.calculate_minor_axis_and_angle()
        self.R = np.array([[np.cos(self.angle), -np.sin(self.angle)],
                           [np.sin(self.angle), np.cos(self.angle)]])
        self.ax = ax
        self.plot = None
        self.points = None

    def calculate_minor_axis_and_angle(self):
        major_axis_vector = self.p2 - self.p1
        angle = np.arctan2(major_axis_vector[1], major_axis_vector[0])

        rotation_matrix = np.array([[np.cos(-angle), -np.sin(-angle)],
                                    [np.sin(-angle), np.cos(-angle)]])
        rotated_p3 = rotation_matrix @ (self.p3 - self.center)
        b = np.abs(rotated_p3[1])
        return b, angle

    def convert2ll(self, lat_int, lon_int):
        return [lat_int(self.x0, self.y0)[0][0], lon_int(self.x0, self.y0)[0][0],
                lat_int(self.p1[0], self.p1[1])[0][0], lon_int(self.p1[0], self.p1[1])[0][0],
                lat_int(self.p2[0], self.p2[1])[0][0], lon_int(self.p2[0], self.p2[1])[0][0],
                lat_int(self.p3[0], self.p3[1])[0][0], lon_int(self.p3[0], self.p3[1])[0][0]]

    def draw(self):
        if self.plot:
            self.plot.remove()
        if self.points:
            self.points.remove()
        theta = np.linspace(0, 2 * np.pi, 100)
        x = self.a * np.cos(theta)
        y = self.b * np.sin(theta)
        ellipse_points = self.R @ np.array([x, y])
        self.plot = self.ax.plot(ellipse_points[0, :] + self.center[0],
                                 ellipse_points[1, :] + self.center[1],
                                 c="blue", lw=1)[0]

    def get_perimeter(self, num_points=36):
        """
        calculate coordinates of points at perimeter of ellipse
        :param num_points: number of pints (the less, the more angular)
        :return: [[x of points], [y of points]]
        """
        theta = np.pi / 2 - np.linspace(0, 2 * np.pi, num_points + 1)[:-1] - self.angle
        x = self.a * np.cos(theta)
        y = self.b * np.sin(theta)
        ellipse_points = self.R @ np.array([x, y])
        ellipse_points[0, :] += self.center[0]
        ellipse_points[1, :] += self.center[1]
        return ellipse_points

    def inellipse(self, size_x, size_y):
        """
        calculate mask for our grid (which have size_x, size_y)
        we assume that the ellipse is given in grid units
        :param size_x: number of x points in mesh
        :param size_y: number of y points in mesh
        :return: mask (1 - if the point belongs to the ellipse, 0 - otherwise)
        """
        res = np.zeros((size_x, size_y))

        res[max(0, round(self.center[0] - self.a)): min(round(self.center[0] + self.a), size_x),
        max(0, round(self.center[1] - self.a)): min(round(self.center[1] + self.a), size_y)] = 1

        for x in range(max(0, round(self.center[0] - self.a)), min(round(self.center[0] + self.a), size_x)):
            for y in range(max(0, round(self.center[1] - self.a)), min(round(self.center[1] + self.a), size_y)):
                point = self.R.T @ np.array([x - self.center[0], y - self.center[1]])
                if (point[0] / self.a) ** 2 + (point[1] / self.b) ** 2 > 1:
                    res[x, y] = 0
        return res.astype("bool")

    def interpol_data(self, data, n_rho, n_phi):
        """
        interpolate data on specific grid in the ellipse
        :param data: data for interpolation on regular (!) grid
        :param n_rho: number of points at distance axis
        :param n_phi: number of points at azimuth axis
        :return: interpolated data in array with sizes (n_phi, n_rho)
        """
        res = np.zeros((n_phi, n_rho))
        points = self.get_perimeter(n_phi)

        # change mathematical center or center_point

        # center_x, center_y = self.center[0], self.center[1]
        center_x, center_y = self.x0, self.y0

        ranges = [[np.linspace(center_x, points[0][i], n_rho), np.linspace(center_y, points[1][i], n_rho)]
                  for i in range(n_phi)]

        # for r, rang in enumerate(ranges):
        #     if r == 0:
        #         self.ax.plot(rang[0], rang[1], c="k")
        #     elif r == 1:
        #         self.ax.plot(rang[0], rang[1], c="g")
        #     else:
        #         self.ax.plot(rang[0], rang[1], c="r")

        if np.count_nonzero(np.isnan(data)) > 0:
            mask = ~np.isnan(data)
            X, Y = np.meshgrid(np.arange(data.shape[0]), np.arange(data.shape[1]), indexing='ij')
            points = np.column_stack((X[mask], Y[mask]))
            for r, rang in enumerate(ranges):
                res[r, :] = griddata(points, data[mask], np.column_stack((rang[1], rang[0])), method="linear")
        else:
            data[np.isnan(data)] = 0
            interp = RectBivariateSpline(np.arange(data.shape[0]), np.arange(data.shape[1]), data)
            for r, rang in enumerate(ranges):
                res[r, :] = interp(rang[1], rang[0], grid=False)
        return res

    def clean(self):
        try:
            if self.plot:
                self.plot.remove()
            if self.points:
                self.points.remove()
        except:
            pass


class Track:
    def __init__(self, index, ax):
        self.index = index
        self.ellps = []
        self.ax = ax
        self.plot = None

    def append(self, point):
        self.ellps.append(point)

    def print(self):
        for p in self.ellps:
            print(p.x, p.y)

    def draw(self, flag=True):
        if self.plot:
            self.plot.remove()
            self.plot = None
        self.plot = self.ax.plot([p.x0 for p in self.ellps], [p.y0 for p in self.ellps], c="k", lw=1)[0]

        for p in self.ellps[:-1]:
            try:
                if p.plot and p.plot in self.ax.lines:
                    p.plot.remove()
                if p.points and p.points in self.ax.collections:
                    p.points.remove()
            except ValueError:
                pass
        if flag:
            self.ellps[-1].draw()

    def save(self):
        filename = f"{TRACKS_FOLDER}/{self.index:09d}.csv"

        ptt_ind = []
        pit_ind = []
        pxc_ind = []
        pyc_ind = []
        px1_ind = []
        py1_ind = []
        px2_ind = []
        py2_ind = []
        px3_ind = []
        py3_ind = []

        with xr.open_dataset(FILE_RORTEX) as ds:
            times = ds['Time']

        for po in self.ellps:

            ptt_ind.append(times[po.t].values)
            pit_ind.append(po.t)
            pxc_ind.append(po.x0)
            pyc_ind.append(po.y0)
            px1_ind.append(po.p1[0])
            py1_ind.append(po.p1[1])
            px2_ind.append(po.p2[0])
            py2_ind.append(po.p2[1])
            px3_ind.append(po.p3[0])
            py3_ind.append(po.p3[1])

            try:
                if po.plot and po.plot in self.ax.lines:
                    po.plot.remove()
            except:
                pass

        track_data = {'time': ptt_ind, 'time_ind': pit_ind,
                      'pxc_ind': pxc_ind, 'pyc_ind': pyc_ind,
                      'px1_ind': px1_ind, 'py1_ind': py1_ind,
                      'px2_ind': px2_ind, 'py2_ind': py2_ind,
                      'px3_ind': px3_ind, 'py3_ind': py3_ind}
        df = pd.DataFrame(track_data)
        df.to_csv(filename)

        try:
            if self.plot and self.plot in self.ax.lines:
                self.plot.remove()
            for p in self.ellps:
                if p and p in self.ax.collections:
                    p.remove()
        except:
            pass


def remove_collections(collection):
    if collection:
        for coll in collection.collections:
            coll.remove()


def remove_streamline(streamlines):
    if streamlines:
        streamlines.lines.remove()
