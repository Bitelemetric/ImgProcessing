#%% UPLOAD FILES 
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os,glob
import math
import micasense.metadata as metadata
from micasense.image import Image
from micasense.panel import Panel
import micasense.plotutils as plotutils
import micasense.utils as msutils
import re

panelCalibration = { 
    "Blue": 0.5105, 
    "Green": 0.50993, 
    "Red": 0.50921, 
    "Red edge": 0.50889, 
    "NIR": 0.50807 
}

def get_num_per_band(band):
    if band == 'Red':
        return 3
    elif band == 'Green':
        return 2
    elif band == 'Blue':
        return 1
    elif band == 'NIR':
        return 4
    else:
        return 5


def get_meta(imageName):
    imageRaw=plt.imread(imageName)
    exiftoolPath = None
    if os.name == 'nt':
        exiftoolPath = os.environ.get('exiftoolpath')
    # get image metadata
    meta = metadata.Metadata(imageName, exiftoolPath=exiftoolPath)
    cameraMake = meta.get_item('EXIF:Make')
    cameraModel = meta.get_item('EXIF:Model')
    firmwareVersion = meta.get_item('EXIF:Software')
    bandName = meta.get_item('XMP:BandName')
    print('{0} {1} firmware version: {2}'.format(cameraMake, 
                                                cameraModel, 
                                                firmwareVersion))
    print('Exposure Time: {0} seconds'.format(meta.get_item('EXIF:ExposureTime')))
    print('Imager Gain: {0}'.format(meta.get_item('EXIF:ISOSpeed')/100.0))
    print('Size: {0}x{1} pixels'.format(meta.get_item('EXIF:ImageWidth'),meta.get_item('EXIF:ImageHeight')))
    print('Band Name: {0}'.format(bandName))
    print('Center Wavelength: {0} nm'.format(meta.get_item('XMP:CentralWavelength')))
    print('Bandwidth: {0} nm'.format(meta.get_item('XMP:WavelengthFWHM')))
    print('Capture ID: {0}'.format(meta.get_item('XMP:CaptureId')))
    print('Flight ID: {0}'.format(meta.get_item('XMP:FlightId')))
    print('Focal Length: {0}'.format(meta.get_item('XMP:FocalLength')))

    print('****************** get meta ********************')
    check_panel(imageName,meta,imageRaw,bandName)

def check_panel(imageName,meta,imageRaw,bandName):
    imageName = glob.glob(imageName)[0]
    img = Image(imageName)
    panel = Panel(img)
    if not panel.panel_detected():
        raise IOError("Panel Not Detected! Check your installation of pyzbar")
    else:
        panel.plot(figsize=(9,9))
    radianceImage, L, V, R = msutils.raw_image_to_radiance(meta, imageRaw)

    markedImg = radianceImage.copy()
    ulx = 660 # upper left column (x coordinate) of panel area
    uly = 490 # upper left row (y coordinate) of panel area
    lrx = 840 # lower right column (x coordinate) of panel area
    lry = 670 # lower right row (y coordinate) of panel area
    cv2.rectangle(markedImg,(ulx,uly),(lrx,lry),(0,255,0),3)
    panelRegion = radianceImage[uly:lry, ulx:lrx]
    #plotutils.plotwithcolorbar(markedImg, 'Panel region in radiance image')
    meanRadiance = panelRegion.mean()
    print('Mean Radiance in panel region: {:1.3f} W/m^2/nm/sr'.format(meanRadiance))
    print('****************** panel ********************')
    radiance_img(meanRadiance,bandName,meta)

def radiance_img(meanRadiance,bandName,meta):
    
    panelReflectance = panelCalibration[bandName]
    radianceToReflectance = panelReflectance / meanRadiance
    num_band = get_num_per_band(bandName)
    regex = '.*'+str(num_band)+'.tif$'
    print('**************  '+bandName+ '*************************')

    dir = os.listdir(imagePath)
    for i in range(len(dir)):
        if re.search(regex,dir[i]) and not('0000' in dir[i]):
            flightImageName = os.path.join(imagePath,dir[i])
            flightImageRaw=plt.imread(flightImageName)
            flightRadianceImage, _, _, _ = msutils.raw_image_to_radiance(meta, flightImageRaw)
            flightReflectanceImage = flightRadianceImage * radianceToReflectance
            flightUndistortedReflectance = msutils.correct_lens_distortion(meta, flightReflectanceImage)
            print(flightUndistortedReflectance.shape)
            #plotutils.plotwithcolorbar(flightUndistortedReflectance, 'Reflectance converted and undistorted image')
            plt.imsave('Result '+dir[i].replace('.tif','')+' '+bandName,flightUndistortedReflectance,format='png', cmap='gray')

imagePath = os.path.join('.','data','DOLE','000')
for i in range(5):
    img_n = 'IMG_0000_'+str(i+1)+'.tif'
    try:
        imageName = os.path.join(imagePath,img_n)
        get_meta(imageName)
        print('*'*50)
    except:
        print('No exit photo ',str(i+1),' whit reflacnce panel')
        raise ValueError

