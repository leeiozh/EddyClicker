
import pandas as pd  #
import xarray as xr  # conda install -c conda-forge xarray dask netCDF4 bottleneck
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from const import *
from track import *
# plot on map:
import cartopy.crs as ccrs
import cartopy.feature as cfeature



def get_tracks(files,time):

    nfiles = len(files)

    result = []

    for ii in files:

        trk_df = pd.read_csv(ii, index_col='time', skipinitialspace=True)

        tmp = trk_df[trk_df.index == time]

        if len(tmp) != 0:
            result.append(trk_df[:time])

    return result

def get_track_EddyClicker(ds: xr.Dataset, trk_df: pd.DataFrame) -> [list,list]:
    """
    ds - xr.Dataset file with coordinate arrays XLAT, XLONG
    trk_df - data from track file
    """

    lats = []
    lons = []
    for index, row in trk_df.iterrows(): 

        ilat = ds['XLAT'].isel(
            west_east=int(row['pxc_ind']), 
            south_north=int(row['pyc_ind']), 
            # method='nearest',
            ).to_numpy()
        ilon = ds['XLONG'].isel(
            west_east=int(row['pxc_ind']), 
            south_north=int(row['pyc_ind']), 
            # method='nearest',
            ).to_numpy()

        lats.append(ilat)
        lons.append(ilon)

    return lons, lats

def get_track_Automate(trk_df: pd.DataFrame) -> [list,list]:
    """
    trk_df - data from track file
    """

    return trk_df['lon'].values, trk_df['lat'].values



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
    # Read WRF borders
    lon_btm = ds.XLONG.isel(south_north=0)
    lon_lft = ds.XLONG.isel(west_east=0)
    lon_top = ds.XLONG.isel(south_north=-1)
    lon_rgt = ds.XLONG.isel(west_east=-1)
    lat_btm = ds.XLAT.isel(south_north=0)
    lat_lft = ds.XLAT.isel(west_east=0)
    lat_top = ds.XLAT.isel(south_north=-1)
    lat_rgt = ds.XLAT.isel(west_east=-1)
    lon_rgt = xr.where(lon_rgt<0, lon_rgt+360, lon_rgt) # X ; 2; ;

    xdim, ydim = ds.sizes['west_east'], ds.sizes['south_north']
    

# Plotting

    # Create a figure
    fig = plt.figure(figsize=(8, 10)) # constrained_layout=True,

    # Add a GridSpec to the figure, defining a 3x3 grid
    gs = gridspec.GridSpec(6, 1)
    ax1 = fig.add_subplot(gs[0:4], projection=ccrs.NorthPolarStereo(central_longitude=ds.STAND_LON))
    ax2 = fig.add_subplot(gs[4])
    ax3 = fig.add_subplot(gs[5])

    proj = ccrs.PlateCarree()

    ax1.coastlines('50m', alpha=1,linewidth=1)
    ax1.add_feature(cfeature.LAND, alpha=0.9)
    # ax.add_feature(cfeature.OCEAN, alpha=0.5)
    # ax.set_extent([30, 90, 65, 85], crs=ccrs.PlateCarree())
    gl = ax1.gridlines(crs=proj,
                      draw_labels=True, dms=True,
                      x_inline=False, y_inline=False,
                      linewidth=0.5, linestyle=":", color='gray', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 6} # , 'color': 'gray'
    gl.ylabel_style = {'size': 6} # , 'color': 'gray'
    gl.rotate_labels=0

    ax1.plot(lon_btm, lat_btm, color="black", transform=proj, label=f"WRF domain")
    ax1.plot(lon_lft, lat_lft, color="black", transform=proj)
    ax1.plot(lon_top, lat_top, color="black", transform=proj)
    ax1.plot(lon_rgt, lat_rgt, color="black", transform=proj)

    length = []
    distance = []
    for ii, itrk in enumerate(files):

        print(f" Track {(ii+1):04d} out of {len(files)}", end='')

        trk_df = pd.read_csv(itrk, skipinitialspace=True)

        dist = np.sqrt(
            (trk_df['x'].iloc[0] - trk_df['x'].iloc[-1])**2 +
            (trk_df['y'].iloc[0] - trk_df['y'].iloc[-1])**2
            )

        # Drop border tracks
        if trk_df['x'].min() < 3             or \
                trk_df['x'].max() > xdim - 5 or \
                trk_df['y'].min() < 3        or \
                trk_df['y'].max() > ydim - 5:
            print(" Out of domain")
            continue

        if len(trk_df) < 12:
            print(" Too brief")
            continue

        if dist < 50:
            print(" Too short")
            continue

        print(" Ok")

        try:
            # data from EddyClicker
            lons, lats = get_track_EddyClicker(ds,trk_df)
        except:
            # data from automatic gen
            lons, lats = get_track_Automate(trk_df)

        ax1.plot(
            lons,
            lats,
            alpha = 0.7,
            color = 'tab:red',
            linewidth=2,
            transform=proj,
            )

        length.append(len(trk_df))
        distance.append(dist)

        # if ii == 1000: break

    ax1.set_title(f"Tracks: {len(length)}/{len(files)}, file: {FILE_RORTEX}")
    ax1.legend(loc='upper right')

    ax2.set_title(f"Length from {min(length)} to {max(length)}")
    ax2.tick_params(axis='y', direction='in', labelleft=False)
    ax2.tick_params(axis='x', direction='in')
    # ax2.grid(axis='both', linestyle=':', color='lightgray', linewidth=0.5)
    ax2.hist(length, bins=np.arange(0,45,5), color='tab:blue', edgecolor='black')

    ax3.set_title(f"Distance from {min(distance):.1f} to {max(distance):.1f}")
    ax3.tick_params(axis='y', direction='in', labelleft=False)
    ax3.tick_params(axis='x', direction='in')
    # ax3.grid(axis='both', linestyle=':', color='lightgray', linewidth=0.5)
    ax3.hist(distance, bins=np.arange(0,150,10), color='tab:blue', edgecolor='black')

    
    plt.savefig(f"./{TRACKS_CHECK_FOLDER}/{TRACKS_FOLDER}_map_cartopy.png", dpi=300)  # , transparent=True
    plt.show()
    plt.close()




if __name__ == "__main__":
    main()
