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

def run(cfg):  
    """""""""""""""""""""""""""
    STEP 1: SET VARIABLES
    """""""""""""""""""""""""""    
    try: 
        baseDir = cfg['baseDir'] # root directory on server
        assert os.path.exists(baseDir)
    except AssertionError: 
        baseDir = cfg['localeBaseDir'] # root directory on server

    ID = cfg['analID'] # Key phrase of analysis that should be run
    nCopes = cfg['nCopes'] # How many contrasts are there
    inputCopes = cfg['inputCopes']
    fsfDir = op.join(baseDir,cfg['fsfDir']%ID) # Dir of newly created fsf files
    template = op.join(baseDir,cfg['templateDir'],cfg['templateFSF']) # template fsf file
    templateSubmit = op.join(baseDir,cfg['templateDir'],cfg['templateSubmit']) # template submit file

    if not op.exists(fsfDir): # submit dir
       print('Creating new folder %s'%(fsfDir))
       os.makedirs(fsfDir)
    """""""""""""""""""""""""""
    #STEP 2: CREATE FSF and SUBFILES
    """""""""""""""""""""""""""
    # copy submit template to subject specific dir
    submitfile = op.join(fsfDir,'3rdlvl_%s.submit'%ID)
    os.system('cp %s %s'%(templateSubmit,submitfile))
    if cfg['method'] == 'old':
        for COPE in range(1,nCopes+1):
            # define the output fsf filename
            outfile = op.join(fsfDir,'%s_cope-%d.fsf'%(ID,COPE))
            os.system('sed -e "s/##ID##/%s/g; s/##COPE##/%d/g" < %s > %s'%(ID,COPE,template,outfile))
            # add fsf file to submit file
            with open(submitfile, 'a') as out:
                out.write("\narguments = scratch/group_level/%s/feats/%s_cope-%d.fsf\n"%(ID,ID,COPE))
                out.write("queue")
    elif cfg['method'] == 'new':
        outfile = op.join(fsfDir,'%s.fsf'%ID)
        os.system('cp %s %s'%(template,outfile))
        for COPE in range(1,inputCopes+1):
            # define the output fsf filename
            os.system('sed -i "s/##ID##/%s/g; s/##COPE%d##/%d/g" %s'%(ID,COPE,COPE,outfile))
        # add fsf file to submit file
        with open(submitfile, 'a') as out:
            out.write("\narguments = scratch/group_level/%s/feats/%s.fsf\n"%(ID,ID))
            out.write("queue")


    # if wished submit jobs to condor
    if cfg['execute']:
        os.system("condor_submit %s"%submitfile)
    print('Finished')

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