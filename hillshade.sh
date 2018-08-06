#!/bin/bash
INFILE=$1
FILLED_DEM=/tmp/filled.gtif
PROJ_DEM=/tmp/projected_dem.gtif
DENOISE_DEM=/tmp/denoise_me.asc
DENOISED_DEM=/tmp/denoised.asc
DEM_FILE=dem.gtif
HILLSHADE_FILE=hillshade.gtif
ASPECT_FILE=aspect.gtif
CWD="$(pwd)"

N=10
T=0.95
Z=1.5

gdal_fillnodata.py $INFILE $FILLED_DEM
gdalwarp -t_srs "EPSG:31466" $FILLED_DEM $PROJ_DEM
gdal_translate -of AAIGrid $PROJ_DEM $DENOISE_DEM
/home/frank/bin/mdenoise -i $DENOISE_DEM -n $N -t $T -o $DENOISED_DEM
gdal_translate -a_srs "EPSG:31466" $DENOISED_DEM "$CWD/$DEM_FILE"
gdaldem hillshade -combined -z $Z "$CWD/$DEM_FILE" "$CWD/$HILLSHADE_FILE"
gdaldem aspect "$CWD/$DEM_FILE" "$CWD/$ASPECT_FILE"

rm $FILLED_DEM
rm $PROJ_DEM
rm $DENOISE_DEM
rm $DENOISED_DEM
