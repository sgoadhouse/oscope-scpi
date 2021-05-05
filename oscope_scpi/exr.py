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
#  Control of Keysight EXR series Oscilloscopes with PyVISA
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

try:
    from .mxr import MXR
except Exception:
    sys.path.append(os.getcwd())
    from mxr import MXR

from time import sleep
from datetime import datetime
from quantiphy import Quantity
from sys import version_info
import pyvisa as visa

class EXR(MXR):
    """Basic class for controlling and accessing a Keysight EXR Series Oscilloscope

    NOTE: This is a cost-reduced version of the MXR series, so it uses MXR as a Parent Class. 
    NOTE: I do not have access to an EXR Oscilloscope so guessing at how this should be.
    """

    def __init__(self, resource, maxChannel=4, wait=0):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        maxChannel - number of channels of this oscilloscope
        wait       - float that gives the default number of seconds to wait after sending each command
        """
        super(EXR, self).__init__(resource, maxChannel, wait)

        # Give the Series a name
        self._series = 'EXR'
        
class EXRxx8A(EXR):
    """Child class of Keysight for controlling and accessing a Keysight EXRxx8A 8-Channel Oscilloscope"""

    maxChannel = 8

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(EXRxx8A, self).__init__(resource, maxChannel=EXRxx8A.maxChannel, wait=wait)

class EXRxx4A(EXR):
    """Child class of Keysight for controlling and accessing a Keysight EXRxx4A 4-Channel Oscilloscope"""

    maxChannel = 4

    def __init__(self, resource, wait=0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(EXRxx4A, self).__init__(resource, maxChannel=EXRxx4A.maxChannel, wait=wait)


