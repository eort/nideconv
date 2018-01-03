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

    ID = cfg['analID'] # Key phrase of analysis that should be run
    try: 
        copes = cfg['copes'] # How many contrasts are there
    except KeyError: 
        nCopes = cfg['nCopes'] # How many contrasts are there
        copes = range(1,nCopes+1)
    fsfDir = op.join(baseDir,cfg['fsfDir']) # Dir of newly created fsf files
    infoDir = op.join(baseDir,cfg['infoDir']) # Dir of newly created fsf files
    modelDir = op.join(baseDir,cfg['modelDir']) # Dir for newly created submit files
    templateSubmit = op.join(baseDir,cfg['templateDir'],cfg['templateSubmit']) # template submit file
    FIR_TR = cfg['FIR_TR']
    FIR_Factor = cfg['FIR_Factor']
    # load file with subject numbers and run numbers per subject
    runsPerSubjectFile = op.join(infoDir,cfg['runsPerSubject']) # filename
    runsPerSubject = dict() # init container
    with open(runsPerSubjectFile, 'r') as infile:
        for x,l in enumerate(infile):
            runs = io.str2list(l)
            runsPerSubject[runs[0]] = runs[1] # add subject:run dict
    subjects = runsPerSubject.keys(); subjects.sort() #extract sub number and sort
    # load specific information which runs were empty
    emptyEVfile = op.join(infoDir,cfg['emptyRuns'])
    emptyRuns = {'%02d'%i:[] for i in range(1,25)}
    with open(emptyEVfile, 'r') as infile:
        for x,l in enumerate(infile):
            llist = l.split()
            emptyRuns[llist[0]].append(llist[1:])
    copeDependencies = op.join(infoDir,cfg['copeDependencies']%ID)
    copeDepend = {}
    with open(copeDependencies, 'r') as infile:
        for x,l in enumerate(infile):
            llist = l.split()
            copeDepend[llist[0]] = llist[1:]

    """""""""""""""""""""""""""
    #STEP 2: CREATE FSF and SUBFILES
    """""""""""""""""""""""""""
    for SUB in subjects:
        # First skip bad subjects
        if SUB in cfg['excl_subj']:
            continue
        subModelDir = op.join(modelDir%SUB,'2ndlvl/%s'%ID)

        # create output directory if not yet existent
        if not op.exists(subModelDir): # submit dir
            os.makedirs(subModelDir)
            print('Creating new folder %s'%(subModelDir))
        if not op.exists(fsfDir%(SUB,ID)): # submit dir
            print('Creating new folder %s'%(fsfDir%(SUB,ID)))
            os.makedirs(fsfDir%(SUB, ID))
        # copy submit template to subject specific dir
        submitfile = op.join(modelDir%SUB,'sub-%02d_%s_2ndlvl.submit'%(SUB,ID))
        os.system('sed -e "s/##SUB##/%02d/g ; s/##ID##/%s/g" < %s > %s'%(SUB,ID,templateSubmit,submitfile))

        # loop over runs and create fsf files
        for COPE in copes:
            goodRuns = range(1,runsPerSubject[SUB]+1)
            badRuns = emptyRuns['%02d'%SUB]
            requiredEV = copeDepend['%s'%COPE]
            for r in badRuns:
                if r[1] in requiredEV:
                    try:
                        goodRuns.remove(int(r[0]))
                    except:
                        print 'RUN %s already removed'%r
            try:
                template = op.join(baseDir,cfg['templateDir'],cfg['templateFSF_%s'%len(goodRuns)]) # template fsf file
            except KeyError as e:
                print 'TOO MANY RUNS WOULD BE REMOVED!!!'
            # define the output fsf filename
            outfile = op.join(fsfDir%(SUB,ID),'sub-%02d_cope-%02d_%s.fsf'%(SUB,COPE,ID))
            # make fsf files
            os.system('sed -e "s/##ID##/%s/g;s/##SUB##/%02d/g; s/##COPE##/%d/g" < %s > %s'%(ID,SUB,COPE,template,outfile))
            for c in range(1,FIR_TR+1):
                FIRCOPE = FIR_Factor*(COPE-1) + c 
                os.system('sed -i "s/##FIRCOPE%d##/%d/g" %s '%(c,FIRCOPE,outfile))  
            for idx,RUN in enumerate(goodRuns,1):
                os.system('sed -i "s/##RUN%s##/%02d/g" %s'%(idx,RUN,outfile))
            # add fsf file to submit file
            with open(submitfile, 'a') as out:
                out.write("\narguments = scratch/sub-%02d/fsf/2ndlvl/%s/sub-%02d_cope-%02d_%s.fsf\n"%(SUB,ID,SUB,COPE,ID))
                out.write("queue")
        # if wished submit jobs to condor
        shell()
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