# kill -9 $(ps ax | grep eddy | cut -f1 -d' ' | head -1)

import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib
import numpy as np

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy.interpolate import RectBivariateSpline
import datetime as dt
from glob import glob
from shutil import move
from os.path import isfile, isdir
from os import mkdir
from track import *
from const import *


class MapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EddyClicker")
        # self.path_file_scalar = FILE_SCALAR
        self.path_file_rortex = FILE_RORTEX
        self.path_save_file = TRACKS_FOLDER

        # if not isfile(FILE_SCALAR):
        #     self.select_file_scalar()

        if not isfile(FILE_RORTEX):
            self.select_file_rortex()

        if not isdir(TRACKS_FOLDER):
            mkdir(TRACKS_FOLDER)

        toolbar_frame = tk.Frame(self)
        toolbar_frame.pack(side=tk.TOP)

        # btn_open_back = tk.Button(toolbar_frame, text="Open criteria file", command=self.select_file_scalar)
        # btn_open_back.pack(side=tk.LEFT, padx=5, pady=5)

        # btn_open_cyc = tk.Button(toolbar_frame, text="Open input file", command=self.select_file_rortex)
        # btn_open_cyc.pack(side=tk.LEFT, padx=5, pady=5)

        # btn_open_save_folder = tk.Button(toolbar_frame, text="Open save folder", command=self.select_save_folder)
        # btn_open_save_folder.pack(side=tk.LEFT, padx=5, pady=5)

        self.file_rortex = Dataset(self.path_file_rortex)
        # ds = Dataset(self.path_file_rortex)
        self.centers = self.file_rortex[LOCAL_EXTR_VARNAME][:, :, :]
        # ds.close()

        self.shot = 0  # current index of shot
        self.RORTEX = None  # current criteria data
        self.geo = None  # current geopotential data
        self.geo_fine = None  # current geopotential data (for zoom)
        self.curr_centers = None  # current position of centers
        self.prev_centers = None  # previous position of centers
        self.curr_line = None
        self.prev_point = None
        self.curr_point = None
        self.el_p1 = None
        self.el_p2 = None
        self.el_p3 = None
        self.prev_el = None
        self.curr_el = None
        self.sel_el = False
        self.k = 1
        self.tracks = []

        if len(self.file_rortex["XLAT"].shape) == 3:
            ydim = self.file_rortex["XLAT"].shape[1]
            xdim = self.file_rortex["XLAT"].shape[2]
        elif len(self.file_rortex["XLAT"].shape) == 2:
            ydim = self.file_rortex["XLAT"].shape[0]
            xdim = self.file_rortex["XLAT"].shape[1]
        else:
            exit("STOP! Wrong XLAT/XLONG dimentions")

        self.lat_int = RectBivariateSpline(np.arange(ydim),
                                           np.arange(xdim),
                                           self.file_rortex["XLAT"][:, :])
        self.lon_int = RectBivariateSpline(np.arange(ydim),
                                           np.arange(xdim),
                                           self.file_rortex["XLONG"][:, :])

        self.mesh_lon, self.mesh_lat = np.meshgrid(np.arange(ydim),
                                                   np.arange(xdim))

        self.fig, self.ax = plt.subplots(figsize=(13, 13))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("button_press_event", self.on_double_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("scroll_event", self.on_mouse_wheel)
        self.bind("<Down>", self.go_back)
        self.bind("<Up>", self.go_forward)
        self.bind("<Escape>", self.release_track)
        self.focus_set()
        toolbar_frame = tk.Frame(self)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        if self.path_save_file:
            self.load_tracks(self.path_save_file)
        self.create_map()

    def create_map(self):
        if self.RORTEX:
            for coll in self.RORTEX.collections:
                coll.remove()
        if self.geo:
            for coll in self.geo.collections:
                coll.remove()
        if self.geo_fine:
            for coll in self.geo_fine.collections:
                coll.remove()
        if self.curr_centers:
            if self.prev_centers:
                self.prev_centers.remove()
            self.prev_centers = self.curr_centers.get_offsets()
            self.prev_centers = self.ax.scatter(self.prev_centers[:, 0], self.prev_centers[:, 1], facecolor="None",
                                                edgecolor="k", zorder=5, s=20)
            self.curr_centers.remove()

        self.ax.contourf(self.mesh_lon, self.mesh_lat, LAND, colors="LightGrey")

        RORTEX = self.file_rortex[RORTEX_VARNAME][self.shot, :, :]
        RORTEX = np.where(RORTEX <= 0, np.nan, RORTEX)

        self.RORTEX = self.ax.contourf(self.mesh_lon, self.mesh_lat, RORTEX, levels=10, cmap="gnuplot_r", alpha=0.8)

        self.geo_fine = self.ax.contour(self.mesh_lon, self.mesh_lat, self.file_rortex[SCALAR_VARNAME][self.shot, :, :],
                                   levels=SCALAR_LEVELS_FINE, colors="k", alpha=0.8, linestyles=":", linewidths=0.1)
        self.geo = self.ax.contour(self.mesh_lon, self.mesh_lat, self.file_rortex[SCALAR_VARNAME][self.shot, :, :],
                                   levels=SCALAR_LEVELS, colors="k", linewidths=0.2)

        mask = self.centers[self.shot, :, :] > 0
        self.curr_centers = self.ax.scatter(self.mesh_lon[mask], self.mesh_lat[mask], c="k", zorder=6, s=40)

        self.ax.set_title((dt.datetime(year=1979, month=1, day=1) + dt.timedelta(
            minutes=int(self.file_rortex["XTIME"][self.shot]))).strftime("%d.%m.%Y %H:%M"))
        self.ax.format_coord = self.custom_format_coord
        self.canvas.draw()

    def go_back(self, event=None):
        if self.shot > 0:
            self.shot -= 1
        self.create_map()

    def go_forward(self, event=None):
        if self.shot < len(self.file_rortex["XTIME"][:]) - 1:
            self.shot += 1
        self.create_map()

    def release_track(self, event=None):
        if self.prev_point:
            self.prev_point = None
        if self.curr_line:
            self.curr_line.remove()
            self.curr_line = None
        if self.curr_el:
            if self.curr_el.plot:
                self.curr_el.plot.remove()
                self.curr_el = None
        self.canvas.draw()

    def custom_format_coord(self, x, y):
        return f"x = {x:.0f}, y = {y:.0f}; Lat = {self.lat_int(x, y)[0, 0]:.2f}°, Lon = {self.lon_int(x, y)[0, 0]:.2f}°"

    def change_path(self, file_path, name):
        with open("const.py", "r") as fin:
            with open("tmp.py", "w") as fout:
                for line in fin.readlines():
                    if name in line:
                        line = line.replace(line.split(" = ")[-1], f"'{file_path}'\n")
                    fout.write(line)
        move("tmp.py", "const.py")

    # def select_file_scalar(self):
    #     file_path = filedialog.askopenfilename(initialdir="/".join(FILE_SCALAR.split("/")[:-1]),
    #                                            title="Select criteria file", filetypes=[("NetCDF files", "*.nc")])
    #     if file_path:
    #         self.path_file_scalar = file_path
    #         self.file_scalar = Dataset(self.path_file_scalar)
    #         self.create_map()
    #         self.change_path(file_path, "FILE_SCALAR")

    def select_file_rortex(self):
        file_path = filedialog.askopenfilename(initialdir="/".join(FILE_RORTEX.split("/")[:-1]),
                                               title="Select centers file", filetypes=[("NetCDF files", "*.nc")])
        if file_path:
            self.path_file_rortex = file_path
            ds = Dataset(self.path_file_rortex)
            self.centers = ds["center"][:, :, :]
            ds.close()
            self.create_map()
            self.change_path(file_path, "FILE_RORTEX")

    def select_save_folder(self):
        folder_path = filedialog.askdirectory(initialdir="/".join(TRACKS_FOLDER.split("/")[:-1]),
                                              title="Select save folder")
        if folder_path:
            self.path_save_file = folder_path
            self.change_path(folder_path, "TRACKS_FOLDER")

    def on_click(self, event):
        if event.inaxes != self.ax or event.dblclick:
            return

        if event.button == 1:
            if not self.prev_point:  # no first point
                cent_f, cent = self.is_center(event.xdata, event.ydata, -1)  # coordinates of center around 2 px
                if cent_f:
                    self.prev_point = cent
                    print("first point selected")
                # cent_track = self.in_track(self.prev_point)
                # if cent_track == -1:
                #     self.sel_el = True  # start of new track

            else:  # have first point
                if not self.curr_point:
                    cent_f, cent = self.is_center(event.xdata, event.ydata, 0)  # coordinates of center around 2 px
                    if cent_f:
                        self.curr_point = cent
                        self.sel_el = True
                        print("second point selected")

                else:  # have two points
                    cent_track = self.in_track(self.prev_point)

                    if self.el_p1 is None:
                        self.el_p1 = np.array([event.xdata, event.ydata])
                    elif self.el_p2 is None:
                        self.el_p2 = np.array([event.xdata, event.ydata])
                    elif self.el_p3 is None:
                        self.el_p3 = np.array([event.xdata, event.ydata])
                        # else:
                        ell = Ellipse(self.curr_point.t, self.curr_point.x, self.curr_point.y,
                                      self.el_p1, self.el_p2, self.el_p3, self.ax)

                        if cent_track == -1:
                            print(f"created {len(self.tracks)} track")
                            new_track = Track(len(self.tracks), self.ax)
                            new_track.points.append(Ellipse(self.prev_point.t, self.prev_point.x, self.prev_point.y,
                                                            np.array([self.prev_point.x, self.prev_point.y]),
                                                            np.array([self.prev_point.x, self.prev_point.y]),
                                                            np.array([self.prev_point.x, self.prev_point.y]),
                                                            self.ax))
                            new_track.points.append(ell)
                            self.tracks.append(new_track)
                            self.tracks[-1].draw()
                        else:
                            print(f"appended {len(self.tracks[cent_track].points)} point to {cent_track} track")
                            self.tracks[cent_track].append(ell)
                            self.tracks[-1].draw()

                        self.prev_point = None
                        self.curr_point = None
                        self.el_p1 = None
                        self.el_p2 = None
                        self.el_p3 = None

        elif event.button == 3 and self.prev_point is None:
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                self.ask_to_save_track(cent_track)
        self.canvas.draw()

    def on_double_click(self, event):
        if event.dblclick:
            if event.inaxes != self.ax:
                return
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                if cent_track != -1:
                    point_index = -1
                    for i, p in enumerate(self.tracks[cent_track].points):
                        if p.x0 == cent.x and p.y0 == cent.y:
                            point_index = i
                            break
                    if point_index != -1:
                        self.tracks[cent_track].points.pop(point_index)
                        self.tracks[cent_track].draw()
                        # if self.curr_el:
                        #     if self.curr_el.plot:
                        #         self.curr_el.plot.remove()
                        #         self.curr_el = None
                        self.canvas.draw()

    def on_mouse_move(self, event):

        # if self.prev_point and self.curr_point and event.inaxes == self.ax:
        #     # if self.curr_el:
        #     #     if self.curr_el.plot:
        #     #         self.curr_el.plot.remove()
        #     #         self.curr_el = None
        #     # self.curr_el = Ellipse(self.curr_point.t, self.curr_point.x, self.curr_point.y,
        #     #                        event.xdata, event.ydata, self.k, self.ax)
        #     # self.curr_el.draw()
        #     if self.curr_line:
        #         self.curr_line.remove()
        #     self.curr_line = \
        #         self.ax.plot([self.curr_point.x, event.xdata], [self.curr_point.y, event.ydata], c="k", lw=1)[0]

        if self.prev_point and self.curr_point is None and event.inaxes == self.ax:
            if self.curr_line:
                self.curr_line.remove()
            self.curr_line = \
                self.ax.plot([self.prev_point.x, event.xdata], [self.prev_point.y, event.ydata], c="k", lw=1)[0]
        self.canvas.draw_idle()

    def on_mouse_wheel(self, event):
        if self.prev_point and self.curr_point and self.curr_el:
            if event.button == "up" and self.k < 1. - 1e-2:
                self.k += 5e-2
            elif event.button == "down" and self.k > 1e-2:
                self.k -= 5e-2
            self.curr_el.draw()
            self.canvas.draw_idle()

    def is_center(self, x, y, c=0):
        mask = self.centers[self.shot + c, :, :] > 0
        centers = np.column_stack((self.mesh_lon[mask], self.mesh_lat[mask]))
        for center in centers:
            if np.isclose([x, y], center, atol=2).all():
                return True, Point(self.shot + c, center[0], center[1])
        return False, Point(-1, -1, -1)

    def in_track(self, point):
        for track in self.tracks:
            if track.points[-1].x0 == point.x and track.points[-1].y0 == point.y:
                return track.index
        return -1

    def ask_to_save_track(self, index):
        response = messagebox.askyesno("Save Track", "Do you want to save this track?")
        if response:
            for p in self.tracks[index].points:
                self.centers[p.t, p.x0, p.y0] = 0

            self.tracks[index].save(self.lat_int, self.lon_int, self.file_rortex["XTIME"][:])
            messagebox.showinfo("Saving", f"Track was added into {self.path_save_file}/{index:09d}.csv")
            self.curr_point = None
            self.prev_point = None

            if self.curr_line:
                self.curr_line.remove()
                self.curr_line = None
            if self.curr_el:
                if self.curr_el.plot:
                    self.curr_el.plot.remove()
                if self.curr_el.points:
                    self.curr_el.points.remove()
                self.curr_el = None

            print(f"Track {index} was saved.")

    def load_tracks(self, path):
        files = sorted(glob(path + "/*.csv"))
        for f in files:
            df = np.loadtxt(f, delimiter=";")
            ind = df[:, 1:4].astype("int")
            self.centers[ind[:, 0], ind[:, 1], ind[:, 2]] = np.nan

            # print(self.centers[0])
            # mask = np.isin(self.centers, df[:, 1:4])
            # print(self.centers[mask])
            # self.centers[mask] = np.nan
            # ells = [Ellipse(d[0], d[1], d[2], np.array([d[3], d[4]]), np.array([d[5], d[6]]), np.array([d[7], d[8]]),
            #                self.ax) for d in df]
            # new_track = Track(f.split("/")[-1][:-4], self.ax)
            # new_track.points = ells
            # self.tracks.append(new_track)
            # self.tracks[-1].draw()
        self.canvas.draw()


if __name__ == "__main__":
    app = MapApp()
    app.mainloop()
