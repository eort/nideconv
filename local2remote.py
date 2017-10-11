"""
Change paths inside text files to either match the local or the remote dirnames
inputfile: Which file to convert
outputfile: how to store the new file
mode: loc2rem or rem2loc
"""

import os
import sys
import os.path as op
import glob
from IPython import embed as shell
import subprocess


def run(inputfile,outputfile,mode = 'rem2loc'):
    
    if mode == 'rem2loc':
        key = '/home/data/exppsy/ora_Amsterdam'
        repl = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/exppsy/ora_Amsterdam/'
    elif mode == 'loc2rem':
        repl = '/home/data/exppsy/ora_Amsterdam'
        key = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/exppsy/ora_Amsterdam/'
        
    with open(inputfile,'r') as infile:
        for x,l in enumerate(infile):
            shell()
            if key in l
if __name__ == '__main__':
    # Check input
    try:
        	inputfile = op.abspath(sys.argv[1]) 
    except IndexError:
        print('You need to specify configuration file for this analysis')
        sys.exit()        
    try:
        	outputfile = op.abspath(sys.argv[2]) 
    except IndexError:
        infile, extension = op.splitext(inputfile)
        outputfile = op.join(infile,'_conv',extension)
        print('Use default outputfile ')              
    try:
        	mode = sys.argv[3]
    except IndexError:
        mode = 'rem2loc'
        print('Convert to locale (default)')        
    run(inputfile,outputfile,mode)
