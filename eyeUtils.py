import numpy as np
import pandas as pd
import re
from IPython import embed as shell
import itertools

def dist((x1,y1),(x2,y2)):
    """
    2-dim eukledian distance
    """
    return ((x2-x1)**2+(y2-y1)**2)**0.5


def findDist(*args):
    """
    Input: a number of (x,y) points
    Returns: a list with the cartesian distances between any of them
    """    
    dim = (len(args)*(len(args)-1))/2
    dists = np.zeros((dim,len(args[0][0])))
    perm = itertools.combinations(range(len(args)),2)
    
    for d,(idx1,idx2) in enumerate(perm):
        dists[d,:] = np.linalg.norm(zip(args[idx1][0]-args[idx2][0],args[idx1][1]-args[idx2][1]),axis=1)
    return dists 

def getTarget(df,choice,targets,ID = None):
    """
    df: Dataframe that contains columns: choice and targets
    choice: the label of a column in df. This column is used to make a binary classification
    targets: list of labels of target columns that are used to compare the content of the variables
          	that are contained in choice
    ID: identifier to complete column name that should be checked to retreive  
        the information that is used to classify. If values in choice are also columns
        in df, ID is obsolete
    Returns: which a binary series (what was fixated target1 or target2)
    """
    fixatedTarget =  pd.Series(np.nan, index=df[choice].index,name='target_category')
    for idx,ch in enumerate(df[choice]): 
        if pd.isnull(ch):
            continue
        else:
            if ID != None:
                key = ch + ID
            else:
                key = ch
            fixatedTarget.iloc[idx] = 't' + str((df[key].iloc[idx] == df[targets[1]].iloc[idx])+1)
    return fixatedTarget


def countRepetitions(ar):
    """
    Input a binary array like thing, where 0s are being counted, and 1 are used to interrup tthe coutn
    Returns an array like thing giving the number of times a certain item was repeated
    """
    new_array = np.zeros(ar.shape)
    c = 0
    for i,item in enumerate(ar):        
        if not item:
            c += 1
        else:
            c = 0
        new_array[i] = int(c)      
    return new_array

def getInterval(*args):
    """
    Input:  Crit_ar: A boolean array.
            time_ar: An array with timepoints
    Returns:    A new array, providing the time interval between two consecutive
                True values.    
    """
    #shell()
    crit_ar = args[0][args[0].columns[0]]
    time_ar = args[0][args[0].columns[1]]
    out = pd.Series(np.nan, index=time_ar.index,name='switch_interval')
    out[:] = np.nan
    # get indices
    idx =crit_ar[crit_ar==True].index
    out[idx] = time_ar.loc[idx]-time_ar.loc[idx].shift(1)
    out = pd.DataFrame(out)
    return out    


def angle(spoints,epoints):
    """
    Returns angle between two points in arc
    """
    x = epoints[0]-spoints[0]
    y = epoints[1]-spoints[1]
    return (np.arctan2(y,x) + 2*np.pi)%(2*np.pi)


def genCoordComparison(df,function,base,identifier):
    """
    Select base columns from data frame and apply the function pointwise to all matches
    between the base and columns that match identifier. Returns a list with the results from
    the function. 
    
    Currently supports angles and distances between stimuli and current fixation
    """   
    output = []
    id1,id2 = re.compile(identifier[0]),re.compile(identifier[1])
    Xs =  filter(id1.match,df.columns)
    Ys =  filter(id2.match,df.columns)
    for x,y in zip(Xs,Ys):
        output.append(function([df[base[0]],df[base[1]]],[df[x],df[y]]))
    return output

def getSwitch(series):
    """
    series: a panda series
    returns binary series where two consectuive values were the same or different
    """
 
    switch =  pd.Series(np.nan, index=series.index,name='switch')
    if switch.shape[0] == 1:
       return switch
    try:    
        switch.iloc[1:]=series!=series.shift(1)
    except:
        shell()
    # exclude NaNs
    miss = series[pd.isnull(series)].index
    if len(miss)>0:
        miss2 = miss + 1
        miss2 = miss2[miss2<max(series.index)]
        switch.loc[miss] = np.nan
        switch.loc[miss2] = np.nan
    return switch

def phaseDiff(angle1, angle2):
    """
    checks the shortest distance between two distances
    """
    return np.absolute(angle2-angle1)  
    
def getSacChoice(df,sac_angle,stim_angles, angTh = np.pi/6): 
    """
    First input is the angle of the saccade, 
    Second input is the angles of the stimuli with start point
    of saccade as reference
    Function returns, to which item the saccade was directed
    """
    #shell()
    distances = np.zeros((len(stim_angles),sac_angle.size))
    idx_ar = np.chararray((sac_angle.size))
    idx_ar[:] = 's'
    for ang_idx,ang in enumerate(stim_angles):
        #compute distance
        d = phaseDiff(sac_angle,ang)
        d_min = np.min((d,2*np.pi-d) ,axis = 0)
        distances[ang_idx] = d_min
    
    output = idx_ar
    output = idx_ar + (np.argmin(distances,axis = 0) + 1).astype('|S1')
    output[np.min(distances,axis = 0) > angTh] =  's0'
    return output