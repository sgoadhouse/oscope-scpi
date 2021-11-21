#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2018,2019,2020,2021 Stephen Goadhouse <sgoadhouse@virginia.edu>
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

#---------------------------------------------------------------------------------
#  Control of HP/Agilent/Keysight MSO-X/DSO-X 3000A Oscilloscope using
#  standard SCPI commands with PyVISA
#
# For more information on SCPI, see:
# https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments
# http://www.ivifoundation.org/docs/scpi-99.pdf
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
from sys import version_info
from sys import exit
import pyvisa as visa

class SCPI(object):
    """Basic class for controlling and accessing an Oscilloscope with Standard SCPI Commands"""

    OverRange = +9.9E+37                  # Number which indicates Over Range
    UnderRange = -9.9E+37                 # Number which indicates Under Range
    ErrorQueue = 30                       # Size of error queue
    
    def __init__(self, resource, max_chan=1, wait=0,
                     cmd_prefix = '',
                     read_strip = '',
                     read_termination = '',
                     write_termination = '\n',
                     timeout = 5000):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        max_chan   - number of channels
        wait       - float that gives the default number of seconds to wait after sending each command
        cmd_prefix - optional command prefix (ie. some instruments require a ':' prefix)
        read_strip        - optional read_strip parameter used to strip any returned termination characters
        read_termination  - optional read_termination parameter to pass to open_resource()
        write_termination - optional write_termination parameter to pass to open_resource()
        """
        self._resource = resource
        self._max_chan = max_chan                # number of channels
        self._wait = wait
        self._prefix = cmd_prefix
        self._curr_chan = 1                      # set the current channel to the first one
        self._read_strip = read_strip
        self._read_termination = read_termination
        self._write_termination = write_termination
        self._timeout = timeout
        self._IDNmanu = ''      # store manufacturer from IDN here
        self._IDNmodel = ''     # store instrument model number from IDN here
        self._IDNserial = ''    # store instrument serial number from IDN here
        self._version = 0.0     # set software version to lowest value until it gets set
        self._versionLegacy = 0.0   # set software version which triggers Legacy code to lowest value until it gets set
        self._legacyError = True    # Start off using Legacy Error method since both old and new instruments return something
        self._inst = None

    def open(self):
        """Open a connection to the VISA device with PYVISA-py python library"""
        self._rm = visa.ResourceManager('@py')
        self._inst = self._rm.open_resource(self._resource,
                                            read_termination=self._read_termination,
                                            write_termination=self._write_termination)
        self._inst.timeout = self._timeout

        # Keysight recommends using clear()
        #
        # NOTE: must use pyvisa-py >= 0.5.0 to get this implementation
        # NOTE: pyvisa-py does not support clear() for USB so catch error
        try:
            self._inst.clear()
        except visa.VisaIOError as err:
            if (err.error_code == visa.constants.StatusCode.error_nonsupported_operation):
                # If this resource does not support clear(), that is
                # okay and it can be ignored.
                pass
            else:
                # However, if this is a different error be sure to raise it.
                raise
                
        # Read ID to gather items like software version number so can
        # deviate operation based on changes to commands over history
        # (WHY did they make changes?)  MUST be done before below
        # clear() which sends first command.
        self._getID()

        # Also, send a *CLS system command to clear the command
        # handler (error queues and such)
        self.clear()

        
    def close(self):
        """Close the VISA connection"""
        self._inst.close()

    @property
    def channel(self):
        return self._curr_chan

    @channel.setter
    def channel(self, value):
        self._curr_chan = value

    def _instQuery(self, queryStr, checkErrors=True):
        if (queryStr[0] != '*'):
            queryStr = self._prefix + queryStr
        #print("QUERY:",queryStr)
        try:
            result = self._inst.query(queryStr)
        except visa.VisaIOError as err:
            # Got VISA exception so read and report any errors
            if checkErrors:
                self.checkInstErrors(queryStr)
            #@@@#print("Exited because of VISA IO Error: {}".format(err))
            #@@@#exit(1)
            # raise same error so code calling this can use try/except to catch things
            raise
            
        if checkErrors:
            self.checkInstErrors(queryStr)
        return result.rstrip(self._read_strip)

    def _instQueryNumber(self, queryStr, checkErrors=True):
        return float(self._instQuery(queryStr, checkErrors))

    def _instWrite(self, writeStr, checkErrors=True):
        if (writeStr[0] != '*'):
            writeStr = self._prefix + writeStr
        #@@@print("WRITE:",writeStr)
        try:
            result = self._inst.write(writeStr)
        except visa.VisaIOError as err:
            # Got VISA exception so read and report any errors
            if checkErrors:
                self.checkInstErrors(writeStr)
            #@@@#print("Exited because of VISA IO Error: {}".format(err))
            #@@@#exit(1)
            # raise same error so code calling this can use try/except to catch things
            raise

        if checkErrors:
            self.checkInstErrors(writeStr)
        return result

    def chStr(self, channel):
        """return the channel string given the channel number and using the format CHx"""

        return 'CH{}'.format(channel)

    def _chanStr(self, channel):
        """return the channel string given the channel number and using the format x"""

        return '{}'.format(channel)

    def channelStr(self, channel):
        """return the channel string given the channel number and using the format CHANnelx if x is numeric. If pass in None, return None."""

        try:
            return 'CHAN{}'.format(int(channel))
        except TypeError:
            # If channel is None, will get this exception so simply return it
            return channel
        except ValueError:
            return self._chanStr(channel)

    def _onORoff(self, str):
        """Check if string says it is ON or OFF and return True if ON
        and False if OFF
        """

        # Only check first two characters so do not need to deal with
        # trailing whitespace and such
        if str[:2] == 'ON':
            return True
        else:
            return False

    def _1OR0(self, str):
        """Check if string says it is 1 or 0 and return True if 1
        and False if 0
        """

        # Only check first character so do not need to deal with
        # trailing whitespace and such
        if str[:1] == '1':
            return True
        else:
            return False

    def _chanNumber(self, str):
        """Decode the response as a channel number and return it. Return 0 if string does not decode properly.
        """

        # Only check first character so do not need to deal with
        # trailing whitespace and such
        if str[:4] == 'CHAN':
            return int(str[4])
        else:
            return 0

    def _wait(self):
        """Wait until all preceeding commands complete"""
        #self._instWrite('*WAI')
        self._instWrite('*OPC')
        wait = True
        while(wait):
            ret = self._instQuery('*OPC?')
            if ret[0] == '1':
                wait = False

    # =========================================================
    # Taken from the MSO-X 3000 Programming Guide and modified to work
    # within this class ...
    #    
    # UPDATE: Apparently "SYSTem:ERRor?" has changed but the
    # documentation is unclear so will make it work as it works on
    # MXR058A with v11.10
    # =========================================================
    # Check for instrument errors:
    # =========================================================
    def checkInstErrors(self, commandStr):

        methodNew = ("SYSTem:ERRor? STRing", ("0,", 0, 2))
        methodOld = ("SYSTem:ERRor?",        ("+0,", 0, 3))
        if (not self._legacyError and self._version > self._versionLegacy):
            cmd = methodNew[0]
            noerr = methodNew[1]
        else:
            self._legacyError = True # indicate that using Legacy Error method
            cmd = methodOld[0]
            noerr = methodOld[1]
            
        errors = False
        # No need to read more times that the size of the Error Queue
        for reads in range(0,self.ErrorQueue):
            try:
                # checkErrors=False prevents infinite recursion!
                #@@@#print('Q: {}'.format(cmd))
                error_string = self._instQuery(cmd, checkErrors=False)
            except visa.errors.VisaIOError as err:    
                if (err.error_code == visa.constants.StatusCode.error_timeout and cmd is methodNew[0]):
                    ## Older instruments may not understand a
                    ## parameter after the '?' and will not respond
                    ## resulting in a timeout. So, if trying the 'New'
                    ## command and get a timeout, assume this is
                    ## happening and try query again but modified for
                    ## the Legacy way.
                    ##
                    ## NOTE: Since loop goes no further than
                    ## self.ErrorQueue, will have 1 less possible loop
                    ## but that is okay.
                    cmd = methodOld[0]
                    noerr = methodOld[1]
                    # Also, set _legacyError to True to make
                    # code use methodOld in subsequent calls
                    self._legacyError = True # indicate that using Legacy Error method
                    continue
                else:
                    print("Unexpected VisaIOError during checkInstErrors(): {}".format(err))
                    errors = True # if unexpected response, then set as Error
                    break
                    
            error_string = error_string.strip()  # remove trailing and leading whitespace
            if error_string: # If there is an error string value.
                if error_string.find(*noerr) == -1:
                    # Not "No error".
                    #
                    # First check if using Legacy Error command just
                    # got an error code. If so, this is really a newer
                    # instrument and so retry using New command format
                    if (self._legacyError and error_string.isdigit()):
                        cmd = methodNew[0]
                        noerr = methodNew[1]
                        self._legacyError = False # indicate that using New Error method
                        continue
                        
                    print("ERROR({:02d}): {}, command: '{}'".format(reads, error_string, commandStr))
                    errors = True           # indicate there was an error
                else: # "No error"
                    break

            else: # :SYSTem:ERRor? should always return string.
                print("ERROR: :SYSTem:ERRor? returned nothing, command: '{}'".format(commandStr))
                errors = True # if unexpected response, then set as Error
                break

        return errors           # indicate if there was an error

    # =========================================================
    # Based on do_query_ieee_block() from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def _instQueryIEEEBlock(self, queryStr, checkErrors=True):
        if (queryStr[0] != '*'):
            queryStr = self._prefix + queryStr
        #print("QUERYIEEEBlock:",queryStr)
        try:
            result = self._inst.query_binary_values(queryStr, datatype='s', container=bytes)
        except visa.VisaIOError as err:
            # Got VISA exception so read and report any errors
            if checkErrors:
                self.checkInstErrors(queryStr)
            print("Exited because of VISA IO Error: {}".format(err))
            exit(1)
            
        if checkErrors:
            self.checkInstErrors(queryStr)
        return result

    # =========================================================
    # Based on code from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def _instQueryNumbers(self, queryStr, checkErrors=True):
        if (queryStr[0] != '*'):
            queryStr = self._prefix + queryStr
        #print("QUERYNumbers:",queryStr)
        try:
            result = self._inst.query_ascii_values(queryStr, converter='f', separator=',')
        except visa.VisaIOError as err:
            # Got VISA exception so read and report any errors
            if checkErrors:
                self.checkInstErrors(queryStr)
            print("Exited because of VISA IO Error: {}".format(err))
            exit(1)
            
        if checkErrors:
            self.checkInstErrors(queryStr)
        return result

    # =========================================================
    # Based on do_command_ieee_block() from the MSO-X 3000 Programming
    # Guide and modified to work within this class ...
    # =========================================================
    def _instWriteIEEEBlock(self, writeStr, values, checkErrors=True):
        if (writeStr[0] != '*'):
            writeStr = self._prefix + writeStr
        #print("WRITE:",writeStr)

        if (version_info < (3,)):
            ## If PYTHON 2, must use datatype of 'c'
            datatype = 'c'
        else:
            ## If PYTHON 2, must use datatype of 'B' to get the same result
            datatype = 'B'

        try:
            result = self._inst.write_binary_values(writeStr, values, datatype=datatype)
        except visa.VisaIOError as err:
            # Got VISA exception so read and report any errors
            if checkErrors:
                self.checkInstErrors(writeStr)
            print("Exited because of VISA IO Error: {}".format(err))
            exit(1)

        if checkErrors:
            self.checkInstErrors(writeStr)
        return result

    def _instWriteIEEENumbers(self, writeStr, values, checkErrors=True):
        if (writeStr[0] != '*'):
            writeStr = self._prefix + writeStr
        #print("WRITE:",writeStr)

        try:
            result = self._inst.write_binary_values(writeStr, values, datatype='f')
        except visa.VisaIOError as err:
            # Got VISA exception so read and report any errors
            if checkErrors:
                self.checkInstErrors(writeStr)
            print("Exited because of VISA IO Error: {}".format(err))
            exit(1)

        if checkErrors:
            self.checkInstErrors(writeStr)
        return result

    def _getID(self):
        """Query IDN data like Software Version to handle command history deviations. This is called from open()."""
        ## Skip Error check since handling of errors is version specific
        idn = self._instQuery('*IDN?', checkErrors=False).split(',')
        
        self._IDNmanu = idn[0]   # store manufacturer from IDN here
        self._IDNmodel = idn[1]  # store instrument model number from IDN here
        self._IDNserial = idn[2] # store instrument serial number from IDN here

        ver = idn[3].split('.')
        try:
            # put major and minor version into floating point format so can numerically compare
            self._version = float(ver[0]+'.'+ver[1])
        except:
            # In case version is not purely numeric
            ver[-1] = ver[-1].replace('\n', '')
            self._version = tuple(ver)
            self._versionLegacy = tuple()
        
    def idn(self):
        """Return response to *IDN? message"""
        return self._instQuery('*IDN?')

    def clear(self):
        """Sends a *CLS message to clear status and error queues"""
        return self._instWrite('*CLS')

    def reset(self):
        """Sends a *RST message to reset to defaults"""
        return self._instWrite('*RST')

    def setLocal(self):
        """Set the power supply to LOCAL mode where front panel keys work again
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite('SYSTem:LOCK OFF')

    def setRemote(self):
        """Set the power supply to REMOTE mode where it is controlled via VISA
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite('SYSTem:LOCK ON')

    def setRemoteLock(self):
        """Set the power supply to REMOTE Lock mode where it is
           controlled via VISA & front panel is locked out
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite('SYSTem:LOCK ON')

    def beeperOn(self):
        """Enable the system beeper for the instrument"""
        # no beeper to turn off, so make it do nothing
        pass

    def beeperOff(self):
        """Disable the system beeper for the instrument"""
        # no beeper to turn off, so make it do nothing
        pass

    def isOutputOn(self, channel=None):
        """Return true if the output of channel is ON, else false

           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        str = 'STATus? {}'.format(self.channelStr(self.channel))
        ret = self._instQuery(str)
        return self._1OR0(ret)

    def outputOn(self, channel=None, wait=None):
        """Turn on the output for channel

           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'VIEW {}'.format(self.channelStr(self.channel))
        self._instWrite(str)
        sleep(wait)

    def outputOff(self, channel=None, wait=None):
        """Turn off the output for channel

           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'BLANK {}'.format(self.channelStr(self.channel))
        self._instWrite(str)
        sleep(wait)

    def outputOnAll(self, wait=None):
        """Turn on the output for ALL channels

        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        for chan in range(1,self._max_chan+1):
            str = 'VIEW {}'.format(self.channelStr(chan))
            self._instWrite(str)

        sleep(wait)

    def outputOffAll(self, wait=None):
        """Turn off the output for ALL channels

        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        #for chan in range(1,self._max_chan+1):
        #    str = 'BLANK {}'.format(self.channelStr(chan))
        #    self._instWrite(str)

        if (self._version > self._versionLegacy):
            self._instWrite("BLANk ALL")
        else:
            # Turn off all channels (Legacy f/w take no parameter to blank all)
            self._instWrite("BLANk")
        
        sleep(wait)             # give some time for PS to respond

    def measureVoltage(self, channel=None):
        """Read and return a voltage measurement from channel

           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        str = 'INSTrument:NSELect {}; MEASure:VOLTage:DC?'.format(self.channel)
        val = self._instQueryNumber(str)
        return val
