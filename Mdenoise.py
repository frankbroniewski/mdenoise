# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingFeedback,
                       QgsProcessingUtils,
                       QgsProcessingOutputLayerDefinition,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination)
import processing

import os
import subprocess


class SmoothElevation(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    CRS = 'CRS'
    PIXELSIZE = 'PIXELSIZE'
    REPROJECT = 'REPROJECT'
    MDENOISE = 'MDENOISE'
    N = 'N'
    T = 'T'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SmoothElevation()

    def name(self):
        return 'mdenoise'

    def displayName(self):
        return self.tr('Smooth elevation raster')

    def group(self):
        return self.tr('Terrain')

    def groupId(self):
        return 'terrain'

    def shortHelpString(self):
        return self.tr("Smooth a elevation raster with mdenoise")

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Elevation raster')
            )
        )

        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('Projected CRS for denoising (choose on that fits the region)')
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PIXELSIZE,
                self.tr('Pixel size in meters of the input elevation data'),
                defaultValue=30.0
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.REPROJECT,
                self.tr('Reproject the raster back into the original CRS?')
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.MDENOISE,
                self.tr('Location of the mdenoise executable'),
                defaultValue = r'C:/Users/GIS/bin/MDenoise.exe'
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.N,
                self.tr('Number of iterations'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=10
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.T,
                self.tr('Threshold'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.95
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Smoothed elevation')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        input_evelation = self.parameterAsRasterLayer(parameters, self.INPUT,
                                                      context)
        # -> QgsRasterLayer
        project_crs = self.parameterAsCrs(parameters, self.CRS, context)
        reproject = self.parameterAsBool(parameters, self.REPROJECT, context)
        mdenoise_path = self.parameterAsFile(parameters, self.MDENOISE, context)
        iterations = self.parameterAsInt(parameters, self.N, context)
        threshold = self.parameterAsDouble(parameters, self.T, context)
        result = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        # debug
        # result_msg = 'RESULT:self.parameterAsOutputLayer %s->%s' % (type(result), result)
        # feedback.pushDebugInfo(result_msg)
        # params_msg = 'Parameters: %s->%s' % (type(parameters), parameters)
        # feedback.pushDebugInfo(params_msg)

        # -> RESULT:self.parameterAsOutputLayer 
        # C:/Users/GIS/AppData/Local/Temp/processing_ea33dbafdb70478382c4f0c3a361f362/5f414d505c9a4be396e7f6d4a11c4ab5/OUTPUT.tif
        # -> Parameters: {'CRS': 'EPSG:31466', 
        #                 'INPUT': <qgis._core.QgsRasterLayer object at 0x0000025F175AFCA8>, 
        #                 'MDENOISE': 'C:/Users/GIS/bin/MDenoise.exe', 
        #                 'N': 10.0, 
        #                 'OUTPUT': <QgsProcessingOutputLayerDefinition {
        #                       'sink':C:/Users/GIS/AppData/Local/Temp/processing_ea33dbafdb70478382c4f0c3a361f362/5f414d505c9a4be396e7f6d4a11c4ab5/OUTPUT.tif,
        #                       'createOptions': {'fileEncoding': 'System'}
        #                 }>, 
        #                 'PIXELSIZE': 30.0, 
        #                 'REPROJECT': False,
        #                 'T': 0.95}

        # file extension sensitive, use *.tif as file type, not gtiff or similar
        params = {
            'INPUT': input_evelation,
            'BAND': 1,
            'DISTANCE': 10,
            'ITERATIONS': 0,
            'NO_MASK': False,
            'OUTPUT': QgsProcessingUtils.generateTempFilename('filled.tif')
        }
        filled = self.run_process('gdal:fillnodata', params, context, feedback)
        self.file_exists(filled)

        # check if input_elevation data is in WGS84 or not
        # if it is reproject to a metric CRS
        to_translate = filled
        input_crs_id = input_evelation.crs().authid()
        feedback.pushDebugInfo('Input CRS %s' % input_crs_id)
        if input_crs_id == 'EPSG:4326':
            feedback.pushInfo('Reprojecting geographic data to a projected CRS')
            feedback.pushDebugInfo(filled)
            # TODO test if / for there is a file location somewhere ...
            # bilinear resampling for elevation data, data type float32
            params = {
                'INPUT': filled,
                'SOURCE_CRS': input_crs_id,
                'TARGET_CRS': project_crs.authid(),
                'RESAMPLING': 1,
                'TARGET_RESOLUTION': parameters[self.PIXELSIZE],
                'DATA_TYPE': 5,
                'MULTITHREADING': None,
                'OUTPUT': QgsProcessingUtils.generateTempFilename('warped.tif')
            }
            to_translate = self.run_process('gdal:warpreproject', params,
                                            context, feedback)
            self.file_exists(to_translate)

        # tranlate to AAIGrid
        # gdal:translate does only data type translation, so we use
        # gdal_translate with subprocess
        feedback.pushInfo('Converting to to AAIGrid format')
        output_aaigrid = QgsProcessingUtils.generateTempFilename('translated.asc')
        feedback.pushInfo('FILE: %s' % output_aaigrid)
        subprocess.run([
            'gdal_translate',
            '-of', 'AAIGrid',
            to_translate,
            output_aaigrid
        ])
        self.file_exists(output_aaigrid)

        # mdenoise
        feedback.pushInfo('Denoising data')
        denoised_grid = QgsProcessingUtils.generateTempFilename('denoised.asc')
        feedback.pushInfo('FILE: %s' % denoised_grid)
        subprocess.run([
            mdenoise_path,
            '-i', output_aaigrid,
            '-n', str(iterations),
            '-t', str(threshold),
            '-z',
            '-o', denoised_grid
        ])
        self.file_exists(denoised_grid)

        # retranslate to GeoTiff
        feedback.pushInfo('Converting to to GeoTIFF format')
        # output_gtiff = QgsProcessingUtils.generateTempFilename('denoised.tif')
        subprocess.run([
            'gdal_translate',
            '-of', 'GTiff',
            denoised_grid,
            result
        ])
        self.file_exists(result)

        return { self.OUTPUT: result }


    def run_process(self, name, params, context, feedback):
        """wrapper: run a QGIS processing framework process"""

        if feedback.isCanceled():
            exit()
        
        my_feedback = QgsProcessingFeedback()
        proc = processing.run(name, params, context=context,
                              feedback=feedback)
        return proc['OUTPUT']

    def file_exists(self, location):
        """test if a file location exists"""
        if not os.path.isfile(location):
            raise QgsProcessingException('File %s not found' % location)
        return True

