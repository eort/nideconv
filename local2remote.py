"""
Change paths inside text files to either match the local or the remote dirnames
inputfile: Which file to convert
outputfile: how to store the new file
mode: loc2rem or rem2loc
"""

import os
import sys
import os.path as op
from IPython import embed as shell

def run(inputfile,mode,outputfile):
    # set what to replace with what
    if mode == 'rem2loc':
        key = '/home/data/exppsy/ora_Amsterdam/'
        repl = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/exppsy/ora_Amsterdam/'
    elif mode == 'loc2rem':
        repl = '/home/data/exppsy/ora_Amsterdam/'
        key = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/exppsy/ora_Amsterdam/'
    # use command line sed to do conversion
    os.system('sed -e "s~%s~%s~g" < %s > %s'%(key,repl,inputfile,outputfile))
            
if __name__ == '__main__':
    # Check inputs
    try:
        	inputfile = op.abspath(sys.argv[1]) 
    except IndexError:
        print('You need to specify configuration file for this analysis')
        sys.exit()   
    try:
        	mode = sys.argv[2]
    except IndexError:
        mode = 'rem2loc'
        print('Convert to locale (default)')  
    try:
        	outputfile = op.abspath(sys.argv[3]) 
    except IndexError:
        infile, extension = op.splitext(inputfile)
        outputfile = infile + '_'+ mode[-3:] + extension
        print('Use default outputfile ')              
    # run replacement 
    run(inputfile,mode,outputfile)
