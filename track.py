from tkinter import messagebox
from const import *


class Point:
    def __init__(self, x, y, t):
        self.t = t
        self.x = x
        self.y = y

    def convert2ll(self, lat_int, lon_int):
        return lat_int(self.x, self.y), lon_int(self.x, self.y)


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
        self.plot = self.ax.plot([p.x for p in self.points], [p.y for p in self.points], c="k", lw=1)[0]

    def save(self, filename, lat_int, lon_int, time_arr):
        with open(TRACKS_FOLDER + f"{filename}", 'a') as f:
            f.write(f"{self.index};time;")
            for point in self.points:
                f.write(f"{time_arr[point.t]:.0f};")
            f.write("\n")
            f.write(f"{self.index};lat;")
            for point in self.points:
                f.write(f"{lat_int(point.x, point.y)[0][0]};")
            f.write("\n")
            f.write(f"{self.index};lon;")
            for point in self.points:
                f.write(f"{lon_int(point.x, point.y)[0][0]};")
            f.write("\n")
        self.plot.remove()
