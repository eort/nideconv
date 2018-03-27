# -*- coding: utf-8 -*-
"""
Preprocessing of BA_TripleTrace. 
Read out ascii file that was produced by converting a EDF file
and transform the format to match CSV style. 
created by Eduard Ort, 2015
"""

import os
import sys
import pandas as pd
from IPython import embed as shell
import IO as io
import math
import misc
import numpy as np

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Helper function defintion (too few for the effort of separate module)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def phaseDiff(angle1, angle2):
    """
    checks the shortest distance between two distances
    """
    return np.absolute(angle2-angle1)      
          
def checkSacAngle(sac_angle,stim_angles, threshold = 0.25):
    """
    First input is the angle of the saccade, 
    Second input is the angles of the stimuli with start point
    of saccade as reference
    Function returns, to which item the saccade was directed
    """
    distances = []
    for ang in stim_angles:
        #compute distance
        d = phaseDiff(sac_angle,ang)
        d_min = np.min((d,2*np.pi-d) )
        distances.append(d_min)
        
    if np.min(distances) > threshold: 
        return 's0'
    else:
        return 's' + str(np.argmin(distances) + 1)
    
def angle(spoints,epoints):
    
    x = epoints[0]-spoints[0]
    y = epoints[1]-spoints[1]
    return (math.atan2(y,x) + 2*np.pi)%(2*np.pi)
    
def getOverlap(points, fixation,threshold = 90):
    """
    points is a list of point coordinates that should be included in the computation
    of the distances. Fixation is the point that was fixated in the end. 
    Threshold indicates the minimal distance between two points to not be a 
    conflict. 
    Returns True if there is an overlap of the fixated stimulus with any of the
    others, and False otherwise as first argument and the 
    """
    # default is target1
    
    if fixation == 's2':
        x1,y1 = points.pop(1)
    elif fixation == 's3':
        x1,y1 = points.pop(2)
    else:
        x1,y1 = points.pop(0)
        
    for x,y in points:
        d = misc.dist((x1,y1),(x,y))
        #shell()
        if d < threshold:
            return 1,d

    if fixation == None:    
        d = misc.dist(points[0],points[1])
       
        if d < threshold:
            return 1,d
    return 0,-99
    
def fixS01(stim, t_dur):
    """
    Fix the issue with subject one (fixatedStim from 0 to 4, instead of 1 to 5)
    """
    if t_dur >2950:
        return 's'+ str(int(stim[-1])+1)    
    return stim
    
    
    
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
MAIN ScRIPT
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def run(subj):
    # set paths
    #shell()
    folder = os.path.abspath(os.path.join(os.getcwd(),os.pardir))
    filepath = os.path.join(os.getcwd(),subj)# path to ascii fil
    # include also csv file, for color info
    out_path = os.path.join(folder,'eye_csv')
    csv_path = os.path.join(folder,'os_csv/',subj[:-3] + 'csv')
    # create the output folder if necessary
    if not os.path.exists(out_path):
        os.makedirs(out_path)  
    writepath = os.path.join(out_path,subj[:-4]+'_RFILES.csv')

    print "start processing", subj

    # read out asc file
    eye_data= []
    f = open(filepath, 'r')
    for line in f:
        values= io.str2list(line)
        eye_data.append(values)

    include_col = [\
        's1_x','s1_y','s1_color','s1_cat','s2_x','s2_y','s2_cat','s2_color',\
        's3_x','s3_y','s3_cat','s3_color','s4_x','s4_y','s4_cat','s4_color',\
        's5_x','s5_y','s5_cat','s5_color','tc1','tc2','dc1','dc2','dc3',\
        'subject_nr','block_no','trial_no','filler_block_no','run_no',\
        'fixatedStim','fixated_target','accFix','forcedExit','terminated',\
        'df','df_idx','practice','trial_type','type_switch','mode','prev_df','correct','miss',\
        'trial_duration','stim_on','exit_time','findPos_time','no_switch',\
        'sleep','ITI','filler_block','prepTime','r','run_length','run_limit',\
        'CueOnsetTime','FirstFixOnsetTime','FmriTriggerTime','SecondFixOnsetTime',\
        'curfix_x','curfix_y','free_seqs','t_off','time_in_block','time_in_run',
        'endCurRun','startCurRun']
    # read in the csv file, but include only one relevant column
    csv_df = pd.read_csv(csv_path,usecols = include_col)

    # initialize variables necessary to keep track of trials/fixations/etc
    # while looping over eye data
    inTrial = False
    start_trial = ['Begin','search','canvas']# trigger of trial start
    stop_trial = ['Trial','over'] # message OpenSesame sent to eyetracker to indicate stop recording
    start_block = ['Begin','cue','canvas']
    trial_count = -1 
    line_count  = 0
    blink = False
    analyze_saccade = False
    failedFixation = False
    inSac = False
    trials = []
    
    try:
        for idx,line in enumerate(eye_data):
            # skip not informative lines in ascii file
        
            if len(line)== 0:
                continue
    
            elif line[0]=='MSG':
                # first learn about the start and end of a trial
            
                if line[-4:-1] == start_block:
                    previousTarget = None
                    switch_time = -9999999
                    no_rep = 1 
                    blink=False

                elif line[-4:-1] == start_trial:
                    OS_trialOnsetTime = line[-1]
                    sac_no = 1
                    resp_saccade = 1
                    switch_interval = None
                    trial_count += 1
                    inTrial = True
                    firstSacToSelection = False
                    trial_start_time = line[1] # used to calculate eff.fix.dur
                    fix_onset = line[1]
                    if inSac:
                        failedFixation = True
                    else:
                        failedFixation = False
                    inTrialPending = False 
                    
                # end of trial
                elif line[-3:-1] == stop_trial:
                    #shell()
                    if not inSac:
                        inTrial = False
                        OS_trialOffsetTime = line[-1]
                    else:
                        inTrialPending = True  

            # mark start of blink
            elif line[0]=='SBLINK':
                blink = True
            # mark beginning of saccade    
            elif line[0]=='SSACC':
                inSac = True   
               
            elif line[0]=='ESACC':
                inTrialPending = False
                inSac = False
                if inTrial and not blink and not failedFixation:
                    analyze_saccade = True
                if blink:
                    blink = False
                if failedFixation:
                    failedFixation = False
                    
            if analyze_saccade: 
                analyze_saccade = False
                t_dur = csv_df['fixatedStim'][trial_count] # trial duration
                fixatedStim = csv_df['fixatedStim'][trial_count]
                if subj in ['s-01-01.asc','s-01-02.asc','s-01-03.asc','s-01-04.asc']:
                    fixatedStim = fixS01(fixatedStim, t_dur)
                
                if csv_df['fixatedStim'][trial_count] == 's0':
                    fixatedTarget  = None
                elif csv_df[fixatedStim+'_color'][trial_count] ==csv_df['tc1'][trial_count]:
                    fixatedTarget = 't1'
                elif csv_df[fixatedStim+'_color'][trial_count] ==csv_df['tc2'][trial_count]:
                    fixatedTarget = 't2'
                else:
                    fixatedTarget  = None

                # compute the distance of stimuli to each other
                conflict,distance = getOverlap([[csv_df['s1_x'][trial_count],csv_df['s1_y'][trial_count]],\
                   [csv_df['s2_x'][trial_count],csv_df['s2_y'][trial_count]],\
                   [csv_df['s3_x'][trial_count],csv_df['s3_y'][trial_count]],\
                   [csv_df['s4_x'][trial_count],csv_df['s4_y'][trial_count]],\
                   [csv_df['s5_x'][trial_count],csv_df['s5_y'][trial_count]]]\
                   ,fixatedStim)
                      
                # have saccade angle and saccade amplitude
                start_x,start_y,end_x,end_y = line[5]-640,line[6]-420,line[7]-640,line[8]-420
                
                sac_amplitude = line[9]
                sac_angle = angle((start_x,start_y),(end_x,end_y))
                
                # angle to targets, dist to targets
                angle_to_s1 = angle((start_x,start_y),(csv_df['s1_x'][trial_count],csv_df['s1_y'][trial_count]))               
                dist_to_s1 = misc.dist((csv_df['s1_x'][trial_count],csv_df['s1_y'][trial_count]),(end_x,end_y))   
                angle_to_s2 = angle((start_x,start_y),(csv_df['s2_x'][trial_count],csv_df['s2_y'][trial_count]))
                dist_to_s2 = misc.dist((csv_df['s2_x'][trial_count],csv_df['s2_y'][trial_count]),(end_x,end_y))
                angle_to_s3 = angle((start_x,start_y),(csv_df['s3_x'][trial_count],csv_df['s3_y'][trial_count]))  
                dist_to_s3 = misc.dist((csv_df['s3_x'][trial_count],csv_df['s3_y'][trial_count]),(end_x,end_y))
                angle_to_s4 = angle((start_x,start_y),(csv_df['s4_x'][trial_count],csv_df['s4_y'][trial_count]))
                angle_to_s5 = angle((start_x,start_y),(csv_df['s5_x'][trial_count],csv_df['s5_y'][trial_count]))  
                stim_angles = [angle_to_s1,angle_to_s2,angle_to_s3,angle_to_s4,angle_to_s5]
                
                # accumulate microsaccades, everythng below 1 degree
                if (resp_saccade == sac_no) and sac_amplitude <= 1:
                    resp_saccade +=1    
                
                if sac_amplitude > 1:
                    sac_to_S = checkSacAngle(sac_angle,stim_angles, np.pi/6) 
                elif sac_no > resp_saccade:
                    sac_to_S = checkSacAngle(sac_angle,stim_angles, np.pi/6)   
                else:
                    sac_to_S = 's0'
                
                if sac_to_S == fixatedStim and firstSacToSelection != True:
                    sacToSelection = 1
                    firstSacToSelection = True
                else: 
                    sacToSelection = 0
       
                
                if fixatedTarget == None or previousTarget == None:
                    color_switch = None
                elif fixatedTarget == previousTarget:
                    color_switch = 0
                    no_rep += 1
                elif fixatedTarget != previousTarget:
                    color_switch = 1
                    no_rep = 0 
                    switch_interval = csv_df['stim_on'][trial_count]- switch_time
                    switch_time = csv_df['stim_on'][trial_count]
                
                if sac_no >1:
                    color_switch = trials[-1]['color_switch']
                    no_rep = trials[-1]['no_rep']
    
                trials.append({'subj':subj,'line_count':line_count,\
                'sac_no':sac_no,'begin_fix':line[3],'end_prev_x':start_x,'end_prev_y':start_y,\
                'end_prev_fix': line[2],'s_cur_x':end_x,'s_cur_y':end_y,'sac_amplitude':sac_amplitude}) 
    
                trials[-1]['target_category']= fixatedTarget
                trials[-1]['color_switch']= color_switch
                trials[-1]['no_rep']= no_rep
                trials[-1]['switch_interval']= switch_interval
                trials[-1]['conflict']= conflict
                trials[-1]['distance']= distance
                trials[-1]['sac_angle']= sac_angle
                trials[-1]["sac_lat_trial"]=line[2]-trial_start_time # sac latency since trial onset
                trials[-1]["angle_to_s1"]=angle_to_s1 # which saccade is the first real response
                trials[-1]["angle_to_s2"]=angle_to_s2
                trials[-1]["angle_to_s3"]=angle_to_s3                
                trials[-1]["dist_to_s1"]=dist_to_s1
                trials[-1]["dist_to_s2"]=dist_to_s2
                trials[-1]["dist_to_s3"]=dist_to_s3
                trials[-1]["resp_saccade"]=resp_saccade
                trials[-1]["sac_to_S"]=sac_to_S
                trials[-1]["sacToSelection"]=sacToSelection
                trials[-1]["SacContainsBlink"]=int(blink)
                
                
                # fix block number for blocks that were aborted
                if csv_df['terminated'][trial_count]:
                    if sac_no<2:
                        csv_df['trial_no'].loc[trial_count] = csv_df['trial_no'].loc[trial_count-1]+1
                    else:
                        csv_df['trial_no'].loc[trial_count] = csv_df['trial_no'].loc[trial_count-1]
                    
                #add trial parameters to trial container, too
                
                columns = csv_df[:1].columns.values
                for key in columns:
                    if key == 'free_seqs':
                        continue
                    try:
                        trials[-1][key]=csv_df[key][trial_count].replace(',',';')     
                    except:
                        trials[-1][key]=csv_df[key][trial_count] 
                # correct duration of first fixation in a trial
                if sac_no == 1:
                    trials[-1]["effective_fix_dur"]=line[2]-trial_start_time
                else:
                    trials[-1]["effective_fix_dur"]=line[2]-fix_onset 
                 
                previousTarget = fixatedTarget
                fix_onset = line[3]
                line_count += 1
                sac_no += 1
                if inSac and inTrialPending:
                    inTrial = False
                    inTrialPending = False
                inSac = False                    

    except:
        print 'ohoh'
        
    #shell()
    # Write to file
    f = open(writepath, 'w')
    io.write2CSV(f, trials[0].keys())
    for trial in trials:
        io.write2CSV(f, trial.values())
        #print trial.values()
        #shell()
    f.close()
    print 'subjected completed successfully'
    #shell()
if __name__== '__main__':
    os.chdir('/home/ede/projects/BA_fMRI/')
    folders = os.listdir(os.getcwd())  
    folders.sort()
    for f in folders:
        if f[:4]== 'sub-':
            os.chdir(os.path.join(f,'asc'))
            files = os.listdir(os.getcwd()) 
            files.sort()
            for asc in files:
                if ".asc" in asc:    
                    #asc = 's-03-05.asc'
                    try:        
                        o = run(asc)
                    except Exception as e:
                        print e
                        continue
                    
            os.chdir('../..')
                    #break