
import pandas as pd  #
import xarray as xr  # conda install -c conda-forge xarray dask netCDF4 bottleneck
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

from const import *
from track import *

# ffmpeg -framerate 10 -i smp_%05d.png -c:v libx264 -r 30 -pix_fmt yuv420p fileout.mp4

def get_tracks(files,time):

    nfiles = len(files)

    result = []

    for ii in files:

        trk_df = pd.read_csv(ii, index_col='time', skipinitialspace=True)
        trk_df['TrackNo'] = int(ii.stem)

        tmp = trk_df[trk_df.index == time]

        if len(tmp) != 0:
            result.append(trk_df[:time])

    return result

def get_time_lims(files,times):

    mins = []
    maxs = []

    for ii in files:

        trk_df = pd.read_csv(ii, skipinitialspace=True)
        
        mins.append(trk_df['time'].iloc[ 0])
        maxs.append(trk_df['time'].iloc[-1])

    df = pd.DataFrame({'mins':mins, 'maxs':maxs})

    df_time = pd.DataFrame({'times':times})

    ts = df['mins'].min()
    te = df['maxs'].max()

    tsi = df_time.index[df_time['times'] == ts].values[0]
    tei = df_time.index[df_time['times'] == te].values[0]
    return tsi, tei



def main():

    levels = np.linspace(-50, 50, 41)

    # COLLECT TRACK FILES
    p = sorted(Path(f'./{TRACKS_FOLDER}').glob('**/*.csv'))
    files = [x for x in p if x.is_file()]
    # p = sorted(Path(f'./track_folder.MatveySMP-2019-01/').glob('**/*.csv'))
    # files_tmp = [x for x in p if x.is_file()]
    # files = files_tmp + files

    # MAKE OUTPUT DIR
    folder_out = Path(f'./{TRACKS_CHECK_FOLDER}/{TRACKS_ANIMATION_FOLDER}/{TRACKS_FOLDER}/')
    folder_out.mkdir(parents=True, exist_ok=True)

    ### READ: NC FILE

    ds = xr.open_dataset(FILE_RORTEX)

    times  = pd.to_datetime(ds['Time'])

    tsi, tei = get_time_lims(files,times)
    # tsi, tei = 0, len(times)

    iit = 0
    for itime in range(tsi,tei):

        print(times[itime])


        # fig = plt.figure(figsize=([7, 7]), constrained_layout=True)
        # spec = gridspec.GridSpec(ncols=1, nrows=1, hspace=0.1, wspace=0)
        # ax1 = fig.add_subplot(spec[0])
        fig, ax1 = plt.subplots(1, 1, figsize=(WINDOW_WIDTH/100, SCREEN_HEIGHT/150)) # , constrained_layout=True


        ax1.contour(LAND,
            [0],
            alpha=1,
            linewidths=2,
            colors='grey',
            )

        tmp = ds[RORTEX_VARNAME][itime,0]
        R2D = xr.where(((tmp < 10) & (tmp > -10)), np.nan, tmp)

        R2D.plot(
            ax=ax1,
            alpha=0.9,
            cmap='PuOr_r',
            levels=levels,
            # vmin=-20, vmax=20,
            extend='both',
            add_colorbar=False,
        )


        tracks = get_tracks(files,str(times[itime]))

        ntracks = len(tracks)

        if ntracks != 0:

            for itrk in tracks:

                # print(itrk['pxc_ind'])
                # print(float(itrk['pxc_ind'].values[0]))
                # exit()

                ax1.plot(
                    itrk['pxc_ind'].values,
                    itrk['pyc_ind'].values,
                    color = 'black',
                    linewidth=3,
                    )


                tmp = itrk.reset_index()
                points = tmp[ pd.to_datetime(tmp['time']) == times[itime]  ]

                for index, row in points.iterrows():

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

                    xe = np.append(xe,xe[0])
                    ye = np.append(ye,ye[0])

                    ax1.plot(  # ELLIPSE
                        xe,
                        ye,
                        color='tab:red',
                        linewidth=2,
                    )

                ax1.text(
                    float(itrk['pxc_ind'].values[-1])+5,
                    float(itrk['pyc_ind'].values[-1]),
                    itrk['TrackNo'].values[0],
                    )

        ax1.set_title(f"{times[itime]}", fontsize=8)
        # ax1.set_title(f"{times[itime]} (no. of tracks on map = {ntracks})", fontsize=8)

        plt.savefig(f"{folder_out}/tracks_{int(iit):05d}.png", dpi=150)  # , transparent=True
        # plt.show()
        plt.clf()
        plt.close()

        iit = iit + 1

    print(f"FINISHED")
    print(f"Now you can make a movie:")
    print(f"# ffmpeg -framerate 10 -pattern_type glob -i /{folder_out}/'tracks_*.png' -c:v libx264 -pix_fmt yuv420p -vf 'pad=ceil(iw/2)*2:ceil(ih/2)*2' ./{TRACKS_CHECK_FOLDER}/{TRACKS_FOLDER}.mp4")


if __name__ == "__main__":
    main()
