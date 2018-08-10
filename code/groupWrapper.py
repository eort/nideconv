# Script to wrap around a python script and to enable condor processing
# in theory all possible scripts could work with it
# Only problem is the directory of condor submit file that is being created
# If it doesnt follow the sub,sigID, analID schema, it won't work
# Maybe this can be fixed with providing enough info in the config file
import json
import sys
import glob
import os

from IPython import embed as shell

assert len(sys.argv)==2
try:
    jsonfile = sys.argv[1]
except:
    print "The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line."
    sys.exit(-1)
else:
    with open(jsonfile) as f:    
        cfg = json.load(f)

# further settings
baseDir = cfg['baseDir'] # root
outDir = os.path.join(baseDir,cfg['outDir'].format(analID = cfg['analID']))
if not os.path.exists(outDir):
    os.makedirs(outDir)

search_key = cfg['search_key'].format(sigID = cfg['sigID'],analID = cfg['analID'])

all_files = glob.glob(baseDir + search_key)

# get set with all ROIs from file list
all_rois = set([f.split('_')[-2] for f in all_files])

# make submit files and shoot off
for ROI in all_rois:
    # copy template submit file to subject folder
    ROISubmit = os.path.join(outDir,'{pyScript}_condor.submit'.format(pyScript=cfg['pyScript'][:-3]))
    os.system('cp {submitfile} {subSubmit}'.format(submitfile=cfg['submitfile'],subSubmit=ROISubmit))
    # and edit this new submitfile with the info
    with open(ROISubmit, 'a') as out:
        out.write('\narguments = code/{pyScript} {cfg} {ROI}'.format(pyScript=cfg['pyScript'],cfg=jsonfile,ROI=ROI))
        out.write('\nqueue')
    # send away
    os.system('condor_submit {submitfile}'.format(submitfile=ROISubmit))

