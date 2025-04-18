import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as patches
import datetime as dt
from glob import glob
from shutil import move
from os.path import isfile, isdir
from os import mkdir
from track import *
from const import *

# import datetime

# kill -9 $(ps ax | grep eddy | cut -f1 -d' ' | head -1)

cent_track = 0
nscalar = 0


# а в этом был сакральный смысл?
# SCALAR1_VARNAME = SCALARS['scalar1']['name']
# SCALAR2_VARNAME = SCALARS['scalar2']['name']
# SCALAR3_VARNAME = SCALARS['scalar3']['name']
# SCALAR1_LEVELS_STEP = SCALARS['scalar1']['step']
# SCALAR2_LEVELS_STEP = SCALARS['scalar2']['step']
# SCALAR2_CMAP = SCALARS['scalar2']['cmap']


def show_instructions():
    instructions = (
        "Welcome to EddyClicker!\n\n"
        "Instruction:\n"
        "↑ - move to next stamp\n"
        "↓ - move to prev stamp\n"
        "LMC - select the point\n"
        "Esc - release the point\n"
        "RMC - save the track\n"
        "2xLMC - pop the point\n\n"
        "Enjoy it!"
    )
    messagebox.showinfo("Instruction", instructions)


class MapApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EddyClicker")

        x_offset = 0
        y_offset = 0
        self.geometry(f"{WINDOW_WIDTH}x{SCREEN_HEIGHT}+{x_offset}+{y_offset}")
        self.resizable(True, True)
        # self.geometry("1000x1000")

        # if first_time:
        #     show_instructions()

        # Create main container
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create toolbar frame
        toolbar_frame = tk.Frame(container)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        self.time_entry = tk.Entry(container)
        self.time_entry.insert(0, "YYYY-MM-DD-HH")
        self.time_entry.pack(side=tk.TOP)
        self.time_entry.bind("<Return>", self.update_time)

        # Create figure frame
        figure_frame = tk.Frame(container)
        figure_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.path_file_rortex = FILE_RORTEX
        self.path_save_file = TRACKS_FOLDER

        if not isfile(FILE_RORTEX):
            self.select_file_rortex()

        if not isdir(TRACKS_FOLDER):
            mkdir(TRACKS_FOLDER)

        self.file_rortex = Dataset(self.path_file_rortex)
        self.centers = np.asarray(self.file_rortex[LOCAL_EXTR_VARNAME][:, LEVEL, :, :], dtype=float)

        self.shot = 0
        self.land = None
        self.rortex = None
        self.scalar = 0
        self.cbar = None
        self.field = 0
        self.curr_centers = None
        self.prev_centers = None
        self.curr_line = None
        self.prev_point = None
        self.curr_point = None
        self.el_p1 = None
        self.el_p2 = None
        self.el_p3 = None
        self.sel_el = False
        self.k = 1
        self.tracks = []

        if len(self.file_rortex["XLAT"].shape) == 3:  # РУДИМЕНТ (по идее можно удалить)
            ydim = self.file_rortex["XLAT"].shape[1]  # РУДИМЕНТ (по идее можно удалить)
            xdim = self.file_rortex["XLAT"].shape[2]  # РУДИМЕНТ (по идее можно удалить)
        elif len(self.file_rortex["XLAT"].shape) == 2:
            xdim = self.file_rortex["XLAT"].shape[1]
            ydim = self.file_rortex["XLAT"].shape[0]
        else:
            exit("MapApp: STOP! Wrong XLAT/XLONG dimentions")

        self.lat_int = RectBivariateSpline(np.arange(xdim), np.arange(ydim), self.file_rortex["XLAT"][:, :].T)
        self.lon_int = RectBivariateSpline(np.arange(xdim), np.arange(ydim), self.file_rortex["XLONG"][:, :].T)
        self.mesh_lon, self.mesh_lat = np.meshgrid(np.arange(xdim), np.arange(ydim), indexing="ij")

        # Create figure and canvas
        ratio = float(SCREEN_HEIGHT) / float(WINDOW_WIDTH)
        self.fig = Figure(figsize=(8, 8 * ratio), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.format_coord = self.custom_format_coord
        self.land = self.ax.contour(self.mesh_lon, self.mesh_lat, LAND.T, levels=1, zorder=10, colors="k",
                                    linewidths=1)

        self.canvas = FigureCanvasTkAgg(self.fig, master=figure_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Connect events
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self.bind("<Left>", self.go_back)
        self.bind("<Right>", self.go_forward)
        self.bind("<Escape>", self.release_track)
        self.bind("<Control-z>", self.undo_last)
        # self.bind("<space>", )
        self.bind("<q>", self.switch_field)
        self.bind("<w>", self.switch_field)
        self.bind("<e>", self.switch_field)
        self.focus_set()

        if self.path_save_file:
            self.load_tracks(self.path_save_file)
        self.create_map()

    def create_map(self):

        if self.scalar is not None:

            # Rortex
            remove_collections(self.rortex)

            if len(self.file_rortex[RORTEX_VARNAME].shape) == 4:
                rortex = self.file_rortex[RORTEX_VARNAME][self.shot, LEVEL, :, :]
            elif len(self.file_rortex[RORTEX_VARNAME].shape) == 3:
                rortex = self.file_rortex[RORTEX_VARNAME][self.shot, :, :]
            else:
                exit(f"###################\nDimention of {RORTEX_VARNAME} not eq 3 or 4. EXIT!\n##################")

            rortex_data = np.where(rortex <= 0, np.nan, rortex)
            self.rortex = self.ax.contourf(self.mesh_lon, self.mesh_lat, rortex_data.T,
                                           levels=10, zorder=3, cmap="gnuplot_r", alpha=0.8)

            # current centers -> previous centers
            if self.curr_centers:
                if self.prev_centers:
                    self.prev_centers.remove()
                self.prev_centers = self.curr_centers.get_offsets()
                self.prev_centers = self.ax.scatter(self.prev_centers[:, 0], self.prev_centers[:, 1],
                                                    c="k", zorder=5, s=30)
                self.curr_centers.remove()

            # show current centers
            mask = (self.centers[self.shot, :, :] > 0).T
            self.curr_centers = self.ax.scatter(self.mesh_lon[mask], self.mesh_lat[mask], facecolor="None",
                                                edgecolor="k", zorder=6, s=50, lw=1)

            # title
            time_str = f"{(dt.datetime(year=1970, month=1, day=1) + dt.timedelta(hours=int(self.file_rortex['Time'][self.shot]))).strftime('%Y-%m-%d %H:%M')}"
            level_hight_str = f"avg level hight = {LEV_HGT:.1f} km"
            title_str = f"{time_str}, {level_hight_str}"

            self.ax.set_title(title_str, fontsize=20)

        # scalar background
        remove_collections(self.scalar)

        scalar_name = SCALARS[self.field]["name"]

        if len(self.file_rortex[scalar_name].shape) == 4:
            scalar_field = self.file_rortex[scalar_name][self.shot, LEVEL, :, :]
        elif len(self.file_rortex[scalar_name].shape) == 3:
            scalar_field = self.file_rortex[scalar_name][self.shot, :, :]
        else:
            exit(f"######################\nDimention of {scalar_name} not eq 3 or 4. EXIT!\n######################")

        if not SCALARS[self.field]["land"]:
            scalar_field[LAND == 0] = np.nan

        # scalar_field = np.where(LAND != 0, scalar_field, np.nan)
        min_val = np.nanmin(scalar_field)
        max_val = np.nanmax(scalar_field)
        scalar_levels = np.arange(min_val, max_val, SCALARS[self.field]["step"])

        if SCALARS[self.field]["cmap"] != "":
            self.scalar = self.ax.contourf(self.mesh_lon, self.mesh_lat, scalar_field.T, levels=scalar_levels,
                                           extend='both', cmap=SCALARS[self.field]["cmap"], zorder=4)
        else:
            self.scalar = self.ax.contour(self.mesh_lon, self.mesh_lat, scalar_field.T, levels=scalar_levels,
                                          colors="darkolivegreen", linewidths=0.3, zorder=3)

        if self.cbar is not None:
            self.cbar.ax.clear()
            self.cbar.set_ticks([])
        self.cax = self.ax.inset_axes([1.02, 0.0, 0.02, 1])

        if scalar_name == "geopotential":
            self.cbar = self.fig.colorbar(self.rortex, cax=self.cax, label="rortex")
        else:
            self.cbar = self.fig.colorbar(self.scalar, cax=self.cax, label=scalar_name)
        self.canvas.draw()

    def update_time(self, event=None):
        time_str = self.time_entry.get()
        try:
            target_time = (dt.datetime.strptime(time_str, "%Y-%m-%d-%H") -
                           dt.datetime(year=1970, month=1, day=1)).total_seconds() / 3600
            self.shot = int(np.argmin(np.abs(target_time - np.array(self.file_rortex["Time"][:]))))
            self.create_map()

        except ValueError:
            messagebox.showerror("Error", "Wrong time format. Please, use YYYY-MM-DD-HH")

    def go_back(self, event=None):
        if self.shot > 0:
            self.shot -= 1
        self.create_map()

    def go_forward(self, event=None):
        if self.shot < len(self.file_rortex["Time"][:]) - 1:
            self.shot += 1
        self.create_map()

    def release_track(self, event=None):
        if self.prev_point:
            self.prev_point = None
        if self.curr_point:
            self.curr_point = None
        if self.curr_line:
            self.curr_line.remove()
            self.curr_line = None
        if self.el_p1:
            self.el_p1.clean()
            self.el_p1 = None
        if self.el_p2:
            self.el_p2.clean()
            self.el_p2 = None
        if self.el_p3:
            self.el_p3.clean()
            self.el_p3 = None
        self.canvas.draw()

    def undo_last(self, event=None):
        global cent_track
        if len(self.tracks) > cent_track:
            if self.tracks[cent_track] and len(self.tracks[cent_track].ellps) > 0:
                self.tracks[cent_track].ellps[-1].clean()
                self.tracks[cent_track].ellps.pop()
                self.tracks[cent_track].draw(flag=False)
                self.release_track()

    def switch_field(self, event=None):
        remove_collections(self.scalar)
        self.scalar = None

        if event.keysym == "q":
            self.field = 0
        elif event.keysym == "w":
            self.field = 1
        elif event.keysym == "e":
            self.field = 2

        self.create_map()

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
            self.centers = np.asarray(ds["center"][:, LEVEL, :, :], dtype=float)
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
        global cent_track
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
                        self.el_p1 = DrawPoint(event.xdata, event.ydata,
                                               self.ax)  # np.array([event.xdata, event.ydata])
                        self.el_p1.draw()
                    elif self.el_p2 is None:
                        self.el_p2 = DrawPoint(event.xdata, event.ydata,
                                               self.ax)  # np.array([event.xdata, event.ydata])
                        self.el_p2.draw()
                    elif self.el_p3 is None:
                        self.el_p3 = DrawPoint(event.xdata, event.ydata,
                                               self.ax)  # np.array([event.xdata, event.ydata])
                        self.el_p3.draw()

                        ell = Ellipse(self.curr_point.t, self.curr_point.x, self.curr_point.y,
                                      self.el_p1, self.el_p2, self.el_p3, self.ax)

                        if cent_track == -1:
                            print(f"created {len(self.tracks)} track")
                            new_track = Track(len(self.tracks), self.ax)
                            new_track.ellps.append(Ellipse(self.prev_point.t, self.prev_point.x, self.prev_point.y,
                                                           np.array([self.prev_point.x, self.prev_point.y]),
                                                           np.array([self.prev_point.x, self.prev_point.y]),
                                                           np.array([self.prev_point.x, self.prev_point.y]),
                                                           self.ax))
                            new_track.ellps.append(ell)
                            self.tracks.append(new_track)
                            self.tracks[-1].draw()

                        else:
                            print(f"appended {len(self.tracks[cent_track].ellps)} point to {cent_track} track")
                            self.tracks[cent_track].append(ell)
                            self.tracks[-1].draw()

                        self.prev_point = None
                        self.curr_point = None
                        self.el_p1.clean()
                        self.el_p2.clean()
                        self.el_p3.clean()
                        self.el_p1 = None
                        self.el_p2 = None
                        self.el_p3 = None

        elif event.button == 3 and self.prev_point is None:
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                self.ask_to_save_track(cent_track)

        elif event.dblclick and event.inaxes == self.ax:
            cent_f, cent = self.is_center(event.xdata, event.ydata, -1)
            if cent_f:
                cent_track = self.in_track(cent)
                if cent_track != -1:
                    point_index = -1
                    for i, p in enumerate(self.tracks[cent_track].ellps):
                        if p.x0 == cent.x and p.y0 == cent.y:
                            point_index = i
                            break
                    if point_index != -1:
                        self.tracks[cent_track].ellps.pop(point_index)
                        self.tracks[cent_track].draw()
                        self.canvas.draw()
        self.canvas.draw()

    def on_mouse_move(self, event):
        if self.prev_point and self.curr_point is None and event.inaxes == self.ax:
            if self.curr_line:
                self.curr_line.remove()
            self.curr_line = self.ax.plot([self.prev_point.x, event.xdata], \
                                          [self.prev_point.y, event.ydata], c="k", lw=1, zorder=10)[0]
        self.canvas.draw_idle()

    def is_center(self, x, y, c=0):
        mask = self.centers[self.shot + c, :, :] > 0
        centers = np.column_stack((self.mesh_lon[mask.T], self.mesh_lat[mask.T]))
        for center in centers:
            if np.isclose([x, y], center, atol=2).all():
                return True, Point(self.shot + c, center[0], center[1])
        return False, Point(-1, -1, -1)

    def in_track(self, point):
        for track in self.tracks:
            if track != 0 and track is not None:
                if track.ellps[-1].x0 == point.x and track.ellps[-1].y0 == point.y:
                    return track.index
        return -1

    def ask_to_save_track(self, index):
        response = messagebox.askyesnocancel("Save Track", "Do you want to save this track?")
        if response is not None:
            if response:
                for p in self.tracks[index].ellps:
                    self.centers[p.t, p.y0, p.x0] = np.nan
                self.tracks[index].save()
                messagebox.showinfo("Saving", f"Track was saved into {self.path_save_file}/{index:09d}.csv")

            if not response:
                for po in self.tracks[index].ellps:
                    if po.plot and po.plot in self.ax.lines:
                        po.plot.remove()
                if self.tracks[index].plot and self.tracks[index].plot in self.ax.lines:
                    self.tracks[index].plot.remove()
                for p in self.tracks[index].ellps:
                    if p and p in self.ax.collections:
                        p.remove()
                self.tracks.pop(index)

            self.curr_point = None
            self.prev_point = None
            if self.curr_line:
                self.curr_line.remove()
                self.curr_line = None

    def load_tracks(self, path):
        files = sorted(glob(path + "/[!~$]*.csv"))

        with xr.open_dataset(FILE_RORTEX) as ds:
            times = pd.to_datetime(ds["Time"].values)
            times_ns = times.astype("int64").to_numpy()

        for f in files:
            try:
                df = pd.read_csv(f)
                track_times = pd.to_datetime(df["time"])
                track_ns = track_times.astype("int64").to_numpy()
                diffs = np.abs(track_ns[:, None] - times_ns[None, :])

                matches = diffs <= 1_000_000_000
                matched_rows, matched_cols = np.where(matches)

                if len(matched_rows) != len(track_ns):
                    print(f"Time mismatch in {f} with {FILE_RORTEX} time grid!")
                    continue  # skip this file

                time_ind = np.full(len(track_ns), -1)
                time_ind[matched_rows] = matched_cols

                self.centers[time_ind,  # df['time_ind'].astype('int64')
                df['pyc_ind'].astype('int64'),
                df['pxc_ind'].astype('int64')] = np.nan
            except Exception as e:
                print(f"Failed to load track from {f}: {e}")
            self.tracks.append(0)
        print(f"loaded {len(self.tracks)} tracks from {path}")
        self.canvas.draw()


if __name__ == "__main__":
    app = MapApp()
    app.mainloop()
