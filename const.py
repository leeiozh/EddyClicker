from netCDF4 import Dataset
import numpy as np

###############################################################################
### CHANGE THIS START #########################################################

# GUI WINDOWS SIZE
SCREEN_HEIGHT = 850
WINDOW_WIDTH = 1500

# INPUT AND OUTPUT FILE 
FILE_RORTEX = "TEST.nc"
TRACKS_FOLDER = "track_folder"  # track output folder

# REQUIRED VARIABLES
LEVEL = 0  # Level of interest
RORTEX_VARNAME = "R2D"  # Rortex variable to plot
LOCAL_EXTR_VARNAME = "local_extr_cluster"  # dots to plot (scatter)
HGT_VARNAME = "HGT"  # coastline plot (2D curve)

# OTHER VARIABLES (vars to help recognize vortices)
SCALARS = [
    {"name": "slp", "land": True, "step": 1, "cmap": ""},  # REQUIRED, Key Q
    {"name": "cloudfrac", "land": False, "step": 0.01, "cmap": "binary_r"},  # Optional, Key W
    {"name": "wspd", "land": False, "step": 1, "cmap": "viridis"},  # Optional, Key E
]

### CHANGE THIS END   #########################################################
###############################################################################


### BELOW: YOU CAN ONLY CHANGE IF YOU KNOW WHAT YOU ARE DOING!

# Get land map
ds_land = Dataset(FILE_RORTEX)
LAND = ds_land[HGT_VARNAME][:, :]
LAND = np.where(LAND > 5, 0, 1)

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
