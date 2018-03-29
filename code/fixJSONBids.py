"""
The json files for fieldmaps and functional niftis that come out of 
heudiconv miss a couple of fields. This scripts adds them to it. 

EES computed with formula: 
1000 x WFS(pixels) / wfs x ( ETL + 1 ) / acceleration
WFS = WaterFatShift
ETL = ECHO TRAIN LENGTH
wfs = based on Joerg: Radian / delta TE (2.3ms): 1/0.0023 = 434.7826
VALUES TAKES FROM SEQUENCE TXT FILES

(1000 x 12.5) / (434.7826 x(39 +1))/2 = 0.359375
"""
import sys
import json
import os
from os import path as op
import glob
from IPython import embed as shell

# load json sidecar
try:
    jsonfile = sys.argv[1]
except IndexError:
    print('You need to specify configuration file for this analysis')
    sys.exit()
try:
    with open(jsonfile) as data_file:    
        settings = json.load(data_file)
except IOError as e:
    print "The provided file does not exist. Please"\
        "provide a valid file in the command line."
    sys.exit()

# set/load parameters
baseDir = settings['baseDir'] # root directory on server
skip = settings['skip'] # which subjects have already been converted
# add info to functional json sidecars
if settings['func']:
    # find all func jsons
    func_jsons = glob.glob(baseDir + '/sub-*/func/*.json')
    # loop over them
    for func in func_jsons:
        # skip runs/subjects if necessary
        if any(["sub-{:02d}".format(sk) in func for sk in skip]):
            print("Skip nifti file {}".format(func))
            continue 
        # make them writable if not already
        os.system("chmod 660 {}".format(func))
        # extract information from jsons
        with open(func, 'r') as data_file:    
            cfg = json.load(data_file)
        # add parameters to settings json
        cfg["EffectiveEchoSpacing"] = settings["EES"]
        cfg["PhaseEncodingDirection"] = settings["PhaseEncodingDirection"]
        cfg["WaterFatShift"] = settings["WFS"]
        cfg["wfs"] = settings["wfs"]
        cfg["MagneticFieldStrength"] = settings["MagneticFieldStrength"]# maybe not necessary
        cfg["ParallelReductionFactorInPlane"] = settings["AP"]
        cfg["TaskName"] = settings["TaskName"]
        # replace original json with another one the same + added info one
        with open(func, 'w') as data_file:    
            json.dump(cfg,data_file,sort_keys=True, indent=4)

# add info to fieldmap json sidecars
if settings['fmap']:
    # find all fieldmap jsons. There are two per directory, but they are
    # identical, so changing one of them is enough
    fmap_jsons = glob.glob(baseDir + '/sub-*/fmap/*2.json')

    for fmap in fmap_jsons:
        # find epis associated with a certain field map(basically sub-specific)
        epis_full = glob.glob(baseDir + '/sub-{}/func/*.nii.gz'.format(op.basename(fmap)[4:6]))
        epis_full.sort()
        # path must be relative, so strip the root
        epis = ['func/' + op.basename(ep) for ep in epis_full ]
        # change permission if necessary
        os.system("chmod 660 {}".format(fmap))
        # load data from json
        with open(fmap, 'r') as data_file:    
            cfg = json.load(data_file)
        # add info
        cfg["IntendedFor"] = epis
        cfg["Units"] = settings["Units"]
        # already use an output file name that is BIDS compatible
        outjson = fmap[:-10]+ 'fieldmap.json'
        # write that file
        with open(outjson, 'w') as data_file:    
            json.dump(cfg,data_file,sort_keys=True, indent=4)
        # delete the original file to keep it clean
        #os.system("rm {}".format(fmap))

        # don't delete the other fieldmap as a backup maybe

