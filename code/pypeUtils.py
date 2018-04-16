import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe        # pypeline engine
import pypeUtils as pu
import workflows as wf
import json
import pandas as pd
import numpy as np
import sys,os
import os.path as op
from IPython import embed as shell

################################
#####   CREATE FUNCTIONS   #####
################################
def makeDesignFig(design_file):
    import numpy as np
    import matplotlib as plt 
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
    returns the dimension size DIM of an image image
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
    Set output base folder for each subject
    Basically, replaces the formatter in the path string
    with the subject number. 
    """
    import numpy as np
    return np.array(aNestedList).T.tolist()

def transposeAndSelect(aNestedList,bunch_files):
    """
    Set output base folder for each subject
    Basically, replaces the formatter in the path string
    with the subject number. 
    """
    import numpy as np
    validCopes = np.array([bf.validCopes for bf in bunch_files], dtype = bool).T.tolist()
    outList = []
    for copeIdx,copelist in enumerate(validCopes):
        subList = []
        for runIdx,c in enumerate(copelist):
            if c:
                subList.append(aNestedList[runIdx][c])
        outList.append(subList)
    return outList    

def printOutput(info):
    print(info)
    print(type(info))

def createDesignInfo(evFile,confoundFile, parameters):
    """
    From the single event file, extract all the events that are 
    relevant for a certain condition/analysis
    """
    import pandas as pd
    from nipype.interfaces.base import Bunch

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
    tType = parameters['trialType']
    #prepare containers
    onsets = []
    conditions = parameters['events']
    durations = []
    amplitudes = []
    validCope = []
    # populate containers
    for event in conditions:
        onset = (df['onset'].loc[(df[tType]==event) & (df['onsetType']=='onset')]).tolist()
        duration = (df['duration'].loc[(df[tType]==event) & (df['onsetType']=='onset')]).tolist()
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

    # collect everything in a Bunch object
    modelInfo = Bunch(
            conditions=conditions,
            onsets=onsets,
            amplitudes=amplitudes,
            durations=durations,
            regressors=regressors,
            regressor_names=regressor_names,
            validCopes = validCope)

    return modelInfo