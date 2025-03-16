from netCDF4 import Dataset
import numpy as np

### MAIN VARIABLES

# GUI windows size
SCREEN_HEIGHT = 850
WINDOW_WIDTH = 1500

LEVEL = 0  # Level of interest
RORTEX_VARNAME = 'R2D'  # Criteria to plot (contourf)
LOCAL_EXTR_VARNAME = 'local_extr_cluster'  # dots to plot (scatter)

SCALARS = {
	'scalar1': {'name':'geopotential', 'step': 50  , 'cmap': '' },
	'scalar2': {'name':'cloudfrac'   , 'step': 0.01, 'cmap': 'binary_r'},
	# 'scalar2': {'name':'WSPD'        , 'step': 1   , 'cmap': 'viridis' },
}


TRACKS_FOLDER = 'track_folder'  # track output folder
FILE_RORTEX = "2019-01.nc"  # Input file #
FILE_SAVE = f"test.txt"

# Get land map
ds_land = Dataset(FILE_RORTEX)
LAND = ds_land["HGT"][:, :]
LAND = np.where(LAND > 5, 0, np.nan)

# Level height at the title (km)
LEV_HGT = np.nanmean(ds_land["geopotential"][0, LEVEL, :, :]) / 10 / 1000
ds_land.close()

# Map settings
from pyproj import Geod

GEOD = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)

# FOR POSTPROCESSING (CHECK TRACK)
NRADIUS = 100
NTHETA = 36
