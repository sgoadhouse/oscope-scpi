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
    from . import SCPI
except Exception:
    from SCPI import SCPI

from time import sleep
from datetime import datetime
from quantiphy import Quantity
from sys import version_info
import pyvisa as visa

class MSOX3000(SCPI):
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
        super(MSOX3000, self).__init__(resource, max_chan=MSOX3000.maxChannel, wait=wait,
                                       cmd_prefix=':',
                                       read_strip='\n',
                                       read_termination='',
                                       write_termination='\n'
                                      )
        
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


    def setupAutoscale(self, channel=None):
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

    def annotate(self, text, color=None, background='TRAN'):
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

    def annotateColor(self, color):
        """ Change screen annotation color """

        ## NOTE: Only certain values are allowed:
        # {CH1 | CH2 | CH3 | CH4 | DIG | MATH | REF | MARK | WHIT | RED}
        #
        # The scope will respond with an error if an invalid color string is passed along
        self._instWrite("DISPlay:ANN:COLor {}".format(color))

    def annotateOff(self):
        """ Turn off screen annotation """

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
        if (self.channel not in MSOX3000.chanAnaValidList):
            raise ValueError('INVALID Channel Value for CHANNEL LABEL: {}  SKIPPING!'.format(self.channel))
            
        self._instWrite('CHAN{}:LABel "{}"'.format(self.channel, label))
        self._instWrite('DISPlay:LABel ON')

    def channelLabelOff(self):
        """ Turn off channel labels """

        self._instWrite('DISPlay:LABel OFF')


    def polish(self, value, measure=None):
        """ Using the QuantiPhy package, return a value that is in apparopriate Si units.

        If value is >= SCPI.OverRange, then return the invalid string instead of a Quantity().

        If the measure string is None, then no units are used by the SI suffix is.

        """

        if (value >= SCPI.OverRange):
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

        # turn on the statistics display
        self._instWrite("SYSTem:MENU MEASure")
        self._instWrite("MEASure:STATistics:DISPlay ON")

        # tell Results? return all values (as opposed to just one of them)
        self._instWrite("MEASure:STATistics ON")

        # create a list of the return values, which are seperated by a comma
        statFlat = self._instQuery("MEASure:RESults?").split(',')

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

    def _measure(self, mode, para=None, channel=None, wait=0.25, install=False):
        """Read and return a measurement of type mode from channel

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
        if (self.channel not in MSOX3000.chanAnaValidList):
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
            self._instWrite("MEASure:SOURce {}".format(self._channelStr(self.channel)))

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

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display

        """

        return self._measure("BRATe", channel=channel, wait=wait, install=install)

    def measureBurstWidth(self, channel=None, wait=0.25, install=False):
        """Measure and return the bit rate measurement.

        This measurement is defined as: 'the width of the burst on the
        screen.'

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("BWIDth", channel=channel, wait=wait, install=install)

    def measureCounterFrequency(self, channel=None, wait=0.25, install=False):
        """Measure and return the counter frequency

        This measurement is defined as: 'the counter frequency.'

        If the returned value is >= SCPI.OverRange, then no valid value
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

        return self._measure("COUNter", channel=channel, wait=wait, install=False)

    def measurePosDutyCycle(self, channel=None, wait=0.25, install=False):
        """Measure and return the positive duty cycle

        This measurement is defined as: 'The value returned for the duty
        cycle is the ratio of the positive pulse width to the
        period. The positive pulse width and the period of the specified
        signal are measured, then the duty cycle is calculated with the
        following formula:

        duty cycle = (+pulse width/period)*100'

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("NDUTy", channel=channel, wait=wait, install=install)

    def measureFallEdgeCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen falling edge count

        This measurement is defined as: 'the on-screen falling edge
        count'

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("NEDGes", channel=channel, wait=wait, install=install)

    def measureFallPulseCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen falling pulse count

        This measurement is defined as: 'the on-screen falling pulse
        count'

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("PEDGes", channel=channel, wait=wait, install=install)

    def measureRisePulseCount(self, channel=None, wait=0.25, install=False):
        """Measure and return the on-screen rising pulse count

        This measurement is defined as: 'the on-screen rising pulse
        count'

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VRMS", para="DISPlay", channel=channel, wait=wait, install=install)

    def measureVoltBase(self, channel=None, wait=0.25, install=False):
        """Measure and return the Voltage base measurement.

        This measurement is defined as: 'the vertical value at the base
        of the waveform. The base value of a pulse is normally not the
        same as the minimum value.'

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
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

        If the returned value is >= SCPI.OverRange, then no valid value
        could be measured.

        channel: channel, as string, to be measured - default channel
        for future readings

        wait - if not None, number of seconds to wait before querying measurement

        install - if True, adds measurement to the statistics display
        """

        return self._measure("VPP", channel=channel, wait=wait, install=install)


    def _readDVM(self, mode, channel=None, timeout=None, wait=0.5):
        """Read the DVM data of desired channel and return the value.

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number

        wait: Number of seconds after select DVM mode before trying to
        read values. Set to None for no waiting (not recommended)
        """

        # If a channel value is passed in, make it the
        # current channel
        if channel is not None and type(channel) is not list:
            self.channel = channel

        # Make sure channel is NOT a list
        if type(self.channel) is list or type(channel) is list:
            raise ValueError('Channel cannot be a list for DVM!')

        # Check channel value
        if (self.channel not in MSOX3000.chanAnaValidList):
            raise ValueError('INVALID Channel Value for DVM: {}  SKIPPING!'.format(self.channel))
            
        # First check if DVM is enabled
        en = self._instQuery("DVM:ENABle?")
        if (not self._1OR0(en)):
            # It is not enabled, so enable it
            self._instWrite("DVM:ENABLE ON")

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
            self._instWrite("DVM:SOURce {}".format(self._channelStr(self.channel)))

        # Select the desired DVM mode
        self._instWrite("DVM:MODE {}".format(mode))

        # wait a little before read value to make sure everything is switched
        if (wait):
            sleep(wait)

        # Read value until get one < +9.9E+37 (per programming guide suggestion)
        startTime = datetime.now()
        val = SCPI.OverRange
        while (val >= SCPI.OverRange):
            duration = datetime.now() - startTime
            if (timeout is not None and duration.total_seconds() >= timeout):
                # if timeout is a value and have been waiting that
                # many seconds for a valid DVM value, stop waiting and
                # return this SCPI.OverRange number.
                break

            val = self._instQueryNumber("DVM:CURRent?")

        # if mode is frequency, read and return the 5-digit frequency instead
        if (mode == "FREQ"):
            val = self._instQueryNumber("DVM:FREQ?")

        return val

    def measureDVMacrms(self, channel=None, timeout=None, wait=0.5):
        """Measure and return the AC RMS reading of channel using DVM
        mode.

        AC RMS is defined as 'the root-mean-square value of the acquired
        data, with the DC component removed.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns SCPI.OverRange
        """

        return self._readDVM("ACRM", channel, timeout, wait)

    def measureDVMdc(self, channel=None, timeout=None, wait=0.5):
        """ Measure and return the DC reading of channel using DVM mode.

        DC is defined as 'the DC value of the acquired data.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns SCPI.OverRange
        """

        return self._readDVM("DC", channel, timeout, wait)

    def measureDVMdcrms(self, channel=None, timeout=None, wait=0.5):
        """ Measure and return the DC RMS reading of channel using DVM mode.

        DC RMS is defined as 'the root-mean-square value of the acquired data.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns SCPI.OverRange
        """

        return self._readDVM("DCRM", channel, timeout, wait)

    def measureDVMfreq(self, channel=None, timeout=3, wait=0.5):
        """ Measure and return the FREQ reading of channel using DVM mode.

        FREQ is defined as 'the frequency counter measurement.'

        channel: channel, as a string, to set to DVM mode and return its
        reading - becomes the default channel for future readings

        timeout: if None, no timeout, otherwise, time-out in seconds
        waiting for a valid number - if timeout, returns SCPI.OverRange

        NOTE: If the signal is not periodic, this call will block until
        a frequency is measured, unless a timeout value is given.
        """

        return self._readDVM("FREQ", channel, timeout, wait)


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

    ## This is a dictionary of measurement labels with their units and
    ## method to get the data from the scope.
    measureTbl = {
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
        'Average - Full Screen': ['V', measureVoltAverage],
        'RMS - Full Screen': ['V', measureVoltRMS],
        }

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
