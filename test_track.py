import argparse
import pandas as pd # 
import xarray as xr # conda install -c conda-forge xarray dask netCDF4 bottleneck

from const import *

def main():

    parser = argparse.ArgumentParser(description = "Plot some track features for sanity check")
    parser.add_argument('-i', '--input', type=str, help="Input track file", required=True)
    parser.add_argument('-a', '--advansed', type=str, help="More statistics (needs TEST_TRACK_SRC in const.py)")
    args = parser.parse_args()

    ifile = args.input
    df = pd.read_csv(ifile, 
    	delimiter=";", 
    	header=None, 
    	index_col=0, 
    	names=['time', 'time_ind', 'pxc_ind','pyc_ind','px1_ind','py1_ind','px2_ind','py2_ind','px3_ind','py3_ind'])
    
    df['datetime'] = pd.to_datetime(df.index, unit='m', origin='unix')

    print(df)

    with xr.open_dataset(FILE_RORTEX) as ds:
    	print(ds.XTIME)





if __name__ == "__main__":
    main()
