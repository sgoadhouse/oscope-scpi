# oscope-scpi

My organization was lucky enough to gain new oscilloscopes. They are also HP/Agilent/Keysight oscilloscopes and they also use SCPI commands but they are newer and unfortunately (or maybe I will learn it is fortunate), many of the syntax of the commands changed. Plus these new scopes have expanded abilities and therefore have expanded commands. Therefore, I mirrored my [MSO-X 3000A specific project](https://github.com/sgoadhouse/msox3000) to this one to be more generic and allow me to expand to other types of oscilloscopes.

So consider the old msox3000 project to be dead and future work will go into this project.

The below documentation is currently the old, mxso3000 specific documentation but much of it is still spplicable.

# msox3000 [OLD]

Control of HP/Agilent/Keysight MSO-X/DSO-X 3000A Oscilloscope through python via PyVisa

Using my previous work on dcps as a guide, this is intended to be a
generic package to control various Oscilloscopes. However, it is
expected that very few oscilloscopes share the same commands so start
off as a python Class specifically for the MSO-X/DSO-X 3000A
Oscilloscope. So will start targeted toward that family of
oscilloscope with a common SCPI.py Class. If it proves useful for
other oscilloscopes, then will create a new project but at least this
one would have started with that in mind.

It may also work on the MSO-X/DSO-X 2000A oscilloscope
but I have not looked into the differences to know for sure. Try it
out and let me know.

Like dcps, this will use the brilliant PyVISA python package along
with the PyVisa-PY access mode which eliminates the need for the (very
buggy) VISA library to be installed on your computer. 

# Installation [OLD]
To install the msox3000 package, run the command:

```
python setup.py install
```

Alternatively, can add a path to this package to the environment
variable PYTHONPATH or even add the path to it at the start of your
python script. Use your favorite web search engine to find out more
details. If you follow this route, you will need to also install all
of the dependant packages which are shown below under Requirements.

Even better, msox3000 is on PyPi. So
you can simply use the following and the required dependancies should
get installed for you:

```
pip install msox3000
```

## Requirements [OLD]
* [python](http://www.python.org/)
   * pyvisa no longer supports python 2.7+ so neither does this package - use older version of MSOX3000 if need python 2.7+
* [pyvisa 1.11.3](https://pyvisa.readthedocs.io/en/stable/)
* [pyvisa-py 0.5.1](https://pyvisa-py.readthedocs.io/en/latest/) 
* [argparse](https://docs.python.org/3/library/argparse.html) 
* [quantiphy 2.3.0](http://quantiphy.readthedocs.io/en/stable/) 

With the use of pyvisa-py, should not have to install the National
Instruments VISA driver.

## Features [OLD]

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

* The only supported channels are the analog channels, '1', '2', etc., as well as 'POD1' for digital 0-7 and 'POD2' for digital 8-15
* Reading of all available single channel measurements 
* Reading of all available DVM measurements 
* Installing measurements to statistics display
* Reading data from statistics display
* Screen Hardcopy to PNG image file
* Reading actual waveform data to a csv file including for 'POD1' and 'POD2'
* Saving oscilloscope setup to a file
* Loading oscilloscope setup from saved file
* Issuing Autoscale for channel(s) for all analog as well as 'POD1' and 'POD2' 
* Screen Annotation
* Channel Labels for only the analog channels

It is expected that new interfaces will be added over time to control
and automate the oscilloscope. The key features that would be good to
add next are: support for Digital/Math/etc. channels, run/stop
control, trigger setup, horizontal and vertical scale control, zoom
control

## Channels [OLD]
Almost all functions require a target channel. Once a channel is passed into a function, the object will remember it and make it the default for all subsequence function calls that do not supply a channel. The channel value is a string or can also be a list of strings, in the case of setupAutoscale(). Currently, the valid channel values are:
* '1' for analog channel 1
* '2' for analog channel 2
* '3' for analog channel 3 if it exists on the oscilloscope
* '4' for analog channel 4 if it exists on the oscilloscope
* 'POD1' for the grouping of digital channels 0-7 on a MSO model
* 'POD2' for the grouping of digital channels 8-15 on a MSO model

## Usage and Examples [OLD]
The code is a basic class for controlling and accessing the
supported oscilloscopes.

The examples are written to access the oscilloscope over
ethernet/TCPIP. So the examples need to know the IP address of your
specific oscilloscope. Also, PyVISA can support other access
mechanisms, like USB. So the examples must be edited to use the
resource string or VISA descriptor of your particular
device. Alternatively, you can set an environment variable, MSOX3000\_IP to
the desired resource string before running the code. If not using
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
# Lookup environment variable MSOX3000_IP and use it as the resource
# name or use the TCPIP0 string if the environment variable does
# not exist
from msox3000 import MSOX3000
from os import environ
resource = environ.get('MSOX3000_IP', 'TCPIP0::172.16.2.13::INSTR')

# create your visa instrument
instr = MSOX3000(resource)
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
instr.annotateColor("CH{}".format(instr.channel))
instr.annotate('{}\\n{} {}'.format('Example of Annotation','for Channel',instr.channel))

# Change label of the channel to "MySig"
instr.channelLabel('MySig')

# Make sure the statistics display is showing for the hardcopy
instr._instWrite("SYSTem:MENU MEASure")
instr._instWrite("MEASure:STATistics:DISPlay ON")

## Save a hardcopy of the screen to file 'outfile.png'
instr.hardcopy('outfile.png')

# Change label back to the default and turn it off
instr.channelLabel('{}'.format(instr.channel))
instr.channelLabelOff()

# Turn off the annotation
instr.annotateOff()
    
# turn off the channel
instr.outputOff()

# return to LOCAL mode
instr.setLocal()

instr.close()
```

## Taking it Further [OLD]
This implements a small subset of available commands.

For information on what is possible for the HP/Agilent/Keysight MSO-X/DSO-X
3000A, see the
[Keysight InfiniiVision
3000 X-Series Oscilloscopes Programming Guide](https://www.keysight.com/upload/cmc_upload/All/3000_series_prog_guide.pdf)

For what is possible with general instruments that adhere to the
IEEE 488 SCPI specification, like the MSO-X 3000A, see the
[SCPI 1999 Specification](http://www.ivifoundation.org/docs/scpi-99.pdf)
and the
[SCPI Wikipedia](https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments) entry.

## Contact [OLD]
Please send bug reports or feedback to Stephen Goadhouse

