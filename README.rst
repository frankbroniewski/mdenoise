MDenoise for QGIS 3
===================

Mdenoise is a utility that smoothens raster elevation data like the ones from 
SRTM scenes.

Obtain Mdenoise
---------------

Mdenoise can be downloaded from the project page
[1] https://personalpages.manchester.ac.uk/staff/neil.mitchell/mdenoise/
[2] https://github.com/exuberant/mdenoise

There's a binary available for Windows, Mac & Linux users need to compile
it from source

IMPORTANT
=========
MDenoise - at least the Windows binary - is not capable of denoising SRTM
1-arc-sec scenes and runs out of memory, which makes it pretty useless.

I've a shell script from 3-arc-sec times which I used to denoise my 90m 
resolution scenes. Without testing if Mdenoise is still capabable of doing
its work I set afoot to program my Processing script for QGIS 3.

Unfortunately as it stands now, I won't be continuing the work, even if the 
script is close to a primary release.

Well at least I learnt quite a few things, so not everything is lost
