"""
Convert raw EYELINK edf files to ascii files. 

"""

import sys
import json
import os
from os import path as op
import glob

# load json sidecar
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


subs = cfg['subIDs'] # which subjects
baseDir = cfg['baseDir'] # what is the project folder
edfDir = cfg['edfDir'] # where are the raw edf files
outDir = cfg['outDir'] # where should the asciis be written to
converter = op.join(baseDir,cfg['converter']) # where is the converter
sampleFlag = cfg['sampleFlag'] # samples or nosamples
overwrite = cfg['overwrite'] # overwrite existing data

# per subject, find edf files, create outputfolder if not already there
# and run the converter
for SUB in subs:
	rawfiles = glob.glob(op.join(baseDir,edfDir,'sub-%02d'%SUB)+'/*.edf')
	derivFolder = op.join(baseDir,outDir%SUB)
	if not os.path.exists(derivFolder):
		os.makedirs(derivFolder)
	arguments = [derivFolder] + [sampleFlag] + rawfiles 
	os.system("echo {} | {} -p {}".format(overwrite,converter,' '.join(arguments)))