from netCDF4 import Dataset
import numpy as np

RES = 'LoRes'
PREF = '77km'

RORTEX_VARNAME = 'R2D'
LOCAL_EXTR_VARNAME = 'local_extr_crit'
SCALAR_VARNAME = 'geopotential'
VELOCITY_VARNAME = ("ue", "ve")
SCALAR_LEVELS = np.arange(40000, 70000, 50)
SCALAR_LEVELS_FINE = np.arange(40000, 70000, 10)

TRACKS_FOLDER = 'track_folder'
FILE_RORTEX = "LoRes_DBSCAN_2010_new.nc"
FILE_SAVE = f"test.txt"

FILE_LAND = "NAAD77km_hgt.nc"
ds_land = Dataset(FILE_LAND)
LAND = ds_land["hgt"][:, :]
ds_land.close()
LAND = np.where(LAND > 0, 0, np.nan)
WIN_SCALE = 1
TEST_TRACK_SRC = "./"

from pyproj import Geod
GEOD = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)

first_time = False