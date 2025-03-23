# EddyClicker

Project for manual eddies tracking written by Elizaveta Ezhova (October, 2024).

## Installing

All packages are listed in environment.yml, so you can install it using pip or Anaconda.

```sh
cd EddyClicker
conda env create --file environment.yml
conda activate clicker_env
python eddyclicker.py
```

<!-- ```sh
python -m venv clicker_env
source clicker_env/bin/activate
pip install -r requirements.txt
python eddyclicker.py
```
 -->
## Using

### Data Preprocessing

The input file should be one has to contain all necessary data:

* 1d (time)     : XTIME as linux epoch ('XXX since 1979-01-01')
* 2d (y,x)      : XLAT, XLONG
* 3d (time,y,x) : Rortex field, scalar field (ex. geopotential), coordinates of Rortex extremes, second plot field (
  WSPD, CF, etc)

*Details will come later*

### First start

Edit the `const.file`:

```python
# DATASET DESCRIPTION (not nesesary )
RES = 'SMP'
PREF = '6km'

### MAIN VARIABLES

# GUI windows size
SCREEN_HEIGHT = 650
WINDOW_WIDTH = 1200

LEVEL = 0  # Level of interest
RORTEX_VARNAME = 'R2D'  # Criteria to plot (contourf)
LOCAL_EXTR_VARNAME = 'local_extr_cluster'  # dots to track (scatter)
SCALAR1_VARNAME = 'geopotential'  # help field (contour)
SCALAR1_LEVELS_STEP = 50  # contour interval
SCALAR1_LEVELS_FINE_STEP = 10  # contour interval view
SCALAR2_VARNAME = 'WSPD'  # help field (at spacebar)

TRACKS_FOLDER = 'track_folder'  # Output folder for track files
FILE_RORTEX = '2019-01.nc'  # Input file
FILE_SAVE = f'test.txt'

# Get land map
ds_land = Dataset(FILE_RORTEX)
LAND = ds_land["HGT"][:, :]
LAND = np.where(LAND > 5, 0, np.nan)

# Level height (km) at the title. Needed ones
LEV_HGT = np.nanmean(
    ds_land["geopotential"][0, LEVEL, :, :]) / 10 / 1000
ds_land.close()

# Map settings
from pyproj import Geod

GEOD = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)

first_time = False

# CIRCLE SETTINGS FOR POSTPROCESSING (CHECK TRACK)
NRADIUS = 100
NTHETA = 36

```

### Navigation

* `->` - move to next stamp
* `<-` - move to prev stamp
* `LMC` - select the point
* `Esc` - undo the last action
* `RMC` - save the track
* `2xLMC` - pop the point
* `spase` - switch to addinional field (`SCALAR2`) and back
* `cntr + z` - undo the last ellipse and track segment at ones
* Upper level field - time to jump instantly

You can also use matplotlib build-in buttons to ZOOM and MOVE the plot.

### Tracking

It is strongly suggested to track one vortex at a time!

The current time step is displayed in the title. You can use the left and right arrow keys on the keyboard to move forward
and backward in time. The current coordinates of the centers of the identified vortices are shown as black dots, while
the previous ones are shown as circles. To draw a track, you need to connect a black dot to a circle.

Next, you will have three left mouse clicks to mark the size of the vortex (as an ellipse). The first two clicks are for
the major axis of the ellipse, and the third click is for the minor axis, all marked as blue dots.

To create a track segment, connect a circle to a black dot. Then, you need to draw an ellipse around the structure using
three left-clicks. The first two clicks indicate the major axis, and the third click marks the minor axis. When you want
to finish the track, right-click on the endpoint of the track (black dot). The geographic coordinates of all points on
the track will be sequentially written to the specified file in the `TRACKS_FOLDER` folder. After that, the completed
track will be deleted from the map. If you realize you made a mistake with the track, you can simply delete (`NO`) the
track and start over.