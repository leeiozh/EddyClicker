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

    def save(self, lat_int, lon_int, time_arr):
        with open(f"{TRACKS_FOLDER}/{self.index}.csv", 'w') as f:
            for po in self.points:
                f.write(f"{time_arr[po.t]:.0f};{lat_int(po.x, po.y)[0][0]};{lon_int(po.x, po.y)[0][0]};{po.x};{po.y}\n")
        self.plot.remove()
