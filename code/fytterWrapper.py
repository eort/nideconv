# Script to wrap around a python script and to enable condor processing
# in theory all possible scripts could work with it
# Only problem is the directory of condor submit file that is being created
# If it doesnt follow the sub,sigID, analID schema, it won't work
# Maybe this can be fixed with providing enough info in the config file
import json
import sys
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

# make submit files and shoot off
for sub in cfg['SUBS']:
    # copy template submit file to subject folder
    outDir = os.path.join(cfg['baseDir'],cfg['outDir'].format(sub=sub,sigID=cfg['sigID'],analID=cfg['analID']))
    subSubmit = os.path.join(outDir,'{pyScript}_condor.submit'.format(pyScript=cfg['pyScript'][:-3]))
    # make directory tree
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    os.system('cp {submitfile} {subSubmit}'.format(submitfile=cfg['submitfile'],subSubmit=subSubmit))
    # and edit this new submitfile with the info
    with open(subSubmit, 'a') as out:
        out.write('\narguments = code/{pyScript} {cfg} {sub}'.format(pyScript=cfg['pyScript'],cfg=jsonfile,sub=sub))
        out.write('\nqueue')
    # send away
    os.system('condor_submit {submitfile}'.format(submitfile=subSubmit))

