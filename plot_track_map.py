
import pandas as pd  #
import xarray as xr  # conda install -c conda-forge xarray dask netCDF4 bottleneck
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

from const import *
from track import *


def get_tracks(files,time):

    nfiles = len(files)

    result = []

    for ii in files:

        trk_df = pd.read_csv(ii, index_col='time', skipinitialspace=True)

        tmp = trk_df[trk_df.index == time]

        if len(tmp) != 0:
            result.append(trk_df[:time])

    return result

def main():

    levels = np.linspace(-50, 50, 41)

    # COLLECT TRACK FILES
    p = sorted(Path(f'./{TRACKS_FOLDER}').glob('**/*.csv'))
    files = [x for x in p if x.is_file()]

    # MAKE OUTPUT DIR
    folder_out = Path(f'./{TRACKS_ANIMATION_FOLDER}/')
    folder_out.mkdir(parents=True, exist_ok=True)


    ### READ: NC FILE

    ds = xr.open_dataset(FILE_RORTEX)

    hgt = ds[HGT_VARNAME]
    hgt = xr.where(hgt > 5, 1, np.nan)


    fig, ax1 = plt.subplots(1, 1, figsize=(WINDOW_WIDTH/100, SCREEN_HEIGHT/150), constrained_layout=True)
    hgt.plot(ax=ax1, add_colorbar=False, alpha=0.3, cmap='Greys')


    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.set_axis_off()
    # ax1.grid(True)

    for itrk in files:

        trk_df = pd.read_csv(itrk, index_col='time', skipinitialspace=True)

        ax1.plot(
            trk_df['pxc_ind'],
            trk_df['pyc_ind'],
            color = 'tab:red',
            linewidth=2,
            )


    ax1.set_title(f"Tracks: {len(files)}, file: {FILE_RORTEX}")

    # plt.savefig(f"{TRACKS_FOLDER}_map.png", dpi=150)  # , transparent=True
    plt.show()
    plt.close()




if __name__ == "__main__":
    main()
