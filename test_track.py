import argparse
import pandas as pd # 
import xarray as xr # conda install -c conda-forge xarray dask netCDF4 bottleneck
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from const import *

def main():

    parser = argparse.ArgumentParser(description = "Plot some track features for sanity check")
    parser.add_argument('-i', '--input', type=str, help="Input track file", required=True)
    parser.add_argument('-a', '--advansed', type=str, help="More statistics (needs TEST_TRACK_SRC in const.py)")
    args = parser.parse_args()

    ifile = args.input
    df = pd.read_csv(ifile, index_col=1)


    with xr.open_dataset(FILE_LAND) as ds:
            hgt = ds['hgt']
            hgt = xr.where(hgt > 5, 1, np.nan)

    # fig = plt.figure(figsize=(7,7), dpi=150)


    fig, axs = plt.subplots(ncols=2, nrows=1, figsize=(10, 10), constrained_layout=True)

    hgt.plot(ax=axs[0], add_colorbar=False, alpha=0.3, cmap='Greys')

    axs[0].plot(
        df['pxc_ind'],
        df['pyc_ind'],
        # ax = axs[0],
        "*",
        markerfacecolor='black',
        markeredgecolor='black',
        markersize=10
        )


    axs[0].grid(color='gray', alpha=0.5, linestyle=':')
    axs[0].tick_params(direction='in', length=0, width=0)

    # plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    main()
