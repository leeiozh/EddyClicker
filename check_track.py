import argparse
import pandas as pd  #
import xarray as xr  # conda install -c conda-forge xarray dask netCDF4 bottleneck
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

from const import *
from track import *

NTHETA = 36
NRADIUS = 100


def newcolormap():
    from matplotlib.colors import ListedColormap, LinearSegmentedColormap
    from matplotlib import cm

    cmap = plt.get_cmap('PuOr_r', 256)
    newcolors = cmap(np.linspace(0, 1, 256))
    color = np.array([256 / 256, 256 / 256, 256 / 256, 0])

    icenter = int(256 / 2)
    newcolors[icenter:icenter, :] = color
    newcmp = ListedColormap(newcolors)

    return newcmp


def main():
    parser = argparse.ArgumentParser(description="Plot some track features for sanity check")
    parser.add_argument('-i', '--input', type=str, help="Input track file", required=True)
    parser.add_argument('-a', '--advansed', type=str, help="More statistics (needs TEST_TRACK_SRC in const.py)")
    args = parser.parse_args()

    new_cmap = newcolormap()

    ### READ: TRACK

    trk_file = Path(args.input)
    trk_df = pd.read_csv(trk_file, index_col=1, skipinitialspace=True)
    # print(trk_df)

    folder_path = Path(f'./track_plots/{trk_file.stem}')
    folder_path.mkdir(parents=True, exist_ok=True)

    ### READ: NC FILE

    with xr.open_dataset(FILE_LAND) as ds:
        hgt = ds['hgt']
        hgt = xr.where(hgt > 5, 1, np.nan)

    # with xr.open_dataset(FILE_RORTEX) as ds:
    #         ror = ds[RORTEX_VARNAME]
    #         ror = xr.where(((ror < 10) & (ror > -10)), np.nan, ror)

    ds = xr.open_dataset(FILE_RORTEX)

    for index, row in trk_df.iterrows():

        print(index)

        bad = False

        it_wrf = int(row['time_ind'])
        it_trk = int(row.iloc[0])

        ror_src = ds[RORTEX_VARNAME][it_wrf, 0]
        ror_nan = xr.where(((ror_src < 10) & (ror_src > -10)), np.nan, ror_src)

        if it_trk != 0:
            # Извлечь координаты эллипса
            x0 = float(row['pxc_ind'])
            y0 = float(row['pyc_ind'])
            x1 = float(row['px1_ind'])
            y1 = float(row['py1_ind'])
            x2 = float(row['px2_ind'])
            y2 = float(row['py2_ind'])
            x3 = float(row['px3_ind'])
            y3 = float(row['py3_ind'])

            p1 = np.array([x1, y1])
            p2 = np.array([x2, y2])
            p3 = np.array([x3, y3])

            el = Ellipse(0, x0, y0, p1, p2, p3, None)

            xe, ye = el.get_perimeter()

            # Вырезать данные из эллипса
            data_ax2 = el.interpol_data(ror_src.values, NRADIUS, NTHETA)

            wspd = np.sqrt(ds['ue'][it_wrf, 0].values ** 2 + ds['ve'][it_wrf, 0].values ** 2)
            data_ax3 = el.interpol_data(wspd, NRADIUS, NTHETA)

            data_ax4 = el.interpol_data(ds['geopotential'][it_wrf, 0].values, NRADIUS, NTHETA)

            azimuths = np.radians(np.linspace(0, 360, NTHETA))
            zeniths = np.arange(0, NRADIUS, 1)
            r, theta = np.meshgrid(zeniths, azimuths)

        ### PLOT

        fig = plt.figure(figsize=([15, 7]), constrained_layout=True)
        spec = gridspec.GridSpec(ncols=4, nrows=2, hspace=0.1, wspace=0)  #
        # spec.update(wspace = 1.5, hspace = 0.3)
        ax1 = fig.add_subplot(spec[0:2, 0:2])
        ax2 = fig.add_subplot(spec[0, 2], projection='polar')
        ax3 = fig.add_subplot(spec[0, 3], projection='polar')
        ax4 = fig.add_subplot(spec[1, 2], projection='polar')
        # ax5 = fig.add_subplot(spec[1, 1], projection = 'polar')
        # ax6 = fig.add_subplot(spec[1, 2], projection = 'polar')

        hgt.plot(ax=ax1, add_colorbar=False, alpha=0.3, cmap='Greys')

        mod_val = np.nanmax(np.abs(ror_src.values))
        vmin, vmax = -mod_val, mod_val
        levels = np.linspace(vmin, vmax, 21)

        ror_nan.plot(
            ax=ax1,
            alpha=0.9,
            cmap='PuOr_r',
            levels=levels,
            # vmin=-20, vmax=20,
            extend='both',
            add_colorbar=False,
        )

        ax1.plot(  # TRACK
            trk_df['pxc_ind'][:it_trk + 1],
            trk_df['pyc_ind'][:it_trk + 1],
            color='red',
            linewidth=1.5,
        )

        if it_trk != 0:
            ax1.plot(  # ELLIPSE
                xe,
                ye,
                color='black',
                linewidth=1.5,
            )

        ax1.plot(  # CENTERS
            row['pxc_ind'],
            row['pyc_ind'],
            "o",
            markerfacecolor='red',
            markeredgecolor='black',
            markersize=5
        )

        ax1.tick_params(direction='in', labelsize=6)
        ax1.set_xlabel("")
        ax1.set_ylabel("")
        ax1.set_title(index)

        ### PLOT: AX2

        # Plot data function

        if row['pxc_ind'] == row['px1_ind']:
            bad = True

        if it_trk != 0 and not bad:
            mod_val = np.max(np.abs(data_ax2))
            vmin, vmax = -mod_val, mod_val
            levels = np.linspace(vmin, vmax, 21)

            plt2 = ax2.contourf(
                theta,
                r,
                data_ax2,
                # vmin=vmin, vmax=vmax,
                levels=levels,
                cmap=new_cmap,  # pplt.Colormap('ColdHot'), #cmaps.NCV_blu_red, # 'RdYlBu_r',
                extend='both',
            )

        # cbar = ax2.colorbar(pax2)
        ax2.grid(color='gray', alpha=0.5, linestyle=':')
        ax2.tick_params(direction='in', length=0, width=0)
        ax2.axes.xaxis.set_ticklabels([])
        ax2.axes.yaxis.set_ticklabels([])

        ax2.set_title("Rortex")

        ### PLOT: AX3

        # Plot data function

        if it_trk != 0 and not bad:
            ax3.contourf(
                theta,
                r,
                data_ax3,
            )

        ax3.grid(color='gray', alpha=0.5, linestyle=':')
        ax3.tick_params(direction='in', length=0, width=0)
        ax3.axes.xaxis.set_ticklabels([])
        ax3.axes.yaxis.set_ticklabels([])

        ### PLOT: AX4

        # Plot data function

        if it_trk != 0 and not bad:
            # mod_val = np.max( np.abs( data_ax4 ) )
            # vmin, vmax = -mod_val, mod_val
            levels = np.linspace(np.min(data_ax4), np.max(data_ax4), 21)

            ax4.contourf(
                theta,
                r,
                data_ax4,
                # vmin=vmin, vmax=vmax,
                levels=levels,
                cmap='Purples_r',  # pplt.Colormap('ColdHot'), #cmaps.NCV_blu_red, # 'RdYlBu_r',
                extend='both',
            )

        ax4.grid(color='gray', alpha=0.5, linestyle=':')
        ax4.tick_params(direction='in', length=0, width=0)
        ax4.axes.xaxis.set_ticklabels([])
        ax4.axes.yaxis.set_ticklabels([])

        ax2.set_title("Wind at 10", fontsize=8)
        ax3.set_title("Rortex", fontsize=8)
        ax4.set_title("Geopotential", fontsize=8)

        plt.savefig(f"{folder_path}/{it_trk:04d}.png", dpi=300)  # , transparent=True
        # plt.show()
        plt.close()


if __name__ == "__main__":
    main()
