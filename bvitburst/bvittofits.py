#!/usr/bin/env python
################################# LICENSE ##################################
# Copyright (c) 2009, South African Astronomical Observatory (SAAO)        #
# All rights reserved.                                                     #
#                                                                          #
############################################################################
#
# Author                 Version      Date
# -----------------------------------------------
# Pim Schellart           0.1          24 Jan 2010 
# Amanda Gulbis (SAAO)    0.2          25 May 2010              
# Steve Crawford (SAAO)   0.3          26 Sep 2014
#
# Updates:
# ----------------------------------------------------------
# 0.2: Added start time of the bin to the header in DATE, TIME, MILLISEC
#      format.  This is required to use the output .fits files in bvitpreview
#      and bvitphot.
#
# 0.3: Updated to most recent version and removed pysalt aspects
#

"""Bvittofits is a tool to convert BVIT sparse tables to standard fits images.
"""

# Ensure Python 2.5 compatibility
from __future__ import with_statement

# Standard Python modules
import os
import datetime
import numpy as np
import pyfits

# Project modules
from astropy.io import fits

import pylab as pl

def bvittofits(hdu, outfile, tbin, reference=None, xbin=1,ybin=1, out32bit=True, skip_first=True, clobber=True):
    """Convert BVIT sparse tables to standard fits images.  This will convert the bvit data into
       images with each image having an exposure time given by tbin.   The  

       Parameters
       ----------
       hdu: `astropy.io.fits.hdu.hdulist.HDUList`
          Name of input file containing BVIT streaming data

       outfile: string
          Name of output to be written.

       reference: None or datetime
          Starting time for the frame
 
    """

    # Size of the image
    nx=4096
    ny=4096

    # Set dtype of output image which will determine it's dynamic range
    if out32bit:
        dtype='uint32'
    else:
        dtype='uint16'

    # Read header
    hdr=hdu[1].header

    # The BVIT headers are written before the data write to file.
    # So when files are aborted by hand, the file length does not
    # match the length stated in the header.
    # Here we check the file size and if it's smaller than the
    # value expected in the header, we rescale to avoid an error
    # when trying to read in the table.
                
    fsize=os.path.getsize(img)
                
    if fsize<hdr['NAXIS2']*10:
        hdr['NAXIS2']=fsize/10-11200

    # Read data
    x=np.array(hdu[1].data.field(0),dtype='int32')
    y=np.array(hdu[1].data.field(1),dtype='int32')
    counts=np.ones(len(x),dtype='int32')
    pulse=np.array(hdu[1].data.field(2),dtype='int32')
    time=np.array(hdu[1].data.field(3),dtype='float64')

    # Close file
    hdu.close()


    # Get delay in ms from end of writing previous file
    delay=int(hdr['DELAY'])


    #set start time
    if reference is None:
       # Construct a datetime object
       start=datetime.datetime(year=int(hdr['DATE'][0:4]),
                            month=int(hdr['DATE'][5:7]),
                            day=int(hdr['DATE'][8:10]),
                            hour=int(hdr['TIME'][0:2]),
                            minute=int(hdr['TIME'][3:5]),
                            second=int(hdr['TIME'][6:8]),
                            microsecond=int(hdr['MILLISEC'])*1000)

       reference=start

    else:
       # Correct for delay
       reference+=datetime.timedelta(microseconds=delay*1000)


    # Find one second pulses by looking for large (>1e5) jump
    jtime = time*0.0
    jtime[:-1] = time[1:]
    diff = time - jtime
    jump=1.0*(diff > 1e5)
    jumpsum = jump.cumsum()

    # Transform time to seconds and correct for jumps
    time=time*25e-9 + jumpsum  

    # now loop through the image starting with the first step in steps of 
    # tbin.
    ndu = fits.PrimaryHDU()
    ndu_list = fits.HDUList([ndu])
    for i, t in enumerate(np.arange(time.min(), time.max(), tbin)):
        mask = (time > t) * (time <= t+tbin)
        hist = np.histogram2d(x[mask], y[mask], bins=nx/xbin, range=((0,nx), (0,ny)))
        data = hist[0]
        ndu=fits.ImageHDU(data=data)
        imagetime = reference + datetime.timedelta(seconds=t)
        ndu.header['DATE-OBS'] = imagetime.strftime("%Y-%m-%d")
        ndu.header['TIME-OBS'] = imagetime.strftime("%H:%M:%S")
           ##ndu.writeto('out_%i.fits' % i)
        ndu_list.append(ndu)
        print t, t+tbin, data.sum()
        
    ndu_list.writeto(outfile, clobber=True)
    imagetime = reference + datetime.timedelta(seconds=time.max())
    return imagetime
 


if __name__=='__main__': 
   import sys
   img_list = sys.argv[1:]
   reference = None
   for img in img_list:
       hdu = fits.open(img, ignore_missing_end=True)
       reference = bvittofits(hdu, 't'+img, 1.0, reference=reference, xbin=8)
