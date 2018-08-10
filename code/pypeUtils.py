################################
#####   CREATE FUNCTIONS   #####
################################

def extractMaskNames(mask_file):
    """
    Extract string from filename
    """
    import os.path as op

    path,f = op.split(mask_file)
    return '_'.join(f.split('_')[:2])

def extractSignal(in_file, roi):
    """
    loads a 3d-timeseries, extracts the voxels as marked in the ROI image
    returns a 1d timeseries that is the average of all voxels in that mask
    """
    import nibabel as nib
    import numpy as np
    import os
    from IPython import embed as shell

    funcImg = nib.load(in_file) # load nifti
    signal = funcImg.get_data() # extract data

    maskImg = nib.load(roi) # load nifti
    mask = maskImg.get_data() # extract mask

    # create outfile based on subject number and roi
    in_d,in_f = os.path.split(in_file)
    sub = in_f.split('_')[0]
    mask_d,mask_f = os.path.split(roi)
    mask_id = '_'.join(mask_f.split('_')[:2])

    out_file = os.path.join(os.getcwd(),'{sub}_{roi}_timeseries.npy'.format(sub=sub,roi=mask_id))
    # select Voxels in roi and average timeseries across them
    timeseries = signal[mask.astype(bool),:].mean(axis = 0)

    np.save(out_file,timeseries)
    return out_file

def stripFilename(in_file, suffix = '_merged_runs.nii.gz'):
    """
    reduces filename to not include run_info anymore
    """
    import os.path as op
    import os
    path,f = op.split(in_file) 
    keeper = '_'.join(f.split('_')[:2])
    return op.join(keeper + suffix)#os.getcwd(),

def getmeanscale(median):
    return '-mul %.10f' % (10000. / median)

def getthreshop(value, factor):
    thr = value*factor
    return '-thr %.10f -Tmin -bin' % thr

def getThreshold(value,factor):
    """
    Thresholds an intensity value with factor
    e.g. 2000*0.10, a value of 2000 is scaled by 10%
    """
    return value*factor

def getUsans(mean,median):
    """
    combines a func file with a median value in a tuple to use as a
    USAN parameter in SUSAN
    """
    return [(mean, 0.75*median)]
    
def computePSC(in_file):
    """
    Converts a time series in a %%-signal change series
    Divide by mean of series, multiply by 100, subtract 100
    Returns a 0 centered in percent times series
    """

    import nibabel as nib
    import numpy as np
    import os.path as op
    from IPython import embed as shell

    # make output file
    base,f = op.split(in_file) 
    out_file = op.join(base,f.split('.')[0]+'_psc.nii.gz')

    # load image and extract data
    funcImg = nib.load(in_file)
    funcData = funcImg.get_data()

    #compute mean_func
    mean_func = np.nanmean(funcData,axis = 3)
    # compute psc
    funcData_psc = (np.divide(funcData-mean_func[:,:,:,np.newaxis],mean_func[:,:,:,np.newaxis],
        out=np.zeros_like(funcData), where=mean_func[:,:,:,np.newaxis]!=0)* 100)
    # store data in a nifti
    outImg = nib.Nifti1Image(funcData_psc, funcImg.affine, funcImg.header)          
    # and save it to file
    nib.save(outImg,out_file)
    return out_file


def make2ndLvlDesignMatrix(copes):
    """
    Creates a new cope structure. Instead of the 4 basic ones, 
    it will make an extended list and match all the computed 
    copes that are necessary for a certain contrast
    """
    regressors = {"reg%d"%copeI:[] for copeI,cope in enumerate(copes)}
    for copeIdx,cope in enumerate(copes):
        zeros = [0]*len(cope)
        ones = [1]*len(cope)
        regressors['reg%d'%copeIdx] = regressors['reg%d'%copeIdx] + ones
        rest = [0,1,2,3]
        rest.remove(copeIdx)
        for r in rest:
            regressors['reg%d'%r] = regressors['reg%d'%r] + zeros
    # rename the dict keys
    new_keys=['proSwitch','reSwitch','proRep','reRep']
    old_keys=['reg0','reg1','reg2','reg3']
    for new_key,old_key in zip(new_keys,old_keys):
        regressors[new_key] = regressors.pop(old_key)
    return regressors    


def makeDesignFig(design_file):
    import numpy as np
    #%matplotlib qt4
    import matplotlib.pyplot as plt
    # load design matrix
    desmtx=np.loadtxt(design_file,skiprows=5)
    # show design matrix
    plt.imshow(desmtx,aspect='auto',interpolation='nearest',cmap='gray')
    plt.savefig('design.pdf')

    # show efficiency matrix
    cc=np.corrcoef(desmtx.T)
    plt.imshow(cc,aspect='auto',interpolation='nearest', cmap=plt.cm.viridis)
    plt.colorbar()
    plt.savefig('design_ef.pdf')


def getDimSize(image,dim=3):
    """
    returns the dimension size DIM of an image
    0,1,2,3 --> x,y,z,t
    """
    import nibabel as nib
    funcImg = nib.load(image) # load nifti
    return funcImg.header.get_data_shape()[dim]

def selectFromList(aList,idx):
    """
    returns the idx-th item from the list
    """
    return aList[idx]

def setSubOutDir(sub_no,subOutDir):
    """
    Set output base folder for each subject
    Basically, replaces the formatter in the path string
    with the subject number. 
    """

    return subOutDir%sub_no

def transpose(aNestedList):
    """
    Change a list with dimension AxB into a list with BxA
    """
    import numpy as np
    return np.array(aNestedList).T.tolist()

def transposeAndSelect(aNestedList,bunch_files):
    """

    """
    import numpy as np
    validCopes = [bf.validCopes for bf in bunch_files]
    copeTypes = {0:[],1:[],2:[],3:[]} # hardcode 4 event types
    for runIdx,copelist in enumerate(validCopes):
        for copeIdx,cope in enumerate(copelist):
            if cope:
                copeTypes[copeIdx].append(aNestedList[runIdx][copeIdx])

    return [v for k,v in copeTypes.items()]

def printTerminal(info):
    print(info)
    print(type(info))

def printFile(info):
    import os
    outputfile = os.path.join('/home/data/foraging','output.txt')
    os.system("echo {} > {}".format(info,outputfile))

def mergeDesignInfo(bunch_files):
    """
    Combine Bunch files of multiple runs to each other. 
    Basically, vstack, incl. adding constant time to onsets (TR*volumes)
    returns a combined bunch object
    """
    from nipype.interfaces.base import Bunch
    import numpy as np
    import cPickle as pickle
    import os
    # initialize empty containers for all lists that run across runs
    # a little weird to make sure everyhting is deepcopied
    all_durs = [list(f) for f in bunch_files[0].durations]
    all_onsets = [list(f) for f in bunch_files[0].onsets]
    all_regressors = [list(f) for f in bunch_files[0].regressors]

    # extract those fields that are the same across runs
    regressor_names = list(bunch_files[0].regressor_names)
    conditions = bunch_files[0].conditions    

    scrubCount = 0 
    # skip the first one (already added)
    for i,bfile in enumerate(bunch_files[1:],1):
        # extract run specific values keywords
        durations = bfile.durations
        # mind onset adjustment across run
        onsets = [[i*420+s for s in f] for f in bfile.onsets]
        regressors = bfile.regressors
        # loop over sublists of onset like lists
        for d in range(len(durations)):
            all_durs[d].extend(durations[d])
            all_onsets[d].extend(onsets[d])

        # loop over sublists of volumes-like lists
        for rI,reg in enumerate(bfile.regressor_names):
            # extra attention to scrubbed volumes per run
            if 'fd_scrubs' in reg: 
                regressor_names.extend(['fd_scrubs_{}'.format(scrubCount)])
                scrubCount += 1
                new_scrub = list([0]*(len(all_regressors[0])-210) + regressors[rI])
                all_regressors.append(new_scrub)
            else:
                all_regressors[rI].extend(regressors[rI]) 
        # fix length of previously added scrubbed volumes       
        standard = len(all_regressors[0])
        for rI,reg in enumerate(all_regressors[1:],1):
            if len(reg) != standard:
                all_regressors[rI].extend(210*[0])
    sub = bunch_files[0].sub
    out_file = os.path.join(os.getcwd(),'{sub}_mergedEVs.pkl'.format(sub=sub))

    bunch = Bunch(
            conditions=conditions,
            onsets=all_onsets,
            durations=all_durs,
            regressors=all_regressors,
            regressor_names=regressor_names)

    with open(out_file,'wb') as f:
        pickle.dump(bunch,f)    
    return out_file

def createDesignInfo(evFile,confoundFile,parameters):
    """
    From the single event file, extract all the events that are 
    relevant for a certain condition/analysis
    """
    import cPickle as pickle
    import pandas as pd
    from nipype.interfaces.base import Bunch
    import os

    # load the confound file and select relevant columns
    confoundFields = parameters['confounds']
    confoundDF = pd.read_csv(confoundFile,sep = '\t',usecols=confoundFields)
    additionalConfounds = parameters['additionalConfounds']

    # perform scrubbing based on FD values. Default threshold:0.9
    if 'FD_scrubs' in additionalConfounds:
        try:
            FD_threshold = parameters['FD_threshold']
        except:
            FD_threshold = 0.9
        assert "FramewiseDisplacement" in confoundDF.columns, \
            'In order to do scrubbing based on FD, you need to include '\
            'FramewiseDisplacement in the confound tsv file.'

        # for every frame that is bigger than threshold, make a new regressor
        # with 1 for that particular frame, and 0s for all other frames
        FD_idx = confoundDF["FramewiseDisplacement"].loc[confoundDF["FramewiseDisplacement"] > FD_threshold].index
        for noFrame,frame in enumerate(FD_idx):
            fd_scrubs = [0]*parameters["nVols"]
            fd_scrubs[frame] = 1
            confoundDF["fd_scrubs_{:d}".format(noFrame)] = fd_scrubs

    # name the confound regressors for the Bunch info
    regressor_names = confoundDF.columns.tolist()
    regressors = [confoundDF[c].fillna(confoundDF[c].mean()).tolist() for c in confoundDF]

    # load event file and select relevant data
    df = pd.read_csv(evFile,sep = '\t')
    # which eventType to look at?
    trialType = parameters['trialType']
    onsetType = parameters['onsetType']
    #prepare containers
    onsets = []
    conditions = parameters['events']
    durations = []
    amplitudes = []
    validCope = []
    # populate containers
    for event in conditions:
        onset = (df['onset'].loc[(df[trialType]==event) & (df['onsetType']==onsetType)]).tolist()
        duration = (df['duration'].loc[(df[trialType]==event) & (df['onsetType']==onsetType)]).tolist()
        # allow to have the same pipeline without taking empty runs into consideration   
        if len(onset)==0:
             onset = [0]
             duration = [0]
             amplitude = [0]
        else:
            amplitude = [1]*len(onset)
        # keep track of relevant empty copes
        if event not in ['error','cue']:
            if len(onset)>1:
                validCope.append(1)
            else:
                validCope.append(0)
        onsets.append(onset)
        amplitudes.append(amplitude)
        durations.append(duration)

    in_d,in_f = os.path.split(evFile)
    sub = in_f.split('_')[0]
    run = in_f.split('_')[2]
     
    # collect everything in a Bunch object
    modelInfo = Bunch(
            sub=sub,
            conditions=conditions,
            onsets=onsets,
            amplitudes=amplitudes,
            durations=durations,
            regressors=regressors,
            regressor_names=regressor_names,
            validCopes=validCope)
    # save Bunch file
    out_file = os.path.join(os.getcwd(),'{sub}_{run}_{onset}_EVs.pkl'.format(sub=sub,run=run,onset=onsetType))
    with open(out_file,'wb') as f:
        pickle.dump(modelInfo,f)    
    return modelInfo,out_file

def getMeanRT(evBunch,meancenter =True):
    """
    Returns a list with the average saccade latencies for each participant
    across conditions. Optionally mean-centered (default yes)
    Input is a merged Bunchobject from the second level modelling
    """
    import numpy as np
    meanRT_list = []
    for bunchfile in evBunch:
        relDurations = zip(bunchfile.conditions,bunchfile.durations)
        durations = [d for c,d in relDurations if not c in ['error','cue']]
        # append the mean of all duratons to the subject file
        meanRT_list.append(np.mean([dur for d in durations for dur in d]))

    if meancenter:
        demeaned_list = [meanRT - np.mean(meanRT_list) for meanRT in meanRT_list]
    else:
        demeaned_list = meanRT_list
    return demeaned_list

def makeDM_3rdlvl(covariates = [[]]):
    """
    Takes a list of covariate lists, with as many elements as there are 
    subjects. Creates a design matrix with the covariates added to a list
    of ones (for the group average) and a contrast file
    """
    import pandas as pd

    if len(covariates) != 0:
        no_sub = len(covariates[0])
        dm = pd.DataFrame({'group':[1]*no_sub})
    for cvI,cv in enumerate(covariates):
        dm["cov-%d"%cvI] = cv

    # adding header and testing and making the contrast file and connecting to lfow
    return dm