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
    from . import Oscilloscope
except Exception:
    from oscilloscope import Oscilloscope

from time import sleep
from datetime import datetime
from quantiphy import Quantity
from sys import version_info
import pyvisa as visa

class MSOX3000(Oscilloscope):
    """Basic class for controlling and accessing a HP/Agilent/Keysight MSO-X/DSO-X 3000A Oscilloscope"""

    maxChannel = 4

    # Return list of ALL valid channel strings.
    #
    # NOTE: Currently, only valid values are a numerical string for
    # the analog channels, POD1 for digital channels 0-7 or POD2 for
    # digital channels 8-15
    chanAllValidList = [str(x) for x in range(1,maxChannel+1)]+['POD1','POD2']
        
    # Return list of valid analog channel strings.
    chanAnaValidList = [str(x) for x in range(1,maxChannel+1)]

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(MSOX3000, self).__init__(resource, maxChannel=MSOX3000.maxChannel, wait=wait)
        
    def setupAutoscaleOLD(self, channel=None):
        """ Autoscale desired channel, which is a string. channel can also be a list of multiple strings"""

        # If a channel value is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # Make channel a list even if it is a single value
        if type(self.channel) is not list:
            chanlist = [self.channel]
        else:
            chanlist = self.channel

        # chanlist cannot have more than 5 elements
        if (len(chanlist) > 5):
            raise ValueError('Too many channels for AUTOSCALE! Max is 5. Aborting')
            
        chanstr = ''
        for chan in chanlist:                        
            # Check channel value
            if (chan not in MSOX3000.chanAllValidList):
                raise ValueError('INVALID Channel Value for AUTOSCALE: {}  SKIPPING!'.format(chan))
            else:
                chanstr += ',' + self._channelStr(chan)

        # remove the leading ',' when creating the command string with '[1:]'        
        self._instWrite("AUToscale " + chanstr[1:])

    def annotateOLD(self, text, color=None, background='TRAN'):
        """ Add an annotation with text, color and background to screen

            text - text of annotation. Can include \n for newlines (two characters)

            color - string, one of {CH1 | CH2 | CH3 | CH4 | DIG | MATH | REF | MARK | WHIT | RED}

            background - string, one of TRAN - transparent, OPAQue or INVerted
        """

        if (color):
            self.annotateColor(color)

        # Add an annotation to the screen
        self._instWrite("DISPlay:ANN:BACKground {}".format(background))   # transparent background - can also be OPAQue or INVerted
        self._instWrite('DISPlay:ANN:TEXT "{}"'.format(text))
        self._instWrite("DISPlay:ANN ON")

    def annotateColorOLD(self, color):
        """ Change screen annotation color """

        ## NOTE: Only certain values are allowed:
        # {CH1 | CH2 | CH3 | CH4 | DIG | MATH | REF | MARK | WHIT | RED}
        #
        # The scope will respond with an error if an invalid color string is passed along
        self._instWrite("DISPlay:ANN:COLor {}".format(color))

    def annotateOffOLD(self):
        """ Turn off screen annotation """

        self._instWrite("DISPlay:ANN OFF")


    def polishOLD(self, value, measure=None):
        """ Using the QuantiPhy package, return a value that is in apparopriate Si units.

        If value is >= Oscilloscope.OverRange, then return the invalid string instead of a Quantity().

        If the measure string is None, then no units are used by the SI suffix is.

        """

        if (value >= Oscilloscope.OverRange):
            pol = '------'
        else:
            try:
                pol = Quantity(value, MSOX3000.measureTbl[measure][0])
            except KeyError:
                # If measure is None or does not exist
                pol = Quantity(value)

        return pol


    def measureStatistics(self):
        """Returns an array of dictionaries from the current statistics window.

        The definition of the returned dictionary can be easily gleaned
        from the code below.
        """

        # turn on the statistics display - these are specific to MSOX
        self._instWrite("SYSTem:MENU MEASure")
        self._instWrite("MEASure:STATistics:DISPlay ON")

        statFlat = super(MSOX3000, self)._measureStatistics()
        
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
    
    # =========================================================
    # Based on the screen image download example from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def hardcopy(self, filename):
        """ Download the screen image to the given filename. """

        self._instWrite("HARDcopy:INKSaver OFF")
        scrImage = self._instQueryIEEEBlock("DISPlay:DATA? PNG, COLor")

        # Save display data values to file.
        f = open(filename, "wb")
        f.write(scrImage)
        f.close()

    # =========================================================
    # Based on the Waveform data download example from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def waveform(self, filename, channel=None, points=None):
        """ Download the Waveform Data of a particular Channel and saved to the given filename as a CSV file. """

        DEBUG = False
        import csv

        # If a channel value is passed in, make it the
        # current channel
        if channel is not None and type(channel) is not list:
            self.channel = channel

        # Make sure channel is NOT a list
        if type(self.channel) is list or type(channel) is list:
            raise ValueError('Channel cannot be a list for WAVEFORM!')

        # Check channel value
        if (self.channel not in MSOX3000.chanAllValidList):
            raise ValueError('INVALID Channel Value for WAVEFORM: {}  SKIPPING!'.format(self.channel))            
            
        if self.channel.upper().startswith('POD'):
            pod = int(self.channel[-1])
        else:
            pod = None

        # Download waveform data.
        # Set the waveform points mode.
        self._instWrite("WAVeform:POINts:MODE MAX")
        if DEBUG:
            qresult = self._instQuery("WAVeform:POINts:MODE?")
            print( "Waveform points mode: {}".format(qresult) )

        # Set the number of waveform points to fetch, if it was passed in
        if (points is not None):
            self._instWrite("WAVeform:POINts {}".format(points))
            if DEBUG:
                qresult = self._instQuery("WAVeform:POINts?")
                print( "Waveform points available: {}".format(qresult) )

        # Set the waveform source.
        self._instWrite("WAVeform:SOURce {}".format(self._channelStr(self.channel)))
        if DEBUG:
            qresult = self._instQuery("WAVeform:SOURce?")
            print( "Waveform source: {}".format(qresult) )

        # Choose the format of the data returned:
        self._instWrite("WAVeform:FORMat BYTE")
        if DEBUG:
            print( "Waveform format: {}".format(self._instQuery("WAVeform:FORMat?")) )

        if DEBUG:
            # Display the waveform settings from preamble:
            wav_form_dict = {
                0 : "BYTE",
                1 : "WORD",
                4 : "ASCii", }

            acq_type_dict = {
                0 : "NORMal",
                1 : "PEAK",
                2 : "AVERage",
                3 : "HRESolution",
            }

            (
                wav_form_f,
                acq_type_f,
                wfmpts_f,
                avgcnt_f,
                x_increment,
                x_origin,
                x_reference_f,
                y_increment,
                y_origin,
                y_reference_f
            ) = self._instQueryNumbers("WAVeform:PREamble?")

            ## convert the numbers that are meant to be integers
            (
                wav_form,
                acq_type,
                wfmpts,
                avgcnt,
                x_reference,
                y_reference
            ) = list(map(int,         (
                wav_form_f,
                acq_type_f,
                wfmpts_f,
                avgcnt_f,
                x_reference_f,
                y_reference_f
            )))


            print( "Waveform format: {}".format(wav_form_dict[(wav_form)]) )
            print( "Acquire type: {}".format(acq_type_dict[(acq_type)]) )
            print( "Waveform points desired: {:d}".format((wfmpts)) )
            print( "Waveform average count: {:d}".format((avgcnt)) )
            print( "Waveform X increment: {:1.12f}".format(x_increment) )
            print( "Waveform X origin: {:1.9f}".format(x_origin) )
            print( "Waveform X reference: {:d}".format((x_reference)) ) # Always 0.
            print( "Waveform Y increment: {:f}".format(y_increment) )
            print( "Waveform Y origin: {:f}".format(y_origin) )
            print( "Waveform Y reference: {:d}".format((y_reference)) ) # Always 125.

        # Get numeric values for later calculations.
        x_increment = self._instQueryNumber("WAVeform:XINCrement?")
        x_origin = self._instQueryNumber("WAVeform:XORigin?")
        y_increment = self._instQueryNumber("WAVeform:YINCrement?")
        y_origin = self._instQueryNumber("WAVeform:YORigin?")
        y_reference = self._instQueryNumber("WAVeform:YREFerence?")

        # Get the waveform data.
        waveform_data = self._instQueryIEEEBlock("WAVeform:DATA?")

        if (version_info < (3,)):
            ## If PYTHON 2, waveform_data will be a string and needs to be converted into a list of integers
            data_bytes = [ord(x) for x in waveform_data]
        else:
            ## If PYTHON 3, waveform_data is already in the correct format
            data_bytes = waveform_data

        nLength = len(data_bytes)
        if (DEBUG):
            print( "Number of data values: {:d}".format(nLength) )

        # Open file for output.
        myFile = open(filename, 'w')
        with myFile:
            writer = csv.writer(myFile, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
            if pod:
                writer.writerow(['Time (s)'] + ['D{}'.format((pod-1) * 8 + ch) for ch in range(8)])
            else:
                writer.writerow(['Time (s)', 'Voltage (V)'])

            # Output waveform data in CSV format.
            for i in range(0, nLength - 1):
                time_val = x_origin + (i * x_increment)
                if pod:
                    writer.writerow([time_val] + [(data_bytes[i] >> ch) & 1 for ch in range(8)])
                else:
                    voltage = (data_bytes[i] - y_reference) * y_increment + y_origin
                    writer.writerow([time_val, voltage])

        if (DEBUG):
            print( "Waveform format BYTE data written to {}.".format(filename) )

        # return number of entries written
        return nLength

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
            print('{: <24} {:>12.6}'.format(meas,instr.polish(MSOX3000.measureTbl[meas][1](instr), meas)))

    ## turn off the channel
    instr.outputOff()

    ## return to LOCAL mode
    instr.setLocal()

    instr.close()
