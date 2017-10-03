#!/usr/bin/python
"""
Convert Philips physiology log files into a format suitable for noise modeling

The challenge is that Philips log files do not contain information on the start
of a volume acquisition (trigger). This information is necessary for
physiological noise modeling of BOLD imaging data. Moreover, the log files also
do not contain a reliable marker that indicated the start of the first scan
volume.

This converter uses the marker that indicates the end of a scan and
reconstructs a trigger pulse train from a given TR value for any given number
of volumes.

Arguments:

    1. volume repetition time in milliseconds (float)
    2. number of volumes in scan (int)
    3. input file name
    4. output file name (compressed if ends with '.gz')

The output file is a space-separated text file with one line per sample and
three columns (all integer):

    1. Trigger (1 for a pulse, 0 elsewhere)
    2. Pleth pulse (PPU)
    2. Respiration (resp)

The sampling rate is alway 500 Hz, as in the original log file. Note, however,
that the effective sampling rate is only 100 Hz.

Example:

    philipsphysioconv 2000 156 SCANPHYSLOG20140718114711.log.gz sub124.log.gz
"""
import os
import glob

fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/models/2ndlvl/search*+.gfeat')
for f in fil:
    os.system("rm -r %s"%f)
