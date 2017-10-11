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


def run(inputfile,outputfile,mode = rem2loc):
    pass

if __name__ == '__main__':
    
    try:
    	inputfile = op.abspath(sys.argv[1])    
    
    
    
        try:
        jsonfile = sys.argv[1]
    except IndexError:
        print('You need to specify configuration file for this analysis')
        sys.exit()
    try:
        with open(jsonfile) as data_file:    
            cfg = json.load(data_file)
    except IOError as e:
        print "The provided file does not exist. Either put a default .json file "\
        "in the directory of this script, or provide a valid file in the command line."
        sys.exit()
    run(inputfile,outputfile,mode)
try:
	inputfile = op.abspath(sys.argv[1])
except IndexError as e:
    parentDir = '/home/data/exppsy/ora_Amsterdam'
    #parentDir = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/exppsy/ora_Amsterdam/'
    print 'Use default path %s'%parentDir