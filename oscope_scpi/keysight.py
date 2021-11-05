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
#  HP/Agilent/Keysight specific SCPI commands
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

try:
    from .oscilloscope import Oscilloscope
except Exception:
    sys.path.append(os.getcwd())
    from oscilloscope import Oscilloscope
    
from time import sleep
from datetime import datetime
from sys import version_info
import numpy as np
import struct

class Keysight(Oscilloscope):
    """Child class of Oscilloscope for controlling and accessing a HP/Agilent/Keysight Oscilloscope with PyVISA and SCPI commands"""

    def __init__(self, resource, maxChannel=2, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        maxChannel - number of channels of this oscilloscope
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        # NOTE: maxChannel is accessible in this package via parent as: self._max_chan
        super(Keysight, self).__init__(resource, maxChannel, wait,
                                       cmd_prefix=':',
                                       read_strip='\n',
                                       read_termination='',
                                       write_termination='\n'
        )

        # Return list of valid analog channel strings. These are numbers.
        self._chanAnaValidList = [str(x) for x in range(1,self._max_chan+1)]

        # list of ALL valid channel strings.
        #
        # NOTE: Currently, only valid common values are a
        # CHAN+numerical string for the analog channels
        self._chanAllValidList = [self.channelStr(x) for x in range(1,self._max_chan+1)]

        # Give the Series a name
        self._series = 'KEYSIGHT'

        # Set the highest version number used to determine if SCPI
        # firmware on oscilloscope expects the LEGACY commands. Any
        # version number returned by the IDN string above this number
        # will use the modern, non-legacy commands.
        #
        # Cannot find a definitive Keysight document that indicates
        # the versions where non-legacy begins. The Legacy
        # oscilloscopes like MSO-X 3034A are up to v2.65 now and it
        # appears that somewhere around 3.00 is where the major change
        # happened. So set _versionLegacy to 2.99 in hopes that this
        # will serve for future oscilloscope firmware updates.
        self._versionLegacy = 2.99
        
        # This will store annotation text if that feature is used
        self._annotationText = ''
        self._annotationColor = 'ch1' # default to Channel 1 color


    def modeRun(self):
        """ Set Oscilloscope to RUN Mode """
        # found that with UXR it helped to wait a little to make sure mode switch happens
        sleep(0.1)
        self._instWrite('RUN')

    def modeStop(self):
        """ Set Oscilloscope to STOP Mode """
        # found that with UXR it helped to wait a little to make sure mode switch happens
        sleep(0.1)
        self._instWrite('STOP')

    def modeSingle(self):
        """ Set Oscilloscope to SINGLE Mode """
        # found that with UXR it helped to wait a little to make sure mode switch happens
        sleep(0.1)
        self._instWrite('SINGLE')

        
    def annotate(self, text, color=None, background='TRAN'):
        """ Add an annotation with text, color and background to screen

            text - text of annotation. Can include \n for newlines (two characters)

            color - see annotateColor for possible strings

            background - string, one of TRAN - transparent, OPAQue or INVerted (ignored unless sw version <= self._versionLegacy)
        """

        # Save annotation text because may need it if change color
        self._annotationText = text

        # Next, if <= self._versionLegacy, set color first. if > self._versionLegacy,
        # annotateColor() also displays the annotation. Also handles
        # case of color is None.
        self.annotateColor(color)
        
        if (self._version <= self._versionLegacy):
            # Legacy commands for annotations
            #
            # Add an annotation to the screen
            self._instWrite("DISPlay:ANN:BACKground {}".format(background))   # transparent background - can also be OPAQue or INVerted
            self._instWrite('DISPlay:ANN:TEXT "{}"'.format(text))
            self._instWrite("DISPlay:ANN ON")
            
    ## Use to convert legacy color names
    _colorNameOldtoNew = {
        'ch1':    'CHAN1',
        'ch2':    'CHAN2',
        'ch3':    'CHAN3',
        'ch4':    'CHAN4',
        'ch5':    'CHAN5',
        'ch6':    'CHAN6',
        'ch7':    'CHAN7',
        'ch8':    'CHAN8',
        'dig':    'DCH',
        'math':   'FUNC1',
        'ref':    'WMEM',
        'marker': 'MARK',
        'white':  'FUNC14',         # closest match
        'red':    'FUNC12'          # no good match
    }
            
    def annotateColor(self, color):
        """ Change screen annotation color """

        ## NOTE: Only certain values are allowed. These are legacy names (<= self._versionLegacy)
        # {CH1 | CH2 | CH3 | CH4 | DIG | MATH | REF | MARK | WHIT | RED}
        #
        # The scope will respond with an error if an invalid color string is passed along
        #
        # If > self._versionLegacy, will translate color names
        
        if (self._version > self._versionLegacy):
            if (color is not None):
                # save color
                self._annotationColor = color

            # Place Bookmark in top left of grid
            self._instWrite("DISPlay:BOOKmark1:XPOSition 0.015")
            self._instWrite("DISPlay:BOOKmark1:YPOSition 0.06")

            #@@@#print("Current Location of Bookmark 1: {},{}".format(
            #@@@#    self._instQuery("DISPlay:BOOKmark1:XPOSition?"), self._instQuery("DISPlay:BOOKmark1:YPOSition?")))
            
            # Always use the first Bookmark to implement similar annotation to 3000 series
            self._instWrite('DISPlay:BOOKmark1:SET NONE,\"{}\",{},\"{}\"'.format(
                self._annotationText,
                self._colorNameOldtoNew[self._annotationColor],
                self._annotationText))
            
        elif (color is not None):
            # If legacy and color is None, ignore
            self._instWrite("DISPlay:ANN:COLor {}".format(color))

    def annotateOff(self):
        """ Turn off screen annotation """

        if (self._version > self._versionLegacy):
            self._instWrite("DISPlay:BOOKmark1:DELete")
        else:
            self._instWrite("DISPlay:ANN OFF")
        

    def channelLabel(self, label, channel=None):
        """ Add a label to selected channel (or default one if None)

            label - text of label
        """

        # If a channel value is passed in, make it the
        # current channel
        if channel is not None and type(channel) is not list:
            self.channel = channel

        # Make sure channel is NOT a list
        if type(self.channel) is list or type(channel) is list:
            raise ValueError('Channel cannot be a list for CHANNEL LABEL!')

        # Check channel value
        if (self.channel not in self._chanAnaValidList):
            raise ValueError('INVALID Channel Value for CHANNEL LABEL: {}  SKIPPING!'.format(self.channel))
            
        self._instWrite('CHAN{}:LABel "{}"'.format(self.channel, label))
        self._instWrite('DISPlay:LABel ON')

    def channelLabelOff(self):
        """ Turn off channel labels """

        self._instWrite('DISPlay:LABel OFF')


    def setupAutoscale(self, channel=None):
        """ Autoscale desired channel, which is a string. channel can also be a list of multiple strings"""

        # If a channel value is passed in, make it the
        # current channel and process the list, viewing only these channels
        if channel is not None:
            self.channel = channel

            # Make channel a list even if it is a single value
            if type(self.channel) is not list:
                chanlist = [self.channel]
            else:
                chanlist = self.channel

            # Turn off all channels
            self.outputOffAll()
            
            # Turn on selected channels
            chanstr = ''
            for chan in chanlist:                        
                # Check channel value
                if (chan not in self._chanAllValidList):
                    print('INVALID Channel Value for AUTOSCALE: {}  SKIPPING!'.format(chan))
                else:
                    self._instWrite("VIEW {}".format(chan))
                    
        # Make sure Autoscale is only autoscaling displayed channels
        #@@@#self._instWrite("AUToscale:CHANnels DISPlayed")

        # Issue autoscale
        self.autoscale()

    # =========================================================
    # Based on the screen image download example from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def hardcopy(self, filename):
        """ Download the screen image to the given filename. """

        if (self._version > self._versionLegacy):
            para = 'PNG,SCReen,ON,NORMal'
        else:
            self._instWrite("HARDcopy:INKSaver OFF")
            para = 'PNG,COLor'

        scrImage = self._instQueryIEEEBlock("DISPlay:DATA? "+para)

        # Save display data values to file.
        f = open(filename, "wb")
        f.write(scrImage)
        f.close()


    # =========================================================
    # Based on the Waveform data download example from the Keysight
    # Infiniium MXR/EXR-Series Oscilloscope Programmer's Guide and
    # modified to work within this class ...
    # =========================================================
    def _waveformDataNew(self, channel, points=None):
        """ Download the Waveform Data of a particular Channel and return it. """

        DEBUG = True
        
        # Download waveform data.
        # --------------------------------------------------------

        # Create array for meta data
        meta = []
        
        # Set the waveform source.
        self._instWrite("WAVeform:SOURce {}".format(self.channelStr(channel)))
        wav_source = self._instQuery("WAVeform:SOURce?")

        # Get the waveform view.
        wav_view = self._instQuery("WAVeform:VIEW?")
        
        # Choose the format of the data returned.
        if (channel.startswith('HIST')):
            # Histogram so request BINary forma
            self._instWrite("WAVeform:FORMat BINary")
        elif(channel == 'POD1' or channel == 'POD2'):
            # For POD1 and POD2, they really are only BYTE values
            # although WORD will work but the MSB will always be
            # 0. Setting this to BYTE here makes later code work out
            # by setting bits to 8 and npTyp to np.int8.
            self._instWrite("WAVeform:FORMat BYTE")
        else:
            # For analog data, WORD is the best and has the highest
            # accuracy (even better than FLOat). WORD works for most
            # of the other channel types as well.
            self._instWrite("WAVeform:FORMat WORD")
        
        # Make sure byte order is set to be compatible with endian-ness of system
        if (sys.byteorder == 'big'):
            bo = 'MSBFirst'
        else:
            bo = 'LSBFirst'
            
        self._instWrite("WAVeform:BYTeorder " + bo)

        #@@@#print('Waveform Format: ' + self._instQuery('WAV:FORM?'))
        
        # Display the waveform settings from preamble:
        wav_form_dict = {
            0 : "ASCii",
            1 : "BYTE",
            2 : "WORD",
            3 : "LONG",
            4 : "LONGLONG",
            5 : "FLOat",
        }
        acq_type_dict = {
            1 : "RAW",
            2 : "AVERage",
            3 : "VHIStogram",
            4 : "HHIStogram",
            6 : "INTerpolate",
            9 : "DIGITAL",
            10 : "PDETect",
        }
        acq_mode_dict = {
            0 : "RTIMe",
            1 : "ETIMe",
            2 : "SEGMented",
            3 : "PDETect",
        }
        coupling_dict = {
            0 : "AC",
            1 : "DC",
            2 : "DCFIFTY",
            3 : "LFREJECT",
        }
        units_dict = {
            0 : "UNKNOWN",
            1 : "VOLT",
            2 : "SECOND",
            3 : "CONSTANT",
            4 : "AMP",
            5 : "DECIBEL",
            6 : "HERTZ",
            7 : "WATT",
        }

        units_abbrev_dict = {
            0 : "?",
            1 : "V",
            2 : "s",
            3 : "CONST.",
            4 : "A",
            5 : "dB",
            6 : "Hz",
            7 : "W",
        }

        units_axis_dict = {
            0 : "UNKNOWN",
            1 : "Voltage",
            2 : "Time",
            3 : "CONSTANT",
            4 : "Current",
            5 : "Decibels",
            6 : "Frequency",
            7 : "Power",
        }
        
        preamble_string = self._instQuery("WAVeform:PREamble?")
        (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,
         x_reference, y_increment, y_origin, y_reference, coupling,
         x_display_range, x_display_origin, y_display_range,
         y_display_origin, date, time, frame_model, acq_mode,
         completion, x_units, y_units, max_bw_limit, min_bw_limit
        ) = preamble_string.split(",")

        meta.append(("Date","{}".format(date)))
        meta.append(("Time","{}".format(time)))
        meta.append(("Frame model #","{}".format(frame_model)))
        meta.append(("Waveform source","{}".format(wav_source)))
        meta.append(("Waveform view","{}".format(wav_view)))
        meta.append(("Waveform format","{}".format(wav_form_dict[int(wav_form)])))
        meta.append(("Acquire mode","{}".format(acq_mode_dict[int(acq_mode)])))
        meta.append(("Acquire type","{}".format(acq_type_dict[int(acq_type)])))
        meta.append(("Coupling","{}".format(coupling_dict[int(coupling)])))
        meta.append(("Waveform points available","{}".format(wfmpts)))
        meta.append(("Waveform average count","{}".format(avgcnt)))
        meta.append(("Waveform X increment","{}".format(x_increment)))
        meta.append(("Waveform X origin","{}".format(x_origin)))
        meta.append(("Waveform X reference","{}".format(x_reference))) # Always 0.
        meta.append(("Waveform Y increment","{}".format(y_increment)))
        meta.append(("Waveform Y origin","{}".format(y_origin)))
        meta.append(("Waveform Y reference","{}".format(y_reference))) # Always 0.
        meta.append(("Waveform X display range","{}".format(x_display_range)))
        meta.append(("Waveform X display origin","{}".format(x_display_origin)))
        meta.append(("Waveform Y display range","{}".format(y_display_range)))
        meta.append(("Waveform Y display origin","{}".format(y_display_origin)))
        meta.append(("Waveform X units","{}".format(units_dict[int(x_units)])))
        meta.append(("Waveform Y units","{}".format(units_dict[int(y_units)])))
        meta.append(("Max BW limit","{}".format(max_bw_limit)))
        meta.append(("Min BW limit","{}".format(min_bw_limit)))
        meta.append(("Completion pct","{}".format(completion)))
        
        # Convert some of the preamble to numeric values for later calculations.
        #
        # NOTE: These are already gathered from PREamble above but s
        #
        acq_type    = int(acq_type)
        wav_form    = int(wav_form)
        x_units     = int(x_units)
        y_units     = int(y_units)
        x_increment = float(x_increment)
        x_origin    = float(x_origin)
        x_reference = int(float(x_reference))
        y_increment = float(y_increment)
        y_origin    = float(y_origin)
        y_reference = int(float(y_reference))
        x_display_range  = float(x_display_range)
        x_display_origin = float(x_display_origin)

        # Get the waveform data.
        pts = ''
        start = 0
        if (points is not None):
            if (channel.startswith('HIST')):
                print('   WARNING: Requesting Histogram data with Points. Ignore Points and returning all\n')
            else:
                # If want subset of points, grab them from the center of display
                midpt = int((((x_display_range / 2) + x_display_origin) - x_origin) / x_increment)
                start = midpt - (points // 2)
                pts = ' {},{}'.format(start,points)
                print('   As requested only downloading center {} points starting at {}\n'.format(points, ((x_reference + start) * x_increment) + x_origin))
            
        self._instWrite("WAVeform:STReaming OFF")
        sData = self._instQueryIEEEBlock("WAVeform:DATA?"+pts)

        meta.append(("Waveform bytes downloaded","{}".format(len(sData))))
        
        if (DEBUG):
            # Wait until after data transfer to output meta data so
            # that the preamble data is captured as close to the data
            # as possible.
            for mm in meta:
                print("{:>27}: {}".format(mm[0],mm[1]))
            print()

        # Set parameters based on returned Waveform Format
        #
        # NOTE: Ignoring ASCII format
        if (wav_form == 1):
            # BYTE
            bits = 8
            npTyp = np.int8
            unpackStr = "@%db" % (len(sData)//(bits//8))
        elif (wav_form == 2):
            # WORD
            bits = 16
            npTyp = np.int16
            unpackStr = "@%dh" % (len(sData)//(bits//8))
        elif (wav_form == 3):
            # LONG (unclear but believe this to be 32 bits)
            bits = 32
            npTyp = np.int32
            unpackStr = "@%dl" % (len(sData)//(bits//8))
        elif (wav_form == 4):
            # LONGLONG
            bits = 64
            npTyp = np.int64
            unpackStr = "@%dq" % (len(sData)//(bits//8))
        elif (wav_form == 5):
            # FLOAT (single-precision)
            bits = 32
            npTyp = np.float32
            unpackStr = "@%df" % (len(sData)//(bits//8))
        else:
            raise RuntimeError('Unknown Waveform Format: ' + wav_form_dict[wav_form])
        
        # Unpack signed byte data.
        if (version_info < (3,)):
            ## If PYTHON 2, sData will be a string and needs to be converted into a list of integers
            #
            # NOTE: not sure if this still works - besides PYTHON2 support is deprecated
            values = np.array([ord(x) for x in sData], dtype=np.int8)
        else:
            ## If PYTHON 3, 
            # Unpack signed data and store in proper type
            #
            # If the acquire type is HHIStogram or VHIStogram, the data is signed 64-bit integers
            #if (acq_type == 3 or acq_type == 4):
            #    unpackStr = "@%dq" % (len(sData)//8)
            #    unpackTyp = np.int64
            #else:
            #    unpackStr = "@%dh" % (len(sData)//2)
            #    unpackTyp = np.int16

            values = np.array(struct.unpack(unpackStr, sData), dtype=npTyp)
            
        nLength = len(values)
        meta.append(("Number of data values","{:d}".format(nLength)))

        # create an array of time (or voltage if histogram) values
        #
        # NOTE: Documentation currently say x_reference should
        # always be 0 but still including it in equation in case
        # that changes in the future
        x = ((np.arange(nLength) - x_reference + start) * x_increment) + x_origin

        # If the acquire type is DIGITAL, the y data
        # does not need to be converted to an analog value
        if (acq_type == 9):
            if (channel.startswith('BUS')):
                # If the channel name starts with BUS, then do not break into bits
                y = values      # no conversion needed
                header = ['Time (s)', 'BUS Values']

            elif (channel.startswith('POD')):
                # If the channel name starts with POD, then data needs
                # to be split into bits. Note that different
                # oscilloscope Series Class add PODx as valid channel
                # names if they support digital channels. This
                # prevents those without digital channels from ever
                # passing in a channel name that starts with 'POD' so
                # no need to also check here.

                # Put number of POD into 'pod'
                if (channel == 'PODALL'):
                    # Default to 1 so the math works out to get all 16 digital channels
                    pod = 1
                else:
                    # Grab number suffix to determine which bit to start with
                    pod = int(channel[-1])
                                
                # So y will be a 2D array where y[0] is time array of bit 0, y[1] for bit 1, etc.
                y = np.empty((bits, len(values)),npTyp)
                for ch in range(bits):
                    y[ch] = (values >> ch) & 1

                header = ['Time (s)'] + ['D{}'.format((pod-1) * bits + ch) for ch in range(bits)]
                    
        else:
            # create an array of vertical data (typ. Voltages)
            #
            if (wav_form == 5):
                # If Waveform Format is FLOAT, then conversion not needed
                y = values
            else:
                # NOTE: Documentation currently say y_reference should
                # always be 0 but still including it in equation in case
                # that changes in the future                    
                y = ((values - y_reference) * y_increment) + y_origin

            header = [f'{units_axis_dict[x_units]} ({units_abbrev_dict[x_units]})', f'{units_axis_dict[y_units]} ({units_abbrev_dict[y_units]})']

            
        # Return the data in numpy arrays along with the header & meta data
        return (x, y, header, meta)
        
    # =========================================================
    # Based on the Waveform data download example from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def _waveformDataLegacy(self, channel, points=None):
        """ Download the Waveform Data of a particular Channel and return it. """

        DEBUG = True
            
        # Download waveform data.
        # --------------------------------------------------------

        # Create array for meta data
        meta = []

        # Set the waveform source.
        self._instWrite("WAVeform:SOURce {}".format(self.channelStr(channel)))
        wav_source = self._instQuery("WAVeform:SOURce?")

        # Get the waveform view.
        wav_view = self._instQuery("WAVeform:VIEW?")
        
        # Choose the format of the data returned:
        self._instWrite("WAVeform:FORMat BYTE")

        # Set to Unsigned data which is compatible with PODx
        self._instWrite("WAVeform:UNSigned ON")

        # Set the waveform points mode.
        self._instWrite("WAVeform:POINts:MODE MAX")
        wav_points_mode = self._instQuery("WAVeform:POINts:MODE?")

        # Set the number of waveform points to fetch, if it was passed in.
        #
        # NOTE: With this Legacy software, this decimated the data so
        # that you would still get a display's worth but not every
        # single time bucket. This works differently for the newer
        # software where above points picks the number of points in
        # the center of the display to send but every consecutive time
        # bucket is sent.
        if (points is not None):
            self._instWrite("WAVeform:POINts {}".format(points))
        wav_points = int(self._instQuery("WAVeform:POINts?"))

        # Display the waveform settings from preamble:
        wav_form_dict = {
            0 : "BYTE",
            1 : "WORD",
            4 : "ASCii",
        }

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


        meta.append(("Waveform source","{}".format(wav_source)))
        meta.append(("Waveform view","{}".format(wav_view)))
        meta.append(("Waveform format","{}".format(wav_form_dict[int(wav_form)])))
        meta.append(("Acquire type","{}".format(acq_type_dict[int(acq_type)])))
        meta.append(("Waveform points mode","{}".format(wav_points_mode)))
        meta.append(("Waveform points available","{}".format(wav_points)))
        meta.append(("Waveform points desired","{:d}".format((wfmpts))))
        meta.append(("Waveform average count","{:d}".format(avgcnt)))
        meta.append(("Waveform X increment","{:1.12f}".format(x_increment)))
        meta.append(("Waveform X origin","{:1.9f}".format(x_origin)))
        meta.append(("Waveform X reference","{:d}".format(x_reference))) # Always 0.
        meta.append(("Waveform Y increment","{:f}".format(y_increment)))
        meta.append(("Waveform Y origin","{:f}".format(y_origin)))
        meta.append(("Waveform Y reference","{:d}".format(y_reference))) # Always 128 with UNSIGNED
        
        # Convert some of the preamble to numeric values for later calculations.
        #
        # NOTE: These are already gathered from PREamble above but s
        #
        wav_form    = int(wav_form)
        x_increment = float(x_increment)
        x_origin    = float(x_origin)
        y_increment = float(y_increment)
        y_origin    = float(y_origin)

        # Get the waveform data.
        sData = self._instQueryIEEEBlock("WAVeform:DATA?")

        meta.append(("Waveform bytes downloaded","{}".format(len(sData))))
        
        if (DEBUG):
            # Wait until after data transfer to output meta data so
            # that the preamble data is captured as close to the data
            # as possible.
            for mm in meta:
                print("{:>27}: {}".format(mm[0],mm[1]))
            print()
        
        if (version_info < (3,)):
            ## If PYTHON 2, sData will be a string and needs to be converted into a list of integers
            #
            # NOTE: not sure if this still works - besides PYTHON2 support is deprecated
            values = np.array([ord(x) for x in sData], dtype=np.int8)
        else:
            ## If PYTHON 3, 
            # Unpack unsigned byte data and store in int16 so room to convert unsigned to signed
            values = np.array(struct.unpack("%dB" % len(sData), sData), dtype=np.int16)

        nLength = len(values)
        meta.append(("Number of data values","{:d}".format(nLength)))

        # create an array of time values
        x = ((np.arange(nLength) - x_reference) * x_increment) + x_origin

        if (channel.startswith('BUS')):
            # If the channel name starts with BUS, then data is not
            # analog and does not need to be converted
            y = values      # no conversion needed
            header = ['Time (s)', 'BUS Values']

        elif (channel.startswith('POD')):
            # If the channel name starts with POD, then data is
            # digital and needs to be split into bits
            if (wav_form == 1):
                # wav_form of 1 is WORD, so 16 bits
                bits = 16
                typ = np.int16
            else:
                # assume byte                
                bits = 8
                typ = np.int8

            # So y will be a 2D array where y[0] is time array of bit 0, y[1] for bit 1, etc.
            y = np.empty((bits, len(values)),typ)
            for ch in range(bits):
                y[ch] = (values >> ch) & 1

            # Put number of POD into 'pod'
            pod = int(channel[-1])
            header = ['Time (s)'] + ['D{}'.format((pod-1) * bits + ch) for ch in range(bits)]
                
        else:
            # create an array of vertical data (typ. Voltages)
            y = ((values - y_reference) * y_increment) + y_origin

            header = ['Time (s)', 'Voltage (V)']
        
        # Return the data in numpy arrays along with the header & meta data
        return (x, y, header, meta)

    def waveformData(self, channel=None, points=None):
        """ Download waveform data of a selected channel

        channel  - channel, as string, to be measured - set to None to use the default channel

        points   - number of points to capture - if None, captures all available points
                   for newer devices, the captured points are centered around the center of the display

        """
        
        # If a channel value is passed in, make it the
        # current channel
        if channel is not None and type(channel) is not list:
            self.channel = channel

        # Make sure channel is NOT a list
        if type(self.channel) is list or type(channel) is list:
            raise ValueError('Channel cannot be a list for WAVEFORM!')

        # Check channel value
        if (self.channel not in self.chanAllValidList):
            raise ValueError('INVALID Channel Value for WAVEFORM: {}  SKIPPING!'.format(self.channel))            

        
        if (self._version > self._versionLegacy):
            (x, y, header, meta) = self._waveformDataNew(self.channel, points)
        else:
            (x, y, header, meta) = self._waveformDataLegacy(self.channel, points)        

        return (x, y, header, meta)
        

    def _measureStatistics(self):
        """Returns data from the current statistics window.
        """

        # tell Results? return all values (as opposed to just one of them)
        self._instWrite("MEASure:STATistics ON")

        # create a list of the return values, which are seperated by a comma
        statFlat = self._instQuery("MEASure:RESults?").split(',')

        # Return flat, uninterpreted data returned from command
        return statFlat
    

    def _readDVM(self, mode, channel=None, timeout=None, wait=0.5):
        """Read the DVM data of desired channel and return the value.

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number

        wait: Number of seconds after select DVM mode before trying to
        read values. Set to None for no waiting (not recommended)
        """

        if (self.series == 'KEYSIGHT' or self.series == 'UXR'):
            # Generic Keysight and UXR do not support DVM
            raise RuntimeError(f"This machine appears to be of the {self.series} series which does not support DVM")

        if (mode == 'FREQ' and self.series != "MSOX3" and self.series != "DSOX3"):
            # This device does not support DVM:FREQ? so simply return an invalid, overrange number
            return self.OverRange
        
        # If a channel value is passed in, make it the
        # current channel
        if channel is not None and type(channel) is not list:
            self.channel = channel

        # Make sure channel is NOT a list
        if type(self.channel) is list or type(channel) is list:
            raise ValueError('Channel cannot be a list for DVM!')

        # Check channel value
        if (self.channel not in self._chanAnaValidList):
            raise ValueError('INVALID Channel Value for DVM: {}  SKIPPING!'.format(self.channel))
            
        # First check if DVM is enabled
        if (not self.DVMisEnabled()):
            # It is not enabled, so enable it
            self.enableDVM(True)
            
        # Next check if desired DVM channel is the source, if not switch it
        #
        # NOTE: doing it this way so as to not possibly break the
        # moving average since do not know if buffers are cleared when
        # the SOURCE command is sent even if the channel does not
        # change.
        src = self._instQuery("DVM:SOURce?")
        #print("Source: {}".format(src))
        if (self._chanNumber(src) != self.channel):
            # Different channel value so switch it
            #print("Switching to {}".format(self.channel))
            self._instWrite("DVM:SOURce {}".format(self.channelStr(self.channel)))

        # Select the desired DVM mode
        self._instWrite("DVM:MODE {}".format(mode))

        # wait a little before read value to make sure everything is switched
        if (wait):
            sleep(wait)

        # Read value until get one < +9.9E+37 (per programming guide suggestion)
        startTime = datetime.now()
        val = self.OverRange
        while (val >= self.OverRange):
            duration = datetime.now() - startTime
            if (timeout is not None and duration.total_seconds() >= timeout):
                # if timeout is a value and have been waiting that
                # many seconds for a valid DVM value, stop waiting and
                # return this self.OverRange number.
                break

            val = self._instQueryNumber("DVM:CURRent?")

        # if mode is frequency, read and return the 5-digit frequency instead
        if (mode == "FREQ"):
            val = self._instQueryNumber("DVM:FREQ?")

        return val

    def DVMisEnabled(self):
        """Return True is DVM is enabled, else False"""

        if (self.series == 'KEYSIGHT' or self.series == 'UXR'):
            # Generic Keysight and UXR do not support DVM
            raise RuntimeError(f"This machine appears to be of the {self.series} series which does not support DVM")

        en = self._instQuery("DVM:ENABle?")
        return self._1OR0(en)

    def enableDVM(self, enable=True):
        """Enable or Disable DVM

        enable: If True, Enable (turn on) DVM mode, else Disable (turn off) DVM mode
        """

        if (self.series == 'KEYSIGHT' or self.series == 'UXR'):
            # Generic Keysight and UXR do not support DVM
            raise RuntimeError(f"This machine appears to be of the {self.series} series which does not support DVM")

        if (enable):
            self._instWrite("DVM:ENABLE ON")
        else:
            self._instWrite("DVM:ENABLE OFF")

        
    def measureDVMacrms(self, channel=None, timeout=None, wait=0.5):
        """Measure and return the AC RMS reading of channel using DVM
        mode.

        AC RMS is defined as 'the root-mean-square value of the acquired
        data, with the DC component removed.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns self.OverRange
        """

        return self._readDVM("ACRM", channel, timeout, wait)

    def measureDVMdc(self, channel=None, timeout=None, wait=0.5):
        """ Measure and return the DC reading of channel using DVM mode.

        DC is defined as 'the DC value of the acquired data.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns self.OverRange
        """

        return self._readDVM("DC", channel, timeout, wait)

    def measureDVMdcrms(self, channel=None, timeout=None, wait=0.5):
        """ Measure and return the DC RMS reading of channel using DVM mode.

        DC RMS is defined as 'the root-mean-square value of the acquired data.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns self.OverRange
        """

        return self._readDVM("DCRM", channel, timeout, wait)

    def measureDVMfreq(self, channel=None, timeout=3, wait=0.5):
        """ Measure and return the FREQ reading of channel using DVM mode.

        FREQ is defined as 'the frequency counter measurement.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns self.OverRange

        NOTE: If the signal is not periodic, this call will block until
        a frequency is measured, unless a timeout value is given.
        """

        return self._readDVM("FREQ", channel, timeout, wait)

    def _measure(self, mode, para=None, channel=None, wait=0.25, install=False):
        """Read and return a measurement of type mode from channel

           mode - selected measurement as a string

           para - parameters to be passed to command

           channel - channel to be measured starting at 1. Must be a string, ie. '1'

           wait - if not None, number of seconds to wait before querying measurement

           install - if True, adds measurement to the statistics display
        """

        # If a channel value is passed in, make it the
        # current channel
        if channel is not None and type(channel) is not list:
            self.channel = channel

        # Make sure channel is NOT a list
        if type(self.channel) is list or type(channel) is list:
            raise ValueError('Channel cannot be a list for MEASURE!')

        # Check channel value
        if (self.channel not in self._chanAnaValidList):
            raise ValueError('INVALID Channel Value for MEASURE: {}  SKIPPING!'.format(self.channel))
            
        # Next check if desired channel is the source, if not switch it
        #
        # NOTE: doing it this way so as to not possibly break the
        # moving average since do not know if buffers are cleared when
        # the SOURCE command is sent even if the channel does not
        # change.
        src = self._instQuery("MEASure:SOURce?")
        #print("Source: {}".format(src))
        if (self._chanNumber(src) != self.channel):
            # Different channel so switch it
            #print("Switching to {}".format(self.channel))
            self._instWrite("MEASure:SOURce {}".format(self.channelStr(self.channel)))

        if (para):
            # Need to add parameters to the write and query strings
            strWr = "MEASure:{} {}".format(mode, para)
            strQu = "MEASure:{}? {}".format(mode, para)
        else:
            strWr = "MEASure:{}".format(mode)
            strQu = "MEASure:{}?".format(mode)

        if (install):
            # If desire to install the measurement, make sure the
            # statistics display is on and then use the command form of
            # the measurement to install the measurement.
            if (self._version > self._versionLegacy):
                self._instWrite("MEASure:STATistics ON")
            else:
                self._instWrite("MEASure:STATistics:DISPlay ON")
            self._instWrite(strWr)

        # wait a little before read value, if wait is not None
        if (wait):
            sleep(wait)

        # query the measurement (do not have to install to query it)
        val = self._instQuery(strQu)

        return float(val)


    def measureBitRate(self, channel=None, wait=0.25, install=False):
        """Measure and return the bit rate measurement.

        This measurement is defined as: 'measures all positive and
        negative pulse widths on the waveform, takes the minimum value
        found of either width type and inverts that minimum width to
        give a value in Hertz'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display

        """

        if (self._version > self._versionLegacy):
            # NOTE: CDRRate requires "ANALyze:AEDGes ON". Not sure how that may impact other measurements
            # NOTE: CDRRate also requires the source to be in the command even though we set MEASURE:SOURCE
            self._instWrite("ANALyze:AEDGes ON")
            return self._measure("CDRRate", channel=channel, wait=wait, install=install)
        else:
            return self._measure("BRATe", channel=channel, wait=wait, install=install)

    def measureBurstWidth(self, channel=None, wait=0.25, install=False):
        """Measure and return the burst width measurement.

        This measurement is defined as: 'the width of the burst on the
        screen.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        
        if (self._version > self._versionLegacy):
            # BWIDth changed - now it is burst width within waveform, not just Screen edges
            # must set an idle time - not sure what to set - setting 1 us for now
            if channel is None:
                # need channel as parameter so grab self.channel if channel is None
                channel = self.channel
            return self._measure("BWIDth", para="{},{}".format(self.channelStr(channel),'1e-6'),
                                 channel=channel, wait=wait, install=install)
        else:
            return self._measure("BWIDth", channel=channel, wait=wait, install=install)

    def measureCounterFrequency(self, channel=None, wait=0.25, install=False):
        """Measure and return the counter frequency

        This measurement is defined as: 'the counter frequency.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - issues if install, so this paramter is ignored
        """

        # NOTE: The programmer's guide suggests sending a :MEASURE:CLEAR
        # first because if COUNTER is installed for ANY channel, this
        # measurement will fail. Note doing the CLEAR, but if COUNTER
        # gets installed, this will fail until it gets manually CLEARed.

        if (self._version > self._versionLegacy):
            # This measurement does not exist for newer sw versions
            return self.OverRange
        else:
            return self._measure("COUNter", channel=channel, wait=wait, install=False)

    def measurePosDutyCycle(self, channel=None, wait=0.25, install=False):
        """Measure and return the positive duty cycle

        This measurement is defined as: 'The value returned for the duty
        cycle is the ratio of the positive pulse width to the
        period. The positive pulse width and the period of the specified
        signal are measured, then the duty cycle is calculated with the
        following formula:

        duty cycle = (+pulse width/period)*100'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        if (self._version > self._versionLegacy):
            # Must specify if Positive (Rising Edge to Rising Edge)
            if channel is None:
                # need channel as parameter so grab self.channel if channel is None
                channel = self.channel
            return self._measure("DUTYcycle", para="{},{}".format(self.channelStr(channel),'RISing'),
                                 channel=channel, wait=wait, install=install)
        else:
            return self._measure("DUTYcycle", channel=channel, wait=wait, install=install)

    def measureFallTime(self, channel=None, wait=0.25, install=False):
        """Measure and return the fall time

        This measurement is defined as: 'the fall time of the displayed
        falling (negative-going) edge closest to the trigger
        reference. The fall time is determined by measuring the time at
        the upper threshold of the falling edge, then measuring the time
        at the lower threshold of the falling edge, and calculating the
        fall time with the following formula:

        fall time = time at lower threshold - time at upper threshold'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("FALLtime", channel=channel, wait=wait, install=install)

    def measureRiseTime(self, channel=None, wait=0.25, install=False):
        """Measure and return the rise time

        This measurement is defined as: 'the rise time of the displayed
        rising (positive-going) edge closest to the trigger
        reference. For maximum measurement accuracy, set the sweep speed
        as fast as possible while leaving the leading edge of the
        waveform on the display. The rise time is determined by
        measuring the time at the lower threshold of the rising edge and
        the time at the upper threshold of the rising edge, then
        calculating the rise time with the following formula:

        rise time = time at upper threshold - time at lower threshold'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("RISetime", channel=channel, wait=wait, install=install)

    def measureFrequency(self, channel=None, wait=0.25, install=False):
        """Measure and return the frequency of cycle on screen

        This measurement is defined as: 'the frequency of the cycle on
        the screen closest to the trigger reference.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("FREQ", channel=channel, wait=wait, install=install)

    def measureNegDutyCycle(self, channel=None, wait=0.25, install=False):
        """Measure and return the negative duty cycle

        This measurement is defined as: 'The value returned for the duty
        cycle is the ratio of the negative pulse width to the
        period. The negative pulse width and the period of the specified
        signal are measured, then the duty cycle is calculated with the
        following formula:

        -duty cycle = (-pulse width/period)*100'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        if (self._version > self._versionLegacy):
            # Must specify if Negative (Falling Edge to Falling Edge)
            if channel is None:
                # need channel as parameter so grab self.channel if channel is None
                channel = self.channel
            return self._measure("DUTYcycle", para="{},{}".format(self.channelStr(channel),'FALLing'),
                                 channel=channel, wait=wait, install=install)
        else:
            return self._measure("NDUTy", channel=channel, wait=wait, install=install)

    def measureFallEdgeCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen falling edge count

        This measurement is defined as: 'the on-screen falling edge
        count'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        if (self._version > self._versionLegacy):
            # This measurement does not exist for newer sw versions
            return self.OverRange
        else:
            return self._measure("NEDGes", channel=channel, wait=wait, install=install)

    def measureFallPulseCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen falling pulse count

        This measurement is defined as: 'the on-screen falling pulse
        count'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("NPULses", channel=channel, wait=wait, install=install)

    def measureNegPulseWidth(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen falling/negative pulse width

        This measurement is defined as: 'the width of the negative pulse
        on the screen closest to the trigger reference using the
        midpoint between the upper and lower thresholds.

        FOR the negative pulse closest to the trigger point:

        width = (time at trailing rising edge - time at leading falling edge)'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("NWIDth", channel=channel, wait=wait, install=install)

    def measureOvershoot(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen voltage overshoot in percent

        This measurement is defined as: 'the overshoot of the edge
        closest to the trigger reference, displayed on the screen. The
        method used to determine overshoot is to make three different
        vertical value measurements: Vtop, Vbase, and either Vmax or
        Vmin, depending on whether the edge is rising or falling.

        For a rising edge:

        overshoot = ((Vmax-Vtop) / (Vtop-Vbase)) x 100

        For a falling edge:

        overshoot = ((Vbase-Vmin) / (Vtop-Vbase)) x 100

        Vtop and Vbase are taken from the normal histogram of all
        waveform vertical values. The extremum of Vmax or Vmin is taken
        from the waveform interval right after the chosen edge, halfway
        to the next edge. This more restricted definition is used
        instead of the normal one, because it is conceivable that a
        signal may have more preshoot than overshoot, and the normal
        extremum would then be dominated by the preshoot of the
        following edge.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("OVERshoot", channel=channel, wait=wait, install=install)

    def measurePreshoot(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen voltage preshoot in percent

        This measurement is defined as: 'the preshoot of the edge
        closest to the trigger, displayed on the screen. The method used
        to determine preshoot is to make three different vertical value
        measurements: Vtop, Vbase, and either Vmin or Vmax, depending on
        whether the edge is rising or falling.

        For a rising edge:

        preshoot = ((Vmin-Vbase) / (Vtop-Vbase)) x 100

        For a falling edge:

        preshoot = ((Vmax-Vtop) / (Vtop-Vbase)) x 100

        Vtop and Vbase are taken from the normal histogram of all
        waveform vertical values. The extremum of Vmax or Vmin is taken
        from the waveform interval right before the chosen edge, halfway
        back to the previous edge. This more restricted definition is
        used instead of the normal one, because it is likely that a
        signal may have more overshoot than preshoot, and the normal
        extremum would then be dominated by the overshoot of the
        preceding edge.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("PREShoot", channel=channel, wait=wait, install=install)

    def measureRiseEdgeCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen rising edge count

        This measurement is defined as: 'the on-screen rising edge
        count'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        if (self._version > self._versionLegacy):
            # This measurement does not exist for newer sw versions
            return self.OverRange
        else:
            return self._measure("PEDGes", channel=channel, wait=wait, install=install)

    def measureRisePulseCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen rising pulse count

        This measurement is defined as: 'the on-screen rising pulse
        count'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("PPULses", channel=channel, wait=wait, install=install)

    def measurePosPulseWidth(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen falling/positive pulse width

        This measurement is defined as: 'the width of the displayed
        positive pulse closest to the trigger reference. Pulse width is
        measured at the midpoint of the upper and lower thresholds.

        IF the edge on the screen closest to the trigger is falling:

        THEN width = (time at trailing falling edge - time at leading rising edge)

        ELSE width = (time at leading falling edge - time at leading rising edge)'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("PWIDth", channel=channel, wait=wait, install=install)

    def measurePeriod(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen period

        This measurement is defined as: 'the period of the cycle closest
        to the trigger reference on the screen. The period is measured
        at the midpoint of the upper and lower thresholds.

        IF the edge closest to the trigger reference on screen is rising:

        THEN period = (time at trailing rising edge - time at leading rising edge)

        ELSE period = (time at trailing falling edge - time at leading falling edge)'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("PERiod", channel=channel, wait=wait, install=install)

    def measureVoltAmplitude(self, channel=None, wait=0.25, install=False):
        """Measure and return the vertical amplitude of the signal

        This measurement is defined as: 'the vertical amplitude of the
        waveform. To determine the amplitude, the instrument measures
        Vtop and Vbase, then calculates the amplitude as follows:

        vertical amplitude = Vtop - Vbase'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VAMPlitude", channel=channel, wait=wait, install=install)

    def measureVoltAverage(self, channel=None, wait=0.25, install=False):
        """Measure and return the Average Voltage measurement.

        This measurement is defined as: 'average value of an integral
        number of periods of the signal. If at least three edges are not
        present, the oscilloscope averages all data points.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VAVerage", para="DISPlay", channel=channel, wait=wait, install=install)

    def measureVoltRMS(self, channel=None, wait=0.25, install=False):
        """Measure and return the DC RMS Voltage measurement.

        This measurement is defined as: 'the dc RMS value of the
        selected waveform. The dc RMS value is measured on an integral
        number of periods of the displayed signal. If at least three
        edges are not present, the oscilloscope computes the RMS value
        on all displayed data points.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VRMS", para="DISPlay,DC", channel=channel, wait=wait, install=install)

    def measureVoltBase(self, channel=None, wait=0.25, install=False):
        """Measure and return the Voltage base measurement.

        This measurement is defined as: 'the vertical value at the base
        of the waveform. The base value of a pulse is normally not the
        same as the minimum value.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VBASe", channel=channel, wait=wait, install=install)

    def measureVoltTop(self, channel=None, wait=0.25, install=False):
        """Measure and return the Voltage Top measurement.

        This measurement is defined as: 'the vertical value at the top
        of the waveform. The top value of the pulse is normally not the
        same as the maximum value.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VTOP", channel=channel, wait=wait, install=install)

    def measureVoltMax(self, channel=None, wait=0.25, install=False):
        """Measure and return the Maximum Voltage measurement.

        This measurement is defined as: 'the maximum vertical value
        present on the selected waveform.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VMAX", channel=channel, wait=wait, install=install)


    def measureVoltMin(self, channel=None, wait=0.25, install=False):
        """Measure and return the Minimum Voltage measurement.

        This measurement is defined as: 'the minimum vertical value
        present on the selected waveform.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VMIN", channel=channel, wait=wait, install=install)


    def measureVoltPP(self, channel=None, wait=0.25, install=False):
        """Measure and return the voltage peak-to-peak measurement.

        This measurement is defined as: 'the maximum and minimum
        vertical value for the selected source, then calculates the
        vertical peak-to-peak value and returns that value. The
        peak-to-peak value (Vpp) is calculated with the following
        formula:

        Vpp = Vmax - Vmin

        Vmax and Vmin are the vertical maximum and minimum values
        present on the selected source.'

        If the returned value is >= self.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VPP", channel=channel, wait=wait, install=install)

    ## This is a dictionary of measurement labels with their units and
    ## method to get the data from the scope.
    _measureTbl = {
        'Bit Rate': ['Hz', measureBitRate],
        'Burst Width': ['s', measureBurstWidth],
        'Counter Freq': ['Hz', measureCounterFrequency],
        'Frequency': ['Hz', measureFrequency],
        'Period': ['s', measurePeriod],
        'Duty': ['%', measurePosDutyCycle],
        'Neg Duty': ['%', measureNegDutyCycle],
        'Fall Time': ['s', measureFallTime],
        'Rise Time': ['s', measureRiseTime],
        'Num Falling': ['', measureFallEdgeCount],
        'Num Neg Pulses': ['', measureFallPulseCount],
        'Num Rising': ['', measureRiseEdgeCount],
        'Num Pos Pulses': ['', measureRisePulseCount],
        '- Width': ['s', measureNegPulseWidth],
        '+ Width': ['s', measurePosPulseWidth],
        'Overshoot': ['%', measureOvershoot],
        'Preshoot': ['%', measurePreshoot],
        'Amplitude': ['V', measureVoltAmplitude],
        'Top': ['V', measureVoltTop],
        'Base': ['V', measureVoltBase],
        'Maximum': ['V', measureVoltMax],
        'Minimum': ['V', measureVoltMin],
        'Pk-Pk': ['V', measureVoltPP],
        'V p-p': ['V', measureVoltPP],
        'Average - Full Screen': ['V', measureVoltAverage],
        'RMS - Full Screen': ['V', measureVoltRMS],
        }

    def measureTblUnits(self, meas):
        """Return units for measurement 'meas'

        meas: a string to be looked up in _measureTbl to determine its units
        """

        try:
            units = self._measureTbl[meas][0]
        except KeyError:
            # Could not find meas so return blank string
            units = ''

        return units

    def measureTblCall(self, meas, channel=None):
        """Call function to gather measurement 'meas' for channel and return its value

        meas: a string to be looked up in _measureTbl to determine its units

        channel: channel, as string, to be measured - default channel
        for future readings
        """

        try:
            value = self._measureTbl[meas][1](self, channel)
        except KeyError:
            # Could not find meas so return self.OverRange
            value = self.OverRange

        return value
    
