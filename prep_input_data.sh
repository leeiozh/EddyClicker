#!/bin/bash

# run `conda activate cdo ``

# DBSCAN
echo "DBSCAN"
for i in $(ls /storage/kubrick/vkoshkina/data/LoRes/DBSCAN_nc/DBSCAN_02-04-10/DBSCAN_LoRes_2010-*.nc); do
	filename=$(basename -- "${i}")
	echo ${filename}
	ncks -C -O -x -v Time ${i} _000_${filename} &> dbscan.log
done
cdo -O mergetime _000_* merge_dbscan.nc  &> dbscan_merge.log
rm -rf _000_*

# SCALAR
echo "SCALAR"
for i in $(ls /storage/NAADSERVER/NAAD/LoRes/PressureLevels/geopotential/2010/geopotential_*.nc); do
	filename=$(basename -- "${i}")
	echo ${filename}
	cdo -sellevel,500 ${i} _000_${filename} &> scalar.log
done

cdo -O mergetime _000_* merge_scalar.nc &> scalar_merge.log
rm -rf _000_*

cdo -O merge merge_dbscan.nc merge_scalar.nc _LoRes_DBSCAN_2010.nc
cdo -O --reduce_dim -copy _LoRes_DBSCAN_2010.nc LoRes_DBSCAN_2010.nc
rm -rf merge_dbscan.nc merge_scalar.nc _LoRes_DBSCAN_2010.nc