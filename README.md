# oscope-scpi

My organization was lucky enough to gain new oscilloscopes. They are
also HP/Agilent/Keysight oscilloscopes and they also use SCPI commands
but they are newer and unfortunately (or maybe I will learn it is
fortunate), much of the syntax of the commands changed. Plus these new
scopes have expanded abilities and therefore have expanded
commands. Therefore, I mirrored my [MSO-X 3000A specific
project](https://github.com/sgoadhouse/msox3000) to this one to be
more generic and allow me to expand to other types of oscilloscopes.

So consider the old msox3000 project to be dead and future work will
go into this project.

# Description

Control of Oscilloscopes with SCPI Command Sets through python via PyVisa

This uses the brilliant PyVISA python package along with the PyVisa-PY
access mode which eliminates the need for the (very buggy, in my
experience) VISA library to be installed on your computer. However,
PyVISA-PY does require `libusb` which is useful for FTDI control and
other things.

The intent is to support as many oscilloscopes as is
possible. However, I only have access to a few Keysight oscilloscopes
so that is what has been coded and tested. If you are interested in
adding support for Rigol, Tektronix or some other SCPI Oscilloscope,
then contact me for details in how to add those. Since Rigol is
suspiciously similar to Keysight, which they use to manufacture, Rigol
oscilloscopes may closely follow the Keysight DSOX/MSOX series in
dso.py and may work if dso.py is copied and modified to be specific to
Rigol.

The support for the newly released Keysight EXR Series is a complete
guess based on how similar EXR and MXR Series are. If you have an EXR
Series oscilloscope, I would be happy to hear how it works.

# Installation

To install the oscope-scpi package, clone this GIT repository and then
run the following command in the top level folder:

```
python setup.py install
```

Alternatively, can add a path to this package to the environment
variable PYTHONPATH or even add the path to it at the start of your
python script. Use your favorite web search engine to find out more
details. If you follow this route, you will need to also install all
of the dependant packages which are shown below under Requirements.

Even better, oscope-scpi is on PyPi. So you can simply use the
following and the required dependancies should get installed for you:

```
pip install oscope_scpi
```

## Requirements
* [argparse](https://docs.python.org/3/library/argparse.html) 
* [numpy 1.19.5](https://numpy.org/) 
* [python](http://www.python.org/)
   * pyvisa no longer supports python 2.7+ so neither does this package - use older version of [MSOX3000](https://github.com/sgoadhouse/msox3000) if need python 2.7+
* [pyvisa 1.11.3](https://pyvisa.readthedocs.io/en/stable/)
* [pyvisa-py 0.5.1](https://pyvisa-py.readthedocs.io/en/latest/) 
* [quantiphy 2.3.0](http://quantiphy.readthedocs.io/en/stable/) 

In order to run the example scripts `oscope.py` and `oscopeplot.py`, will also need to manually install:
* [matplotlib 3.3.4](https://matplotlib.org)
   * If cannot install `matplotlib` on your system, see the comments in `oscope.py` on how to modify it to work without `matplotlib`. 

With the use of pyvisa-py, should not have to install the National
Instruments VISA driver.

## Features

This code is not an exhaustive coverage of all available commands and
queries of the oscilloscopes. The features that do exist are mainly
ones that improve productivity like grabbing a screen hardcopy
directly to an image file on a computer with a descriptive name. This
eliminates the need to save to a USB stick with no descriptive name,
keep track of which hardcopy is which and then eventually take the USB
drive to a computer to download and attempt to figure out which
hardcopy is which. Likewise, I have never bothered to use signal
labels because the oscilloscope interface for adding the labels was
primitive and impractical. With this code, can now easily send labels
from the computer which are easy to create and update.

Currently, this is a list of the features that are supported so far:

* Support for all analog channels, '1', '2', etc.
* Support for digital channels 'POD1', 'POD2', etc.
* Support for many other analog channels like math functions and saved waveforms.
* Reading of all available single channel measurements 
* Reading of all available DVM measurements, if supported by oscilloscope
* Installing measurements to statistics display
* Reading data from statistics display
* Screen Hardcopy to PNG image file
* Reading actual waveform data to a numpy NPZ file
* Saving oscilloscope setup to a file
* Loading oscilloscope setup from saved file
* Issuing Autoscale for supported channel(s)
* Screen Annotation
* Channel Labels for only the analog channels
* Run/Stop/Single mode control

It is expected that new interfaces will be added over time to control
and automate the oscilloscope. The key features that would be good to
add next are: trigger setup, horizontal and vertical scale control,
zoom control

## Channels

Almost all functions require a target channel. Once a
channel is passed into a function, the object will remember it and
make it the default for all subsequence function calls that do not
supply a channel. The channel value is a string or can also be a list
of strings, in the case of setupAutoscale(). Currently, the valid
channel values are:

* '1' or CHAN1 for analog channel 1
* '2' or CHAN2 for analog channel 2
* '3' or CHAN3 for analog channel 3 if it exists on the oscilloscope
* '4' or CHAN4 for analog channel 4 if it exists on the oscilloscope
* '5' or CHAN5 for analog channel 5 if it exists on the oscilloscope
* '6' or CHAN6 for analog channel 6 if it exists on the oscilloscope
* '7' or CHAN7 for analog channel 7 if it exists on the oscilloscope
* '8' or CHAN8 for analog channel 8 if it exists on the oscilloscope
* 'DIFFx' where x is the channel number: Differential Channel on oscilloscopes that support this
* 'COMMx' where x is the channel number: Common-mode Channel on oscilloscopes that support this
* 'FUNCx' where x is 1-16: Function channels, like Math and FFT, etc.
* 'HIST' for Histogram
* 'WMEMx' for saved Waveforms in Memory; x starts at 1 and can go to 4 or 8
* 'POD1' for the grouping of digital channels 0-7 on a MSO/MXR/EXR model
* 'POD2' for the grouping of digital channels 8-15 on a MSO/MXR/EXR model
* 'PODALL' for the grouping of digital channels 0-15 on a MXR/EXR model
* 'BUSx' where x is 1-4: protocol busses (although have not seen this to be useful)

## Usage and Examples
The code is a basic class for controlling and accessing the
supported oscilloscopes.

The examples are written to access the oscilloscope over
ethernet/TCPIP. So the examples need to know the IP address of your
specific oscilloscope. Also, PyVISA can support other access
mechanisms, like USB. So the examples must be edited to use the
resource string or VISA descriptor of your particular
device. Alternatively, you can set an environment variable, OSCOPE\_IP
to the desired VISA resource string before running the code. If not using
ethernet to access your device, search online for the proper resource
string needed to access your device.

For more detailed examples, see:

```
oscope.py -h
```

A basic example that installs a few measurements to the statistics
display, adds some annotations and signal labels and then saves a
hardcopy to a file.

```python
# Lookup environment variable OSCOPE_IP and use it as the resource
# name or use the TCPIP0 string if the environment variable does
# not exist
from oscope_scpi import Oscilloscope
from os import environ
resource = environ.get('OSCOPE_IP', 'TCPIP0::172.16.2.13::INSTR')

# create your visa instrument
instr = Oscilloscope(resource)

# Upgrade Object to best match based on IDN string
instr = instr.getBestClass()

# Open connection to instrument
instr.open()

# set to channel 1
#
# NOTE: can pass channel to each method or just set it
# once and it becomes the default for all following calls. If pass the
# channel to a Class method call, it will become the default for
# following method calls.
instr.channel = '1'

# Enable output of channel, if it is not already enabled
if not instr.isOutputOn():
    instr.outputOn()

# Install measurements to display in statistics display and also
# return their current values here
print('Ch. {} Settings: {:6.4e} V  PW {:6.4e} s\n'.
          format(instr.channel, instr.measureVoltAverage(install=True),
                     instr.measurePosPulseWidth(install=True)))

# Add an annotation to the screen before hardcopy
instr.annotate("{} {} {}".format('Example of Annotation','for Channel',instr.channel), 'ch1')

# Change label of the channel to "MySig1"
instr.channelLabel('MySig1')

# Make sure the statistics display is showing for the hardcopy
instr.measureStatistics()

# STOP Oscilloscope (not required for hardcopy - only showing example of how to do it)
instr.modeStop()

# Save a hardcopy of the screen to file 'outfile.png'
instr.hardcopy('outfile.png')

# SINGLE mode (just an example)
instr.modeSingle()

# Change label back to the default
#
# NOTE: can use instr.channelLabelOff() but showing an example of sending a SCPI command directly
instr._instWrite('DISPlay:LABel OFF')

# RUN mode (since demo Stop and Single, restore Run mode)
instr.modeRun()

# Turn off the annotation
instr.annotateOff()
    
# turn off the channel
instr.outputOff()

# return to LOCAL mode
instr.setLocal()

instr.close()
```

## Taking it Further
This implements a small subset of available commands.

For information on what is possible for the HP/Agilent/Keysight MSO-X/DSO-X
3000A, see the
[Keysight InfiniiVision
3000 X-Series Oscilloscopes Programming Guide](https://www.keysight.com/us/en/assets/9018-06894/programming-guides/9018-06894.pdf)

For the Keysight MXR/EXR-Series Oscilloscopes, see [Keysight Infiniium MXR/EXR-Series Oscilloscopes
Programmer's Guide](https://www.keysight.com/us/en/assets/9018-18183/programming-guides/9018-18183.pdf)

For the Keysight UXR-Series Oscilloscopes, see [Keysight Infiniium UXR-Series Oscilloscopes
Programmer's Guide](https://www.keysight.com/us/en/assets/9018-07723/programming-guides/9018-07723.pdf)

For what is possible with general instruments that adhere to the
IEEE 488 SCPI specification, like the MSO-X 3000A, see the
[SCPI 1999 Specification](http://www.ivifoundation.org/docs/scpi-99.pdf)
and the
[SCPI Wikipedia](https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments) entry.

## Contact
Please send bug reports or feedback to Stephen Goadhouse

