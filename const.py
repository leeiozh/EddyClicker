from netCDF4 import Dataset
import numpy as np

TRACKS_FOLDER = "track_folder"
FILE_BACK = "rortex_2d_criteria_HiRes_level_12_2010-01.nc"
FILE_EDD = "HiRes_2010-01.nc"
FILE_SAVE = "test.txt"

FILE_LAND = "NAAD14km_hgt.nc"
ds_land = Dataset(FILE_LAND)
LAND = ds_land["hgt"][:, :]
ds_land.close()
LAND = np.where(LAND > 0, 0, np.nan)
