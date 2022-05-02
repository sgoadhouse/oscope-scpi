#!/usr/bin/env python

# Copyright (c) 2018,2019,2020,2021, Stephen Goadhouse <sgoadhouse@virginia.edu>
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
#  Plot NPZ waveform output file from oscope.py
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import sys

try:
    import matplotlib.pyplot as plt
except:
    print('matplotlib.pyplot is needed for plotting waveform data to screen')
    print('Please install it with "pip install matplotlib".\n')
    sys.exit(-1)

filename = sys.argv[1]

header=None
meta=None
with np.load(filename) as data:
    x = data['x']
    y = data['y']
    if 'header' in data.files:
        header = data['header']
    if 'meta' in data.files:
        meta = data['meta']

if (meta is not None):
    print('\nMeta:\n',meta)

if (len(x) == len(y)):
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.plot(x, y)      # plot the data
    ax1.axvline(x=0.0, color='r', linestyle='--')
    ax1.axhline(y=0.0, color='r', linestyle='--')
    ax1.set_title('Waveform Data')
    if header is not None:
        ax1.set_xlabel(header[0])
        ax1.set_ylabel(header[1])

    # plot a histogram of the data
    num_bins = 250
    n, bins, patches = ax2.hist(y, num_bins)
    ax2.set_title('Histogram of Waveform Data')

    fig.tight_layout()
    plt.show()
