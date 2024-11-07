import numpy as np
from const import *


class Point:
    def __init__(self, t, x, y):
        self.t = t
        self.x = x
        self.y = y


class Ellipse:
    def __init__(self, t, x0, y0, p1, p2, p3, ax):
        self.t = t
        self.x0 = x0
        self.y0 = y0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.center = (self.p1 + self.p2) / 2
        self.a = np.linalg.norm(self.p1 - self.p2) / 2
        self.b, self.angle = self.calculate_minor_axis_and_angle()
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
        theta = np.linspace(0, 2 * np.pi, 100)
        x = self.a * np.cos(theta)
        y = self.b * np.sin(theta)
        R = np.array([[np.cos(self.angle), -np.sin(self.angle)],
                      [np.sin(self.angle), np.cos(self.angle)]])
        ellipse_points = R @ np.array([x, y])

        # self.points = self.ax.scatter([self.p1[0], self.p2[0], self.p3[0]],
        #                               [self.p1[1], self.p2[1], self.p3[1]],
        #                               color="blue")
        self.plot = self.ax.plot(ellipse_points[0, :] + self.center[0],
                                 ellipse_points[1, :] + self.center[1],
                                 c="blue", lw=1)[0]


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
        self.plot = self.ax.plot([p.x0 for p in self.points], [p.y0 for p in self.points], c="k", lw=1)[0]

        for p in self.points:
            p.draw()

    def save(self, lat_int, lon_int, time_arr):
        with open(f"{TRACKS_FOLDER}/{self.index:09d}.csv", 'w') as f:
            for po in self.points:
                # el_points = po.convert2ll(lat_int, lon_int)
                el_points = [po.x0, po.y0, po.p1[0], po.p1[1], po.p2[0], po.p2[1], po.p3[0], po.p3[1]]

                f.write(f"{time_arr[po.t]:.0f};{po.t};")
                for el in el_points[:-1]:
                    f.write(f"{el};")
                f.write(f"{el_points[-1]}\n")
                po.plot.remove()
            self.plot.remove()
