"""
PREPARE AND OPTIONALLY RUN GLM FOR LEVEL 2 ANALYSIS
INPUT: CONFIGURATION FILE WITH ANALYSIS PARAMETERS
PROCEDURE:  use template fsf file (created with the feat gui) and change
            placeholders to specific subject number. New fsf files are saved
            and moved into the appropriate directory per subject and analysis (ID)
            Bad subjects and runs are skipped. Every fsf file is added to a 
            template submit file that is used to send the jobs to the CONDOR
            cluster. Optionally (EXECUTE), Once a participants has been finished, the submit file is
            sent to CONDOR.

"""
import sys
import json
import os; from os import path as op
from IPython import embed as shell
import IO as io

def run(cfg):  
    """""""""""""""""""""""""""
    STEP 1: SET VARIABLES
    """""""""""""""""""""""""""    
    try: 
        baseDir = cfg['baseDir'] # root directory on server
        assert os.path.exists(baseDir)
    except AssertionError: 
        baseDir = cfg['localeBaseDir'] # root directory on server
    template = op.join(baseDir,cfg['templateDir'],cfg['templateFSF']) # template fsf file
    ID = cfg['ID'] # Key phrase of analysis that should be run
    COPES = cfg['COPES'] # Which Contrasts should be analyzed
    fsfDir = op.join(baseDir,cfg['fsfDir']) # Dir of newly created fsf files
    modelDir = op.join(baseDir,cfg['modelDir']) # Dir for newly created submit files
    templateSubmit = op.join(baseDir,cfg['templateDir'],cfg['templateSubmit']) # template submit file
    
    # load file with subject numbers and run numbers per subject
    runsPerSubjectFile = op.join(baseDir,'generalInfo',cfg['runsPerSubject']) # filename
    runsPerSubject = dict() # init container
    with open(runsPerSubjectFile, 'r') as infile:
        for x,l in enumerate(infile):
            runs = io.str2list(l)
            runsPerSubject[runs[0]] = runs[1] # add subject:run dict
    subjects = runsPerSubject.keys(); subjects.sort() #extract sub number and sort
    # load specific information which runs were empty
    emptyEVfile = op.join(baseDir,'generalInfo',cfg['emptyRuns'])
    emptyRuns = []
    with open(emptyEVfile, 'r') as infile:
		for idx,l in enumerate(infile):
			emptyRuns.append(io.str2list(l))    
            
    """""""""""""""""""""""""""
    #STEP 2: CREATE FSF and SUBFILES
    """""""""""""""""""""""""""
    for SUB in subjects:
        # First skip bad subjects
        if SUB in cfg['excl_subj']:
            continue
        # create folders if not yet existent
        if not op.exists(op.join(modelDir%(SUB),'%s'%ID)): # submit dir
            print('Creating new folder %s'%(op.join(modelDir%(SUB),'%s'%ID)))
            os.system("mkdir %s"%(op.join(modelDir%(SUB),'%s'%ID)))
        # copy submit template to subject specific dir
        submitfile = op.join(modelDir%SUB,'sub-%02d_%s_2ndlvl.submit'%(SUB,ID))
        os.system('sed -e "s/##SUB##/%02d/g" < %s > %s'%(SUB,templateSubmit,submitfile))
        
        # loop over runs and create fsf files
        for RUN in range(1,runsPerSubject[SUB]+1):
            # define the output fsf filename
            outfile = op.join(fsfDir%(SUB,ID),'sub-%02d_run-%02d_%s.fsf'%(SUB,RUN,ID))
            # make fsf files
            os.system('sed -e "s/##SUB##/%02d/g; s/##RUN##/%02d/g" < %s > %s'%(SUB,RUN,template,outfile))
            # add fsf file to submit file
            with open(submitfile, 'a') as out:
                out.write("\narguments = fsf/%s/sub-%02d_run-%02d_%s.fsf\n"%(ID,SUB,RUN,ID))
                out.write("queue")
        # if wished submit jobs to condor
        if cfg['execute']:
            os.system("condor_submit %s"%submitfile)
        print('Finished participant %02d'%SUB)

# populate files
#for SUB in $(seq -f "%02g" 1 $subs);do
#	sed -e "s/##SUB##/$SUB/g; s/##ID##/$ID/g" < $1 > sub-${SUB}/models/sub-${SUB}_${ID}_${LVL}.submit
#done

if __name__== '__main__':
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
    run(cfg)