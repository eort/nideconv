# -*- coding: utf-8 -*-
"""
Parsing EDF-based ascii files. 
Loop over subjects, based on block and trial start messages, parse stream 
of fixations and saccades into trials and blocks. 
Stores current fixation and previous fixation and & saccade information into one
row. A directory of the ascii files can be used as input. 
Uses pandas and writes everything to csv files per subject.

TODO: 

1) Make the parsing of the messages of the ascii file more robust.
    Send messages as single string, not as multiple strings. 
    
2) Move the BIDS formatting out one layer
    

"""
#import re
import os
import numpy as np
import sys
import pandas as pd
from IPython import embed as shell
import IO as io
import glob
import json
import eyeUtils as eu
   
def run(cfg):
    # read files
    baseDir = cfg['baseDir']
    eyefiles = glob.glob(baseDir+'derivatives/sub-*/'+cfg["ascDir"]+'/*.asc')
    eyefiles.sort()
    
    prev_subject = np.nan
    for fIdx in range(len(eyefiles)):
        ascf = os.path.basename(eyefiles[fIdx])
        try:        
           assert ".asc" in ascf 
        except AssertionError as e:
            print e
            continue             
        eyeDir = os.path.join(baseDir,'derivatives','sub-%.2i'%int(ascf[4:6]),cfg['eyeDir'])
        io.makeDirs(eyeDir)
        writepath = os.path.join(eyeDir,ascf[:-4]+'_edf.csv') #outpath 
        
        # load config file
        screenWidth = cfg["screen_width"]
        screenHeight = cfg["screen_height"]
        startBlock = cfg["startBlockMessage"]
        startTrial = cfg["startTrialMessage"]
        endTrial = cfg["endTrialMessage"]
        standard_coordinates = cfg["standard_coordinates"]
        
        if cfg["BIDS"]:
            subject_nr = ascf[4:6] 
            run_no = int(ascf[7:9] )
            if prev_subject != subject_nr:  
                curBlockNo = cfg["block_start"]
        else:
            subject_nr = ascf[:2] 
        
        trials = []
        block_no = curBlockNo
        blink = 0
        inSac = 0
        inTrial= 0
        blinkSac = 0
        sacPending = 0  
        trial_no =  0
        sac_no = 0
        
        fallBack_sac=dict(subject_nr=np.nan,trial_no=np.nan,run_no = np.nan,block_no=-99,\
            sac_no = np.nan,end_prev_fix= np.nan,begin_cur_fix=np.nan,\
            end_prev_x=np.nan,end_prev_y=np.nan, s_cur_x=np.nan,s_cur_y=np.nan,\
            sac_amplitude=np.nan,sac_peakVel = np.nan,blinkSac=np.nan,\
            sac_angle = np.nan,beginTrial = np.nan,inTrial = np.nan,\
            sacLatency = np.nan, corrSacLat = np.nan,OSbeginTrial=np.nan)    
        
        with open(eyefiles[fIdx], 'r') as f:
            for idx,l in enumerate(f):
                line= io.str2list(l)
                
                if len(line)== 0:
                    continue #empty lines are skipped
                
                elif line[0]=='MSG': # if it's a message check what it says and do stuff accordingly                   
                    if line[2:-1] == startBlock:#reset variables for a new block
                        block_no += 1
                        trial_no = 0
                        time_beginTrial = np.nan
                        OS_time_beginTrial = np.nan
                        
                    elif line[2:-1] == startTrial:#reset variables for a new trial                        
                        time_beginTrial = line[1] # when did trial begin
                        OS_time_beginTrial = line[-1]
                        fix_onset = line[1] # when did fixation start
                        inTrial = 1 # Now we are in a trial
                        sac_no = 0 # reset saccade index
                        resp_saccade = 1
                        trial_no += 1 # increment trial number
                        inSac = 0 # We are not (supposed) to be in a trial
                        if sacPending: # if we were waiting for a final EM, 
                            sacPending = 0 # stop waiting
        
                    elif line[2:-1] == endTrial:
                        if inSac:
                            sacPending = 1                    
                        inTrial = 0
                        if sac_no == 0 and not inSac:
                            pass#trials.append(fallBack_sac) # so every trial number appears once
         
                elif line[0]=='EBLINK':
                    blink = 1 # mark a blink
                
                elif line[0]=='SBLINK':
                    continue # do not do anything at the beginning of blink 
                        
                elif line[0]=='SSACC':
                    inSac = 1 # mark a saccade     
         
                elif line[0]=='ESACC':
                    if blink or not inSac: # if we are in a blink or not in a saccade
                        blink = 0 # reset blink and
                        if sacPending: # if trial over, but waiting for end saccade
                            sacPending = 0 # abort waiting
                        continue # dont write anything to file
                    if inTrial or sacPending:
                        sac_no+=1    
                        if (resp_saccade == sac_no) and line[9] <= 1:
                            resp_saccade +=1   
                        try: # get start and end coordinates of current saccade
                            if standard_coordinates:
                                start_x,start_y,end_x,end_y = line[5]-0.5*screenWidth,line[6]-0.5*screenHeight,line[7]-0.5*screenWidth,line[8]-0.5*screenHeight
                            else:
                                start_x,start_y,end_x,end_y = line[5],line[6],line[7],line[8]
                        except: # in case we have failed saccades
                            start_x,start_y,end_x,end_y = np.nan,np.nan,np.nan,np.nan
                        
                        sacLat = line[2]-fix_onset # sacLat with respect to previous EM
                        corrSacLat = line[2]-time_beginTrial # accumulated sacLat if first saccades were very small
                        fix_onset=line[3] # when did current fixation start
                        sac_angle = eu.angle((start_x,start_y),(end_x,end_y)) # radian angle of saccade
                        
                        # collect all saccade features
                        cur_sac=dict(subject_nr=int(subject_nr),trial_no=trial_no,\
                                    block_no=block_no,sac_no = sac_no,end_prev_fix= line[2],\
                                    begin_cur_fix=fix_onset,end_prev_x=start_x,end_prev_y=start_y,\
                                    s_cur_x=end_x,s_cur_y=end_y,sac_amplitude=line[9],\
                                    sac_peakVel = line[10],blinkSac=blinkSac,\
                                    sac_angle = sac_angle,beginTrial = time_beginTrial,\
                                    inTrial = inTrial,run_no = run_no,\
                                    sacLatency = sacLat, corrSacLat = corrSacLat,\
                                    resp_saccade = resp_saccade,\
                                    OSbeginTrial =OS_time_beginTrial )
                        trials.append(cur_sac)
                    sacPending = 0 # terminate a pending saccade
                    blinkSac = 0 # if it was a  blink, reset the variable
                    inSac = 0
        curBlockNo = block_no  
        prev_subject = subject_nr         
        f.close()
        # use the trial list and make a dataframe from it
        eye_df = pd.DataFrame(trials)
        # write file to csv
        eye_df.to_csv(writepath,index=False,na_rep="nan")     
        print("finished parsing subject {}".format(ascf)) 

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