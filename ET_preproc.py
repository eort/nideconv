# -*- coding: utf-8 -*-
"""
Merging all subjects csv file into one data_frame. 
Running preprocessing steps 
Stats?
"""
import os
import sys
import glob
import pandas as pd
from IPython import embed as shell
import IO as io
import eyeUtils as eu
import numpy as np
import json
    
""""""""""""""""""
"""MAIN SCRIPT"""
""""""""""""""""""
def run(cfg):
    # set paths
    baseDir = cfg['baseDir']

    # load variable names
    fixatedTarget = cfg["fixatedTarget"]    
    target1 = cfg["target1"]   
    target2 = cfg["target2"]   
    
    # read files
    #filePatt = re.compile(baseDir)
    #eyefiles = [f for root, subFolders, files in os.walk(baseDir) if filePatt.match(files)]
    eyefiles = glob.glob(baseDir+'sub-*'+'/'+cfg["eyeDir"]+'/'+'*_edf.csv')
    csvfiles = glob.glob(baseDir+'sub-*'+'/'+cfg["behavDir"]+'/'+'*.csv')
    eyefiles.sort();csvfiles.sort()


    ##################################################
    #Load data, add variables and combine data frames
    ##################################################
    include_col = cfg['relevantColumns'] # which columns of behaviour should be read
    for fIdx in range(len(eyefiles)):
        f = os.path.basename(eyefiles[fIdx])
        print "Starting merging file: %s"%f
        compDir = os.path.join(baseDir,'sub-%.2i'%int(f[4:6]),cfg['compDir'])
        io.makeDirs(compDir)
        writepath = os.path.join(compDir,f[:-7]+'comp.csv') #outpath

        eye_data =pd.read_csv(eyefiles[fIdx],header=0,index_col = None) # parsed eye
        trial_data=pd.read_csv(csvfiles[fIdx],header=0,index_col = None,na_values="None",usecols =include_col) # OS output    
       
        # temporary block count fix
        # fix for wrong fixated index for first 4 runs of subject 1 (increase index by one, unless it is a timeout)
        if f in ['sub-01-01_edf.csv','sub-01-02_edf.csv','sub-01-03_edf.csv','sub-01-04_edf.csv']:
            trial_data[fixatedTarget].loc[trial_data['trial_duration']<2950] =  's' +(pd.to_numeric(trial_data[fixatedTarget].loc[trial_data['trial_duration']<2950].str[-1])+1).astype(str)
        trial_data[fixatedTarget].replace('s0',np.nan,inplace=True)

        # if a trial was stopped due to exceeding of time limit, the last good
        # trial number was reset to 1. The next two lines fix that. 
        termIdx = trial_data.loc[trial_data.terminated == 1].index
        trial_data.loc[termIdx,"trial_no"] = list(trial_data.trial_no.loc[termIdx-1]+1) # don't know why I have to wrap it into a list
        trialBlocks =  trial_data.block_no.unique()
        eyeBlocks = eye_data.block_no.unique() 
        try:
            trial_data["block_no"].replace(trialBlocks,eyeBlocks,inplace=True)
        except ValueError:
            trialBlocks = np.insert(trialBlocks,0,-99)
            trial_data["block_no"].replace(trialBlocks,eyeBlocks,inplace=True)
        trial_data.run_no = int(f[7:9]) # make sure run number is correct

        trial_data['target_category'] = eu.getTarget(trial_data,fixatedTarget,[target1,target2],'_color')
        trial_data['switch'] = trial_data.groupby(['subject_nr','block_no'])['target_category'].apply(eu.getSwitch) # time between successive switches
        trial_data['no_rep'] = trial_data.groupby(['subject_nr','block_no'])['switch'].transform(eu.countRepetitions) # number of repetitions
        trial_data['switch_interval'] = trial_data.groupby(['subject_nr','block_no'])['switch','stim_on'].apply(eu.getInterval) # time between successive switches
        trial_data['dists'] = eu.findDist([trial_data['s1_x'],trial_data['s1_y']],[trial_data['s2_x'],trial_data['s2_y']],[trial_data['s3_x'],trial_data['s3_y']]).min(axis=0)
        trial_data['conflict'] = trial_data['dists']<90
        raw_data = pd.merge(eye_data,trial_data,on=['subject_nr','run_no','block_no','trial_no'])
        
        raw_data["RT"] = pd.Series(raw_data.sacLatency,name = "RT")
        raw_data.RT.loc[raw_data.resp_saccade>1]  = raw_data.corrSacLat.loc[raw_data.resp_saccade>1]
        # add RT outliers
        l = lambda x: (x- x.mean(skipna = True)) /x.std(skipna = True)
        raw_data["zRT"]=raw_data.groupby(['subject_nr','block_no'])['RT'].transform(l)
        raw_data["outlier"]=np.abs(raw_data["zRT"])>3

        stim_angles = eu.genCoordComparison(raw_data,eu.angle,['end_prev_x','end_prev_y'],['s[12345]_x','s[12345]_y'])  
        stim_dists = eu.genCoordComparison(raw_data,eu.dist,['s_cur_x','s_cur_y'],['s[12345]_x','s[12345]_y'])  
        # compute eye position related variables
        for idx in range(len(stim_angles)):
            label_ang = 'angle_to_s%s'%(idx+1)
            label_dist = 'dist_to_s%s'%(idx+1)
            raw_data[label_ang] = stim_angles[idx]
            raw_data[label_dist] = stim_dists[idx]

        raw_data["sac_to_S"] = eu.getSacChoice(raw_data,raw_data.sac_angle,stim_angles) 
        raw_data["sac_to_S"].loc[raw_data["sac_amplitude"]<1]= 's0'
        raw_data["block_no"].replace(-99,np.nan,inplace=True)
        # write final file per subject
        raw_data.to_csv(writepath,index=False,na_rep="nan")     
        print "Merging file %s succesfully finished"%os.path.basename(eyefiles[fIdx])

if __name__ == '__main__':  
    if len(sys.argv)<2:
        jsonfile = 'cfg.json'
    else:
        jsonfile = sys.argv[1]
    try:
        with open(jsonfile) as data_file:    
            cfg = json.load(data_file)
        data_file.close()
    except IOError as e:
        print "The provided file does not exist. Either put a default .json file "\
        "in the directory of this script, or provide a valid file in the command line."
    run(cfg)
