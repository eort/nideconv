"""
Wrapper function 
"""
import json
import pandas as pd
import os.path as op

from IPython import embed as shell

# load configuration file
try:
	jsonfile = sys.argv[1]
except IndexError as e:
	jsonfile = '/home/data/foraging/derivatives/configFiles/nipype/GLM_1stlvl_nipype.json'
try:	
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
except IOError as e:
        print("The provided file does not exist. Either put a default .json file \
        in the directory of this script, or provide a valid file in the command line.")
        sys.exit(-1)

# create variables
baseDir = cfg['baseDir']
participantInfo = pd.read_csv(op.join(baseDir,cfg['participantInfo']),sep = '\t')

for idx, row in participantInfo.iterrows():
    cfg['SUB'] = row.participant_id.split('-')[-1]
    cfg['RUNS'] = row.noRuns
    if cfg['INCLUDE']:
        pu.createSubjectWorkflow(cfg)

