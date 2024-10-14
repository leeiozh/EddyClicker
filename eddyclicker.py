import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.interpolate import RectBivariateSpline
import datetime as dt
from glob import glob
from track import *


class MapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EddyClicker")
        self.path_file_back = FILE_BACK
        self.path_file_edd = FILE_EDD
        self.path_save_file = TRACKS_FOLDER

        toolbar_frame = tk.Frame(self)
        toolbar_frame.pack(side=tk.TOP)

        btn_open_back = tk.Button(toolbar_frame, text="Open criteria file", command=self.select_file_back)
        btn_open_back.pack(side=tk.LEFT, padx=5, pady=5)

        btn_open_cyc = tk.Button(toolbar_frame, text="Open centers file", command=self.select_file_edd)
        btn_open_cyc.pack(side=tk.LEFT, padx=5, pady=5)

        btn_open_save_folder = tk.Button(toolbar_frame, text="Open save folder", command=self.select_save_folder)
        btn_open_save_folder.pack(side=tk.LEFT, padx=5, pady=5)

        self.file_back = Dataset(self.path_file_back)
        ds = Dataset(self.path_file_edd)
        self.centers = ds["center"][:, 0, :, :]
        ds.close()

        self.shot = 0  # current index of shot
        self.R_2d = None  # current criteria data
        self.geo = None  # current geopotential data
        self.curr_centers = None  # current position of centers
        self.prev_centers = None  # previous position of centers
        self.curr_line = None
        self.prev_point = None

        self.tracks = []  # array of tracks

        self.lat_int = RectBivariateSpline(np.arange(self.file_back["XLAT"].shape[1]),
                                           np.arange(self.file_back["XLAT"].shape[2]),
                                           self.file_back["XLAT"][0, :, :])
        self.lon_int = RectBivariateSpline(np.arange(self.file_back["XLONG"].shape[1]),
                                           np.arange(self.file_back["XLONG"].shape[2]),
                                           self.file_back["XLONG"][0, :, :])

        self.mesh_lon, self.mesh_lat = np.meshgrid(np.arange(self.file_back["XLAT"].shape[1]),
                                                   np.arange(self.file_back["XLAT"].shape[2]))

        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.bind("<Down>", self.go_back)
        self.bind("<Up>", self.go_forward)
        self.bind("<Escape>", self.release_track)
        self.focus_set()

        toolbar_frame = tk.Frame(self)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.create_map()

    def create_map(self):
        if self.R_2d:
            for coll in self.R_2d.collections:
                coll.remove()
            for coll in self.geo.collections:
                coll.remove()
        if self.curr_centers:
            if self.prev_centers:
                self.prev_centers.remove()
            self.prev_centers = self.curr_centers.get_offsets()
            self.prev_centers = self.ax.scatter(self.prev_centers[:, 0], self.prev_centers[:, 1], facecolor="None",
                                                edgecolor="k", zorder=5, s=20)
            self.curr_centers.remove()

        self.ax.contourf(self.mesh_lon, self.mesh_lat, LAND, colors="LightGrey")

        R_2d = self.file_back["R_2d"][self.shot, 0, :, :]
        R_2d = np.where(R_2d < 0, np.nan, R_2d)
        self.R_2d = self.ax.contourf(self.mesh_lon, self.mesh_lat, R_2d, levels=10, cmap="gnuplot_r", alpha=0.8)

        self.geo = self.ax.contour(self.mesh_lon, self.mesh_lat, self.file_back["geopotential"][self.shot, 0, :, :],
                                   levels=50, colors="k", linewidths=0.2)

        mask = self.centers[self.shot, :, :] > 0
        self.curr_centers = self.ax.scatter(self.mesh_lon[mask], self.mesh_lat[mask], c="k", s=40, zorder=6)

        self.ax.set_title((dt.datetime(year=1979, month=1, day=1) + dt.timedelta(
            minutes=int(self.file_back["XTIME"][self.shot]))).strftime("%d.%m.%Y %H:%M"))
        self.ax.format_coord = self.custom_format_coord
        self.canvas.draw()

    def go_back(self, event=None):
        if self.shot > 0:
            self.shot -= 1
        self.create_map()

    def go_forward(self, event=None):
        if self.shot < len(self.file_back["XTIME"][:]) - 1:
            self.shot += 1
        self.create_map()

    def release_track(self, event=None):
        if self.prev_point:
            self.prev_point = None
        if self.curr_line:
            self.curr_line.remove()
            self.curr_line = None
        self.canvas.draw()

    def custom_format_coord(self, x, y):
        return f"x = {x:.0f}, y = {y:.0f}; Lat = {self.lat_int(x, y)[0, 0]:.2f}°, Lon = {self.lon_int(x, y)[0, 0]:.2f}°"

    def select_file_back(self):
        file_path = filedialog.askopenfilename(title="Select criteria file", filetypes=[("NetCDF files", "*.nc")])
        if file_path:
            self.path_file_back = file_path
            self.file_back = Dataset(self.path_file_back)

    def select_file_edd(self):
        file_path = filedialog.askopenfilename(title="Select centers file", filetypes=[("NetCDF files", "*.nc")])
        if file_path:
            self.path_file_edd = file_path
            ds = Dataset(self.path_file_edd)
            self.centers = ds["center"][:, 0, :, :]
            ds.close()

    def select_save_folder(self):
        folder_path = filedialog.askdirectory(title="Select save folder")
        if folder_path:
            self.path_save_file = folder_path
            self.load_tracks(folder_path)

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        if event.button == 1:

            if not self.prev_point:
                cent_f, cent = self.is_center(event.xdata, event.ydata, -1)  # coordinates of center around 2 px
                if cent_f:
                    self.prev_point = cent

            else:
                cent_f, cent = self.is_center(event.xdata, event.ydata, 0)  # coordinates of center around 2 px
                if cent_f:
                    cent_track = self.in_track(self.prev_point)  # index of track with previous point
                    if cent_track == -1:
                        print(f"New track created {len(self.tracks)}.")
                        new_track = Track(len(self.tracks), self.ax)
                        new_track.append(self.prev_point)
                        new_track.append(cent)
                        self.tracks.append(new_track)
                        self.prev_point = None
                    else:
                        print(f"Point added to track {cent_track}.")
                        self.tracks[cent_track].append(cent)
                        self.prev_point = None
                        if self.curr_line:
                            self.curr_line.remove()
                            self.curr_line = None
                    self.tracks[cent_track].draw()
        elif event.button == 3 and self.prev_point is None:
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                self.ask_to_save_track(cent_track)
        self.canvas.draw()

    def on_mouse_move(self, event):
        if self.prev_point and event.inaxes == self.ax:
            if self.curr_line:
                self.curr_line.remove()
            self.curr_line = \
                self.ax.plot([self.prev_point.x, event.xdata], [self.prev_point.y, event.ydata], c="k", lw=1)[0]
            self.canvas.draw()

    def is_center(self, x, y, c=0):
        mask = self.centers[self.shot + c, :, :] > 0
        centers = np.column_stack((self.mesh_lon[mask], self.mesh_lat[mask]))
        for center in centers:
            if np.isclose([x, y], center, atol=2).all():
                return True, Point(center[0], center[1], self.shot + c)
        return False, Point(-1, -1, -1)

    def in_track(self, point):
        for track in self.tracks:
            if track.points[-1].x == point.x and track.points[-1].y == point.y:
                return track.index
        return -1

    def ask_to_save_track(self, index):
        response = messagebox.askyesno("Save Track", "Do you want to save this track?")
        if response:
            for p in self.tracks[index].points:
                self.centers[p.t, p.x, p.y] = 0

            self.tracks[index].save(self.lat_int, self.lon_int, self.file_back["XTIME"][:])
            messagebox.showinfo("Saving", f"Track was added into {self.path_save_file}{index}.csv")
            print(f"Track {index} was saved.")

    def load_tracks(self, path):
        files = sorted(glob(path + "/*.csv"))
        for f in files:
            df = np.loadtxt(f, delimiter=";")
            points = [Point(d[3], d[4], d[0]) for d in df]
            new_track = Track(f.split("/")[-1][:-4], self.ax)
            new_track.points = points
            self.tracks.append(new_track)
            self.tracks[-1].draw()
        self.canvas.draw()


if __name__ == "__main__":
    app = MapApp()
    app.mainloop()
