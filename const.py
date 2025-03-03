from netCDF4 import Dataset
import numpy as np

# Подготовка данных
# cdo select,var=HGT /storage/kubrick/SMP6km/2021/wrfout_d01_2021-02-23_00.nc tmp.nc
# cdo seltimestep,1 tmp.nc tmp1.nc
# cdo --reduce_dim tmp1.nc tmp2.nc
# cdo chname,HGT,hgt tmp2.nc SMP6km_hgt.nc
# rm tmp*
#
# cp scp kubrick:/storage/kubrick/vkoshkina/data/SMP/R2D_SMP_smoothing/sigma_2_R2D_SMP_2021-02-23.nc .
# cdo merge geopotential.nc sigma_2_DBSCAN_SMP_level_20_2021-02-23.nc tmp.nc
# mv tmp.nc sigma_2_DBSCAN_SMP_level_20_2021-02-23.nc
#

RES = 'SMP'
PREF = '6km'

LEVEL = 10
RORTEX_VARNAME = 'R2D'
LOCAL_EXTR_VARNAME = 'local_extr_crit'
SCALAR_VARNAME = 'geopotential'
VELOCITY_VARNAME = ("ue", "ve")
SCALAR_LEVELS_STEP = 50
# SCALAR_LEVELS = np.arange(40000, 70000, 50)
# SCALAR_LEVELS_FINE = np.arange(40000, 70000, 10)
SCALAR_LEVELS_FINE_STEP = 10

TRACKS_FOLDER = 'track_folder'
FILE_RORTEX = "sigma_2_DBSCAN_SMP_2021-02-23_with_params.nc"
FILE_SAVE = f"test.txt"

SCREEN_HEIGHT = 800  # self.winfo_screenheight()
WINDOW_WIDTH = 1200  # int(screen_height * WIN_SCALE)

ds_land = Dataset(FILE_RORTEX)
LAND = ds_land["HGT"][0, :, :]
LAND = np.where(LAND > 5, 0, np.nan)
WIN_SCALE = 1
TEST_TRACK_SRC = "./"

LEV_HGT = np.nanmean(
    ds_land["geopotential"][0, LEVEL, :, :]) / 10 / 1000  # Для вывода высоты уровня на картинку (считаем один раз)

ds_land.close()

from pyproj import Geod

GEOD = Geod(ellps="WGS84")
PHI = np.linspace(0, 2 * np.pi, 100)

first_time = False
