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

    ID = cfg['ID'] # Key phrase of analysis that should be run
    nCopes = cfg['nCopes'] # How many contrasts are there
    nSubs = cfg['nSubs'] # How many contrasts are there
    fsfDir = op.join(baseDir,cfg['fsfDir']%ID) # Dir of newly created fsf files
    infoDir = op.join(baseDir,cfg['infoDir']) # Dir of newly created fsf files
    modelDir = op.join(baseDir,cfg['modelDir']%s) # Dir for newly created submit files
    template = op.join(baseDir,cfg['templateDir'],cfg['templateFSF']) # template fsf file
    templateSubmit = op.join(baseDir,cfg['templateDir'],cfg['templateSubmit']) # template submit file

    if not op.exists(fsfDir): # submit dir
       print('Creating new folder %s'%(fsfDir))
       os.makedirs(fsfDir)
    """""""""""""""""""""""""""
    #STEP 2: CREATE FSF and SUBFILES
    """""""""""""""""""""""""""
    for COPE in range(nCopes+1):
        # copy submit template to subject specific dir
        submitfile = op.join(fsfDir,'3rdlvl_%s.submit'%ID)
        os.system('cp %s %s'%(templateSubmit,submitfile))
        shell()             
        # define the output fsf filename
        outfile = op.join(fsfDir,'3rdlvl_%s.fsf'%(ID)
        # make fsf files
        os.system('sed -e "s/##ID##/%s/g;s/##SUB##/%02d/g; s/##COPE##/%d/g" < %s > %s'%(ID,SUB,COPE,template,outfile))
        for idx,RUN in enumerate(goodRuns,1):
            os.system('sed -i "s/##RUN%s##/%02d/g" %s'%(idx,RUN,outfile))
        # add fsf file to submit file
        with open(submitfile, 'a') as out:
            out.write("\narguments = fsf/2ndlvl/%s/sub-%02d_cope-%02d_%s.fsf\n"%(ID,SUB,COPE,ID))
            out.write("queue")
        # if wished submit jobs to condor
        if cfg['execute']:
            os.system("condor_submit %s"%submitfile)
        print('Finished participant %02d'%SUB)

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