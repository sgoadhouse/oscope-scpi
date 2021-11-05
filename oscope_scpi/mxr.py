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
#  Control of Keysight MXR series Oscilloscopes with PyVISA
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

try:
    from .keysight import Keysight
except Exception:
    sys.path.append(os.getcwd())
    from keysight import Keysight

class MXR(Keysight):
    """Basic class for controlling and accessing a Keysight MXR Series Oscilloscope"""

    def __init__(self, resource, maxChannel=4, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        maxChannel - number of channels of this oscilloscope
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(MXR, self).__init__(resource, maxChannel, wait)

        # Add Differential Channels
        self._chanAllValidList += ['DIFF'+str(x) for x in range(1,self._max_chan+1)]
        
        # Add Common-Mode Channels
        self._chanAllValidList += ['COMM'+str(x) for x in range(1,self._max_chan+1)]
        
        # Add Functions FUNCx (x is 1-16)
        self._chanAllValidList += ['FUNC'+str(x) for x in range(1,17)]
        
        # Add HIST (Histogram) to list of ALL valid channel strings.
        self._chanAllValidList += ['HIST']

        # Add Wave Memory (document says this is 1-4 but my MXR scope has 8 memory slots)
        self._chanAllValidList += ['WMEM'+str(x) for x in range(1,9)]
        
        # Add digital BUSb (b is 1-4), POD1, POD2 and PODALL
        # NOTE: POD1 is for digital channels 0-7 or POD2 for digital
        # channels 8-15, PODALL is for all 16.
        self._chanAllValidList += ['BUS'+str(x) for x in range(1,5)] + ['POD'+str(x) for x in range(1,3)] + ['PODALL']

        # Give the Series a name
        self._series = 'MXR'

    def measureStatistics(self):
        """Returns an array of dictionaries from the current statistics window.

        The definition of the returned dictionary can be easily gleaned
        from the code below.
        """

        statFlat = super(MXR, self)._measureStatistics()
        
        # convert the flat list into a two-dimentional matrix with seven columns per row
        cols = 7
        if ((len(statFlat) % cols != 0)):
            print('Unexpected response. Oscilloscope may not have any measurements enabled.')
            statMat = []
        else:
            statMat = [statFlat[i:i+cols] for i in range(0,len(statFlat),cols)]
        
        # convert each row into a dictionary, while converting text strings into numbers
        stats = []
        for stat in statMat:
            stats.append({'label':stat[0],
                          'CURR':float(stat[1]),     # Current Value
                          'MIN':float(stat[2]),      # Minimum Value
                          'MAX':float(stat[3]),      # Maximum Value
                          'MEAN':float(stat[4]),     # Average/Mean Value
                          'STDD':float(stat[5]),     # Standard Deviation
                          'COUN':int(float(stat[6])) # Count of measurements
                          })

        # return the result in an array of dictionaries
        return stats

    def setupAutoscale(self, channel=None):
        """ Autoscale desired channel, which is a string. channel can also be a list of multiple strings"""

        # MXR allows autoscale to either STACk, SEParate or OVERlay channels
        #
        # STACk puts them all in the same grid which reduces ADC
        # accuracy where SEParate puts them at max ADC accuracy but in
        # seperate grids.
        #@@@#self._instWrite("AUToscale:PLACement STACk")
        self._instWrite("AUToscale:PLACement SEParate")

        super(MXR, self).setupAutoscale(channel)

        
class MXRxx8A(MXR):
    """Child class of Keysight for controlling and accessing a Keysight MXRxx8A 8-Channel Oscilloscope"""

    maxChannel = 8

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(MXRxx8A, self).__init__(resource, maxChannel=MXRxx8A.maxChannel, wait=wait)

class MXRxx4A(MXR):
    """Child class of Keysight for controlling and accessing a Keysight MXRxx4A 4-Channel Oscilloscope"""

    maxChannel = 4

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(MXRxx4A, self).__init__(resource, maxChannel=MXRxx4A.maxChannel, wait=wait)


