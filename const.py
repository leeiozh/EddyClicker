from netCDF4 import Dataset
import numpy as np

RES = 'LoRes'; PREF = '77km'

RORTEX_VARNAME = 'R2D'
LOCAL_EXTR_VARNAME = 'local_extr_crit'
SCALAR_VARNAME = 'geopotential'
SCALAR_LEVELS = np.arange(40000,70000,100)


TRACKS_FOLDER = f'track_folder'
FILE_SCALAR = f'tmp.nc'
FILE_RORTEX = f'LoRes_DBSCAN_2010.nc'
FILE_SAVE = f"test.txt"

FILE_LAND = f"/storage/NAADSERVER/NAAD/{RES}/Invariants/NAAD{PREF}_hgt.nc"
ds_land = Dataset(FILE_LAND)
LAND = ds_land["hgt"][:, :]
ds_land.close()
LAND = np.where(LAND > 0, 0, np.nan)

from pyproj import Geod

geod = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)