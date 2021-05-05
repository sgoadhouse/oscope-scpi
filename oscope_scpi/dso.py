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
#  Control of HP/Agilent/Keysight MSO-X/DSO-X 3000A Oscilloscope with PyVISA
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from . import Keysight
except Exception:
    from keysight import Keysight

class DSOX(Keysight):
    """Basic class for controlling and accessing a HP/Agilent/Keysight Generic DSO-X Oscilloscope"""

    def __init__(self, resource, maxChannel=2, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        maxChannel - number of channels of this oscilloscope
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(DSOX, self).__init__(resource, maxChannel, wait)
        
    def measureStatistics(self):
        """Returns an array of dictionaries from the current statistics window.

        The definition of the returned dictionary can be easily gleaned
        from the code below.
        """

        # turn on the statistics display - these are specific to MSOX/DSOX
        self._instWrite("SYSTem:MENU MEASure")
        self._instWrite("MEASure:STATistics:DISPlay ON")

        statFlat = super(DSOX, self)._measureStatistics()
        
        # convert the flat list into a two-dimentional matrix with seven columns per row
        statMat = [statFlat[i:i+7] for i in range(0,len(statFlat),7)]
        
        # convert each row into a dictionary, while converting text strings into numbers
        stats = []
        for stat in statMat:
            stats.append({'label':stat[0],
                          'CURR':float(stat[1]),   # Current Value
                          'MIN':float(stat[2]),    # Minimum Value
                          'MAX':float(stat[3]),    # Maximum Value
                          'MEAN':float(stat[4]),   # Average/Mean Value
                          'STDD':float(stat[5]),   # Standard Deviation
                          'COUN':int(stat[6])      # Count of measurements
                          })

        # return the result in an array of dictionaries
        return stats

class MSOX(DSOX):
    """Basic class for controlling and accessing a HP/Agilent/Keysight Generic MSO-X Oscilloscope"""

    def __init__(self, resource, maxChannel=2, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        maxChannel - number of channels of this oscilloscope
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(MSOX, self).__init__(resource, maxChannel, wait)
        
class DSOX3xx2A(DSOX):
    """Basic class for controlling and accessing a HP/Agilent/Keysight DSO-X 3xx2A 2-Channel Oscilloscope"""

    maxChannel = 2

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(DSOX3xx2A, self).__init__(resource, maxChannel=DSOX3xx2A.maxChannel, wait=wait)
        
class MSOX3xx2A(MSOX):
    """Basic class for controlling and accessing a HP/Agilent/Keysight MSO-X 3xx2A 2-Channel Oscilloscope"""

    maxChannel = 2

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(MSOX3xx2A, self).__init__(resource, maxChannel=MSOX3xx2A.maxChannel, wait=wait)

class DSOX3xx4A(DSOX):
    """Basic class for controlling and accessing a HP/Agilent/Keysight DSO-X 3xx4A 4-Channel Oscilloscope"""

    maxChannel = 4

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(DSOX3xx4A, self).__init__(resource, maxChannel=DSOX3xx4A.maxChannel, wait=wait)
        
class MSOX3xx4A(MSOX):
    """Basic class for controlling and accessing a HP/Agilent/Keysight MSO-X 3xx4A 4-Channel Oscilloscope"""

    maxChannel = 4

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(MSOX3xx4A, self).__init__(resource, maxChannel=MSOX3xx4A.maxChannel, wait=wait)
        
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a MSO-X/DSO-X 3000 Oscilloscope')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from os import environ
    resource = environ.get('MSOX3000_IP', 'TCPIP0::172.16.2.13::INSTR')
    instr = MSOX3000(resource)
    instr.open()

    # set the channel (can pass channel to each method or just set it
    # once and it becomes the default for all following calls)
    instr.channel = str(args.chan)

    if not instr.isOutputOn():
        instr.outputOn()

    # Install measurements to display in statistics display and also
    # return their current values
    print('Ch. {} Settings: {:6.4e} V  PW {:6.4e} s\n'.
              format(instr.channel, instr.measureVoltAverage(install=True),
                         instr.measurePosPulseWidth(install=True)))

    # Add an annotation to the screen before hardcopy
    instr._instWrite("DISPlay:ANN ON")
    instr._instWrite('DISPlay:ANN:TEXT "{}\\n{} {}"'.format('Example of Annotation','for Channel',instr.channel))
    instr._instWrite("DISPlay:ANN:BACKground TRAN")   # transparent background - can also be OPAQue or INVerted
    instr._instWrite("DISPlay:ANN:COLor CH{}".format(instr.channel))

    # Change label of the channel to "MySig"
    instr._instWrite('CHAN{}:LABel "MySig"'.format(instr.channel))
    instr._instWrite('DISPlay:LABel ON')

    # Make sure the statistics display is showing
    instr._instWrite("SYSTem:MENU MEASure")
    instr._instWrite("MEASure:STATistics:DISPlay ON")

    ## Save a hardcopy of the screen
    instr.hardcopy('outfile.png')

    # Change label back to the default
    instr._instWrite('CHAN{}:LABel "{}"'.format(instr.channel, instr.channel))
    instr._instWrite('DISPlay:LABel OFF')

    # Turn off the annotation
    instr._instWrite("DISPlay:ANN OFF")

    ## Read ALL available measurements from channel, without installing
    ## to statistics display, with units
    print('\nMeasurements for Ch. {}:'.format(instr.channel))
    measurements = ['Bit Rate',
                    'Burst Width',
                    'Counter Freq',
                    'Frequency',
                    'Period',
                    'Duty',
                    'Neg Duty',
                    '+ Width',
                    '- Width',
                    'Rise Time',
                    'Num Rising',
                    'Num Pos Pulses',
                    'Fall Time',
                    'Num Falling',
                    'Num Neg Pulses',
                    'Overshoot',
                    'Preshoot',
                    '',
                    'Amplitude',
                    'Pk-Pk',
                    'Top',
                    'Base',
                    'Maximum',
                    'Minimum',
                    'Average - Full Screen',
                    'RMS - Full Screen',
                    ]
    for meas in measurements:
        if (meas == ''):
            # use a blank string to put in an extra line
            print()
        else:
            # using MSOX3000.measureTbl[] dictionary, call the
            # appropriate method to read the measurement. Also, using
            # the same measurement name, pass it to the polish() method
            # to format the data with units and SI suffix.
            print('{: <24} {:>12.6}'.format(meas,instr.polish(instr.measureTblCall(meas), meas)))

    ## turn off the channel
    instr.outputOff()

    ## return to LOCAL mode
    instr.setLocal()

    instr.close()
