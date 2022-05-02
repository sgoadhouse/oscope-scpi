#!/usr/bin/env python3

# Copyright (c) 2018,2019,2020,2021,2022 Stephen Goadhouse <sgoadhouse@virginia.edu>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Neotion nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NEOTION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#-------------------------------------------------------------------------------
#  Handle several remote functions of Agilent/KeySight oscilloscopes
#
# Using my new oscope_scpi Class
#
# pyvisa 1.11.3 (or higher) (http://pyvisa.sourceforge.net/)
# pyvisa-py 0.5.1 (or higher) (https://pyvisa-py.readthedocs.io/en/latest/)
#
# NOTE: pyvisa-py replaces the need to install NI VISA libraries
# (which are crappily written and buggy!) Wohoo!
#
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import random
import sys
import argparse

from datetime import datetime

PLOT = True
if (PLOT):
    try:
        import matplotlib.pyplot as plt
    except:
        print('matplotlib.pyplot is needed for plotting waveform data to screen')
        print('(very convenient). Please install it with "pip install matplotlib".\n')
        print('If you do not want to install this very useful Python')
        print('package, then change line "PLOT = True" to "PLOT = False" in')
        print('the file "oscope.py"')
        sys.exit(-1)
    
    
from oscope_scpi import Oscilloscope

def handleFilename(fname, ext, unique=True, timestamp=True):

    # If extension exists in fname, strip it and add it back later
    # after handle versioning
    ext = '.' + ext                       # don't pass in extension with leading '.'
    if (fname.endswith(ext)):
        fname = fname[:-len(ext)]

    # Make sure filename has no path components, nor ends in a '/'
    if (fname.endswith('/')):
        fname = fname[:-1]
        
    pn = fname.split('/')
    fname = pn[-1]
        
    # Assemble full pathname so files go to ~/Downloads    if (len(pp) > 1):
    pn = os.environ['HOME'] + "/Downloads"
    fn = pn + "/" + fname

    if (timestamp):
        # add timestamp suffix
        fn = fn + '-' + datetime.now().strftime("%Y%0m%0d-%0H%0M%0S")

    suffix = ''
    if (unique):
        # If given filename exists, try to find a unique one
        num = 0
        while(os.path.isfile(fn + suffix + ext)):
            num += 1
            suffix = "-{}".format(num)

    fn += suffix + ext

    return fn

def parse(scope):

    parser = argparse.ArgumentParser(description='Access Agilent/KeySight MSO3034A scope')
    parser.add_argument('--hardcopy', '-y', metavar='outfile.png', help='grab hardcopy of scope screen and output to named file as a PNG image')
    parser.add_argument('--waveform', '-w', nargs=2, metavar=('channel', 'outfile.npz'), action='append',
                        help='grab waveform data of channel ('+ str(scope.chanAllValidList).strip('[]') + ') and output to named file as a Numpy NPZ file (see oscopeplot.py or oscopecsv.py)')
    parser.add_argument('--setup_save', '-s', metavar='outfile.stp', help='save the current setup of the oscilloscope into the named file')
    parser.add_argument('--setup_load', '-l', metavar='infile.stp', help='load the current setup of the oscilloscope from the named file')
    parser.add_argument('--statistics', '-t', action='store_true', help='dump to the output the current displayed measurements')
    parser.add_argument('--autoscale', '-u',  nargs='?', action='append', choices=scope.chanAllValidList,
                            help='cause selected channel to get displayed and autoscaled. Can issue multiples of this option. Leave arg blank to autoscale displayed channels.')

    if (scope.series == 'KEYSIGHT' or scope.series == 'UXR'):
        # generic KEYSIGHT series and UXR series do not support DVM,
        # but still need to be able to check args.dvm, so suppress dvm
        # from help() and if someone tries to use it, force to None to
        # prevent its use.
        parser.add_argument('--dvm', '-d', action='store_const', const=None, help=argparse.SUPPRESS)
    else:
        parser.add_argument('--dvm', '-d', nargs=1, action='append', choices=scope.chanAnaValidList,
                                help='measure and output the DVM readings of selected channel')

    parser.add_argument('--measure', '-m', nargs=1, action='append', choices=scope.chanAnaValidList,
                            help='measure and output the selected channel')
    parser.add_argument('--annotate', '-a', nargs='?', metavar='text', const=' ', help='Add annotation text to screen. Clear text if label is blank')
    parser.add_argument('--annocolor', '-c', nargs=1, metavar='color', 
                            choices=['ch'+str(x) for x in scope.chanAnaValidList] + ['dig', 'math', 'ref', 'marker', 'white', 'red'],
                            help='Set the annotation color to use. Valid values: %(choices)s')
    parser.add_argument('--label', '-b',  nargs=2, action='append', metavar=('channel', 'label'), 
                            help='Change label of selected channel (' + str(scope.chanAnaValidList).strip('[]') + ')')

    # Print help if no options are given on the command line
    if (len(sys.argv) <= 1):
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Because of how Keysight now uses Bookmarks instead of
    # annotation, must require that if annotate is given, annocolor
    # must be given or vice versa. However, if given args.annotate
    # with whitespace, it means that the user wants to turn off the
    # bookmark so allow that without annocolor.    
    if (args.annotate):
        text = args.annotate
    else:
        text = ' '
    if ((text.strip() and args.annotate and args.annocolor is None) or (args.annotate is None and args.annocolor)):
        parser.error("--annotate requires --annocolor and vice versa")
    
    return args

def main():

    # Set to the IP address of the oscilloscope
    #@@@#agilent_msox_3034a = os.environ.get('MSOX3000_IP', 'TCPIP0::172.16.2.13::INSTR')
    #@@@#agilent_mxr_058a = os.environ.get('MXR058A_IP', 'TCPIP0::172.16.2.13::INSTR')
    pyvisa_oscope = os.environ.get('OSCOPE_IP', 'TCPIP0::172.16.2.13::INSTR')
    
    ## Connect to the Oscilloscope
    scope = Oscilloscope(pyvisa_oscope)

    ## Help to use with other models. Likely will not need these three
    ## lines once get IDN strings from all know oscilloscopes that I
    ## want to use
    scope.open()
    print('Potential SCPI Device: ' + scope.idn() + '\n')
    scope.close()
    
    ## Upgrade Object to best match based on IDN string
    scope = scope.getBestClass()
    
    ## Open this object and work with it
    scope.open()
    print('Using SCPI Device:     ' + scope.idn() + ' of series: ' + scope.series + '\n')

    # parse command line options with knowledge of instrument
    args = parse(scope)
    
    if (args.dvm):
        for lst in args.dvm:
            try:
                # Save if DVM mode was enabled or not
                # measureDVM functions will enable it if it is not already
                dvmEnabledAtStart = scope.DVMisEnabled()
                
                chan = lst[0]
                acrms = scope.measureDVMacrms(chan)
                dc = scope.measureDVMdc(chan)
                dcrms = scope.measureDVMdcrms(chan)
                if (scope.series == "MSOX3" or scope.series == "DSOX3"):
                    # These series are the only ones know to support DVM:FREQ? command
                    freq = scope.measureDVMfreq(chan)
                else:
                    freq = scope.OverRange
                    
                if (acrms >= scope.OverRange):
                    acrms = 'INVALID '
                if (dc >= scope.OverRange):
                    dc = 'INVALID '
                if (dcrms >= scope.OverRange):
                    dcrms = 'INVALID '
                if (freq >= scope.OverRange):
                    freq = 'INVALID '
            
                print("Ch.{}: {: 7.5f}V ACRMS".format(chan,acrms))
                print("Ch.{}: {: 7.5f}V DC".format(chan,dc))
                print("Ch.{}: {: 7.5f}V DCRMS".format(chan,dcrms))
                if (scope.series == "MSOX3" or scope.series == "DSOX3"):
                    # These series are the only ones know to support DVM:FREQ? command
                    print("Ch.{}: {}Hz FREQ".format(chan,freq))

                # Turn off DVM mode if it was off to begin with
                if (not dvmEnabledAtStart):
                    scope.enableDVM(False)
                
            except ValueError as exp:
                print(exp)
                
    if (args.statistics):
        stats = scope.measureStatistics()

        print('\nNOTE: If returned value is >= {}, then it is to be considered INVALID\n'.format(scope.OverRange))
        print('{: ^24} {: ^12} {: ^12} {: ^12} {: ^12} {: ^12} {: ^12}'.format('Measure', 'Current', 'Mean', 'Min', 'Max', 'Std Dev', 'Count'))
        for stat in stats:
            measure = stat['label'].split('(')[0]   # pull out the measurement name from the label (which has a '(channel)' suffix)
            print('{: <24} {:>12.6} {:>12.6} {:>12.6} {:>12.6} {:>12.6} {:>12}'.format(
                stat['label'],
                scope.polish(stat['CURR'],measure),
                scope.polish(stat['MIN'],measure),
                scope.polish(stat['MAX'],measure),
                scope.polish(stat['MEAN'],measure),
                scope.polish(stat['STDD'],measure),
                stat['COUN']   # no units or polish needed here
                ))
        print()
        
    if (args.measure):        
        for lst in args.measure:
            try:
                chan = lst[0]

                print('\nNOTE: If returned value is >= {}, then it is to be considered INVALID'.format(scope.OverRange))
                print('NOTE: Have not double-checked that these entities are correct, so user must double-check')
                print('\nMeasurements for Ch. {}:'.format(chan))
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
                        # using scope.measureTbl[] dictionary, call the
                        # appropriate method to read the
                        # measurement. Also, using the same measurement
                        # name, pass it to the polish() method to format
                        # the data with units and SI suffix.
                        print('{: <24} {:>12.6}'.format(meas,scope.polish(scope.measureTblCall(meas, chan), meas)))

            except ValueError as exp:
                print(exp)
                        
    if (args.annotate):
        text = args.annotate

        # If only whitespace is passed in, then turn off the
        # annotation. Doing it this way allows leading and trailing
        # whitespace in actual annotation if there are non-whitespace
        # characters as well.
        if (not text.strip()):
            scope.annotateOff()
        else:
            # TRAN = transparent background - can also be OPAQue or INVerted
            scope.annotate(text)
            
    if (args.annocolor):
        # If the annocolor option is given, simply change the color,
        # even if not even enabled yet
        scope.annotateColor(args.annocolor[0])
        
    if (args.label):
        # step through all label options
        for nxt in args.label:
            try:
                scope.channelLabel(nxt[1], channel=nxt[0])
            except ValueError as exp:
                print(exp)
                        
    if (args.hardcopy):
        fn = handleFilename(args.hardcopy, 'png')
        
        scope.hardcopy(fn)
        print("Hardcopy Output file: {}".format(fn) )

    if (args.waveform):
        for nxt in args.waveform:
            try:
                # check the channel
                channel = nxt[0]
                if (channel in scope.chanAllValidList):

                    (x, y, header, meta) = scope.waveformData(channel)

                    # Plot received data to screen so user can see what they got before saving the file.
                    # However, if the lengths do not match, cannot plot. This can happen if channel is PODx and data are bits.
                    if (PLOT and (len(x) == len(y))):
                        print("Close the plot window to continue...")
                        fig, (ax1, ax2) = plt.subplots(1, 2)
                        ax1.plot(x, y)      # plot the data
                        ax1.axvline(x=0.0, color='r', linestyle='--')
                        ax1.axhline(y=0.0, color='r', linestyle='--')
                        ax1.set_title('Waveform Data')
                        ax1.set_xlabel(header[0])
                        ax1.set_ylabel(header[1])
            
                        # plot a histogram of the data
                        num_bins = 250
                        n, bins, patches = ax2.hist(y, num_bins)
                        ax2.set_title('Histogram of Waveform Data')
            
                        fig.tight_layout()
                        plt.show()

                    # Use NPZ files which write in under a second instead of bulky csv files
                    if False:
                        fn = handleFilename(nxt[1], 'csv')
                        dataLen = scope.waveformSaveCSV(fn, x, y, header, meta)
                    else:
                        fn = handleFilename(nxt[1], 'npz')
                        dataLen = scope.waveformSaveNPZ(fn, x, y, header, meta)
                    print("Waveform Output of Channel {} in {} points to file {}".format(channel,dataLen,fn))
                else:
                    print('INVALID Channel Value: {}  SKIPPING!'.format(channel))
            except ValueError as exp:
                print(exp)
                        
    if (args.setup_save):
        fn = handleFilename(args.setup_save, 'stp')
        
        dataLen = scope.setupSave(fn)
        print("Oscilloscope Setup bytes saved: {} to '{}'".format(dataLen,fn) )

    if (args.setup_load):
        fn = handleFilename(args.setup_load, 'stp', unique=False, timestamp=False)

        if(not os.path.isfile(fn)):
            print('INVALID filename "{}" - must be exact and exist!'.format(fn))
        else:
            dataLen = scope.setupLoad(fn)
            print("Oscilloscope Setup bytes loaded: {} from '{}'".format(dataLen,fn) )

    if (args.autoscale):
        try:
            # If no argument, chans will be a list with None
            if (args.autoscale[0] is None):
                chans = None
            else:
                chans = [scope.channelStr(x) for x in args.autoscale]
            scope.setupAutoscale(chans)
        except ValueError as exp:
            print(exp)
                
    # a simple test of enabling/disabling the channels
    if False:
        wait = 0.5 # just so can see if happen
        for chan in range(1,5):
            scope.outputOn(chan,wait)

            for chanEn in range(1,5):
                if (scope.isOutputOn(chanEn)):
                    print("Channel {} is ON.".format(chanEn))
                else:
                    print("Channel {} is off.".format(chanEn))
            print()

        for chan in range(1,5):
            scope.outputOff(chan,wait)

            for chanEn in range(1,5):
                if (scope.isOutputOn(chanEn)):
                    print("Channel {} is ON.".format(chanEn))
                else:
                    print("Channel {} is off.".format(chanEn))
            print()

        scope.outputOnAll(wait)
        for chanEn in range(1,5):
            if (scope.isOutputOn(chanEn)):
                print("Channel {} is ON.".format(chanEn))
            else:
                print("Channel {} is off.".format(chanEn))
        print()

        scope.outputOffAll(wait)
        for chanEn in range(1,5):
            if (scope.isOutputOn(chanEn)):
                print("Channel {} is ON.".format(chanEn))
            else:
                print("Channel {} is off.".format(chanEn))
        print()



    print('Done')
    scope.close()


if __name__ == '__main__':
    main()
