import numpy as np
from const import *


class Point:
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y


class Ellipse:
    def __init__(self, t, x, y, x_a, y_a, k, ax):
        self.t = t
        self.x = x
        self.y = y
        self.x_a = x_a
        self.y_a = y_a
        self.k = k

        self.ax = ax
        self.plot = None

    def convert2ll(self, lat_int, lon_int):
        return lat_int(self.x, self.y)[0][0], lon_int(self.x, self.y)[0][0], \
            lat_int(self.x_a, self.y_a)[0][0], lon_int(self.x_a, self.y_a)[0][0]

    def draw(self):
        if self.plot:
            self.plot.remove()
        vec_x = self.x_a - self.x
        vec_y = self.y_a - self.y
        a = np.linalg.norm([vec_x, vec_y])
        phi = np.arctan2(vec_y, vec_x)
        x = a * np.cos(PHI)
        y = a * self.k * np.sin(PHI)
        res = np.dot(np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]]), np.array([x, y]))
        self.plot = self.ax.plot(self.x + res[0], self.y + res[1], c="tab:green", lw=1)[0]


class Track:
    def __init__(self, index, ax):
        self.index = index
        self.points = []
        self.ax = ax
        self.plot = None

    def append(self, point):
        self.points.append(point)

    def print(self):
        for p in self.points:
            print(p.x, p.y)

    def draw(self):
        if self.plot:
            self.plot.remove()
        self.plot = self.ax.plot([p.x for p in self.points], [p.y for p in self.points], c="tab:blue", lw=1)[0]

        for p in self.points:
            p.draw()

    def save(self, lat_int, lon_int, time_arr):
        with open(f"{TRACKS_FOLDER}/{self.index:09d}.csv", 'w') as f:
            for po in self.points:
                lat_cent, lon_cent, lat_a, lon_a = po.convert2ll(lat_int, lon_int)
                az, _, a = geod.inv(lat_cent, lon_cent, lat_a, lon_a)
                a /= 1000  # in km
                b = a * po.k

                f.write(f"{time_arr[po.t]:.0f};{lat_cent};{lon_cent};{a};{b};{az};"
                        f"{po.x};{po.y};{po.x_a};{po.y_a};{po.k}\n")
                po.plot.remove()
            self.plot.remove()
