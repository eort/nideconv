"""
CONVERTS RAW ARCHIVES WITH DICOM IMAGES INTO BIDS FORMATTED NIFTIS
Find all the tar.gz files in sourcefolder and populate a condor submitfile
with the heudiconv command per participant. 
Scripts uses heudiconv_heuristics.py as well as anon_id.py to do conversion.
Optionally, you can run the conversion only for a subset, by editing the 
finished field in the json sidecar. 
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

# set/load parameters

baseDir = cfg['baseDir'] # root directory on server
rawDir = op.join(baseDir,cfg['rawDir']) # source directory
idmap = cfg['idmap'] # mapping of participants to subID
skip = cfg['skip'] # which subjects have already been converted
submitfile = op.join(baseDir,cfg['templateDir'],cfg['dicomConversion'])# where to create the outputfile
commandTemplate = cfg['heudiConvCommand']#what command to use for conversion
condorOverhead = cfg['condorOverhead']# some initial stuff for condor submitfile
# find all the raw files
rawDicoms = [op.basename(tar) for tar in glob.glob(rawDir + '/*.tar.gz')]

# initialize submit file
with open(submitfile, 'w') as out:
    out.write("{}".format(condorOverhead))
# loop over raw file, skip some ones, and write conversion to submitfile
for raw in rawDicoms:
    if idmap[raw[:4]] in skip:
        continue
    command = commandTemplate%raw
    with open(submitfile, 'a') as out:
        out.write("\n\narguments = {}\nqueue".format(command))
# execute conversion
if cfg['submitCondor']:
    os.system("condor_submit %s"%submitfile)

