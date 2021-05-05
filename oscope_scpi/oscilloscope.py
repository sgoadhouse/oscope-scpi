#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2018,2019,2020,2021, Stephen Goadhouse <sgoadhouse@virginia.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#-------------------------------------------------------------------------------
#  Control of Oscilloscopes with PyVISA and SCPI command set. This started as
#  specific code for the HP/Agilent/Keysight MSO-X/DSO-X 3000A Oscilloscope and
#  has been made more generic to be used with Agilent UXR and MXR Oscilloscopes.
#  The hope is that these commands in this package are generic enough to be
#  used with other brands but may need to make this an Agilent specific
#  package in the future if find that not to be true.
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from . import SCPI
except Exception:
    from scpi import SCPI

from time import sleep
from datetime import datetime
from quantiphy import Quantity
from sys import version_info
import pyvisa as visa
import numpy as np
import csv

class Oscilloscope(SCPI):
    """Base class for controlling and accessing an Oscilloscope with PyVISA and SCPI commands"""

    def __init__(self, resource, maxChannel=1, wait=0,
                     cmd_prefix = ':',
                     read_strip = '\n',
                     read_termination = '',
                     write_termination = '\n'):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        maxChannel - number of channels
        wait       - float that gives the default number of seconds to wait after sending each command
        cmd_prefix - optional command prefix (ie. some instruments require a ':' prefix)
        read_strip        - optional read_strip parameter used to strip any returned termination characters
        read_termination  - optional read_termination parameter to pass to open_resource()
        write_termination - optional write_termination parameter to pass to open_resource()
        """

        # NOTE: maxChannel is accessible in this package via parent as: self._max_chan
        super(Oscilloscope, self).__init__(resource, max_chan=maxChannel, wait=wait,
                                           cmd_prefix=cmd_prefix,
                                           read_strip=read_strip,
                                           read_termination=read_termination,
                                           write_termination=write_termination
        )

        # Return list of valid analog channel strings.
        self._chanAnaValidList = [str(x) for x in range(1,self._max_chan+1)]

        # list of ALL valid channel strings.
        #
        # NOTE: Currently, only valid values are a numerical string for
        # the analog channels, POD1 for digital channels 0-7 or POD2 for
        # digital channels 8-15
        self._chanAllValidList = self._chanAnaValidList + [str(x) for x in ['POD1','POD2']]
        
    @property
    def chanAnaValidList(self):
        return self._chanAnaValidList

    @property
    def chanAllValidList(self):
        return self._chanAllValidList
    
    # =========================================================
    # Based on the save oscilloscope setup example from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def setupSave(self, filename):
        """ Fetch the oscilloscope setup and save to a file with given filename. """

        oscopeSetup = self._instQueryIEEEBlock("SYSTem:SETup?")

        # Save setup to file.
        f = open(filename, "wb")
        f.write(oscopeSetup)
        f.close()

        #print('Oscilloscope Setup bytes saved: {} to "{}"'.format(len(oscopeSetup),filename))

        # Return number of bytes saved to file
        return len(oscopeSetup)

    # =========================================================
    # Based on the loading a previous setup example from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def setupLoad(self, filename):
        """ Restore the oscilloscope setup from file with given filename. """

        # Load setup from file.
        f = open(filename, "rb")
        oscopeSetup = f.read()
        f.close()

        #print('Oscilloscope Setup bytes loaded: {} from "{}"'.format(len(oscopeSetup),filename))

        self._instWriteIEEEBlock("SYSTem:SETup ", oscopeSetup)

        # Return number of bytes saved to file
        return len(oscopeSetup)


    def autoscale(self):
        """ Autoscale Oscilloscope"""

        self._instWrite("AUToscale")

    
    def waveform(self, filename, channel=None, points=None):
        """Download waveform data of a selected channel into a csv file.

        NOTE: This is a LEGACY function to prevent breaking API but it
        is deprecated so use above waveform functions instead.

        NOTE: Now that newer oscilloscopes have very large data
        downloads, csv file format is not a good format for storing
        because the files are so large that the convenience of csv
        files has diminishing returns. They are too large for Excel to
        load and are only useful from a scripting system like Python
        or MATLAB or Root. See waveformSaveNPZ() for a better option.

        filename - base filename to store the data

        channel  - channel, as string, to be measured - set to None to use the default channel

        points   - number of points to capture - if None, captures all available points
                   for newer devices, the captured points are centered around the center of the display

        """

        # Acquire the data (also sets self.channel)
        (x, y, header, meta) = self.waveformData(channel, points)

        # Save to CSV file
        return self.waveformSaveCSV(filename, x, y, header)
    
    
    def waveformSaveCSV(self, filename, x, y, header=None, meta=None):
        """
        filename - base filename to store the data

        x        - time data to write in first column

        y        - vertical data: expected to be a list of columns to write and can be any number of columns

        header   - a list of header strings, one for each column of data - set to None for no header

        meta     - a list of meta data for waveform data - optional and not used by this function - only here to be like other waveformSave functions

        """

        nLength = len(x)

        print('Writing data to CSV file. Please wait...')
        
        # Save waveform data values to CSV file.
        # Determine iterator
        if (nLength == len(y)):
            # Simply single column of y data
            it = zip(x,y)
        else:
            # Multiple columns in y, so break them out
            it = zip(x,*y)
            
        # Open file for output. Only output x & y for simplicity. User
        # will have to copy paste the meta data printed to the
        # terminal
        myFile = open(filename, 'w')
        with myFile:
            writer = csv.writer(myFile, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
            if header is not None:
                writer.writerow(header)
                
            writer.writerows(it)
                    
        # return number of entries written
        return nLength

    
    def waveformSaveNPZ(self, filename, x, y, header=None, meta=None):
        """
        filename - base filename to store the data

        x        - time data to write in first column

        y        - vertical data: expected to be a list of columns to write and can be any number of columns

        header   - a list of header strings, one for each column of data - set to None for no header

        meta     - a list of meta data for waveform data

        A NPZ file is an uncompressed zip file of the arrays x, y and optionally header and meta if supplied. 
        To load and use the data from python:

        import numpy as np
        header=None
        meta=None
        with np.load(filename) as data:
            x = data['x']
            y = data['y']
            if 'header' in data.files:
                header = data['header']
            if 'meta' in data.files:
                meta = data['meta']

        """

        nLength = len(x)

        print('Writing data to Numpy NPZ file. Please wait...')

        arrays = {'x': x, 'y': y}
        if (header is not None):
            arrays['header']=header
        if (meta is not None):
            arrays['meta']=meta
        np.savez(filename, **arrays)
        
        # return number of entries written
        return nLength

    
    ## This is a dictionary of measurement labels with their units. It
    ## is blank here and it is expected that this get defined by child
    ## classes.
    _measureTbl = { }
    

    def polish(self, value, measure=None):
        """ Using the QuantiPhy package, return a value that is in apparopriate Si units.

        If value is >= self.OverRange, then return the invalid string instead of a Quantity().

        If the measure string is None, then no units are used by the SI suffix is.

        """

        if (value >= self.OverRange):
            pol = '------'
        else:
            try:
                pol = Quantity(value, self._measureTbl[measure][0])
            except KeyError:
                # If measure is None or does not exist
                pol = Quantity(value)

        return pol


