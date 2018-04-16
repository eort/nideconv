# CREATE FMRI LOG FILES	


"""
Eventfiles for the modelling. Events are extracted from preprocessed 
eyetracking data
event files contain events locked to different timepoints in a run: 
onset of current run, offset of previous trial, onset of previous trial 
to select the correct events one would have to select based on the variableonset type

TODO

CHECK SANITY
FIND OUT WHY SUDDENLY MUCH FEWER EMPTY RUNS (WITH BOTH OLD AND NEW SCRIPT)

"""

import os
import os.path as op
import pandas as pd
from IPython import embed as shell
import json
import sys
import glob
from collections import OrderedDict


def run(cfg):

    # load parameters
    baseDir = cfg['baseDir']
    subs = cfg['subs']
    skip = cfg['skip']
    include_col = cfg['include_col']
    onsetTypes = cfg['onsetTypes']
    # sub for sub, even though you could do it all at once
    for SUB in subs:
        # skip unwanted subjects
        if SUB in skip:
            print "Skip sub: %02d"%SUB
            continue
        
        print "Do sub: %02d"%SUB
        # fix sub-specific directories
        behavDir = op.join(baseDir,cfg["behavDir"])%SUB
        outDir = op.join(baseDir,cfg["funcDir"])%SUB
        # find behaviorally processed eyefiles and sort
        eyefiles = glob.glob(behavDir+'/*_comp.csv')
        eyefiles.sort()

        # loop across eyefiles
        for eyef in eyefiles:
            eye = op.basename(eyef)
            # get run number
            RUN = int(eye.split('-')[2][:2])
            # filepath to be written to
            outfilename = op.join(outDir,cfg['outfilename']%(SUB,RUN))
            # load relevant columns from current eyefile
            raw_data = pd.read_csv(eyef,header=0,index_col = None,usecols = include_col)

            # collect filters
            raw = raw_data.copy()
            firstSacIdx = raw.loc[raw["sac_no"]==raw["resp_saccade"]].index
            tarDirectedSacIdx = raw.loc[raw["sac_to_S"]==raw["fixatedStim"]].index
            practiceIdx = raw.loc[raw["practice"]=='no'].index # there is no practice
            firstTrialIdx = raw.loc[raw["trial_no"]!=1].index
            missIdx = raw.loc[raw["miss"]==0].index
            outlierIdx = raw.loc[raw["outlier"]==False].index
            RTIdx = raw.loc[raw["RT"]>100].index
            conflictIdx = raw.loc[raw["conflict"]==False].index
            #accIdx = raw.loc[raw["correct"]==1].index
            #errorIdx = raw.loc[(raw["correct"]==0) & (raw["miss"]==0) & (raw["sac_no"]==raw["resp_saccade"])].index
            nanIdx = raw.loc[~pd.isnull(raw["switch"])].index
            # combine index
            cleanIdx = (firstSacIdx & tarDirectedSacIdx & practiceIdx &\
              firstTrialIdx & missIdx & outlierIdx & RTIdx &\
              conflictIdx & nanIdx )#& badSubjIdx)

            # When did run start
            start = raw.startCurRun.iloc[0]
            # apply filters
            clean_data = raw.loc[cleanIdx]
            # get onset times for pretrial events
            cueOnset = 0.001*(clean_data.CueOnsetTime.unique()-start)
            FirstFixOnset = 0.001*(clean_data.FirstFixOnsetTime.unique()-start)
            SecondFixOnset = 0.001*(clean_data.SecondFixOnsetTime.unique()-start)
            # collect pretrial data
            preTrialDFcue = pd.DataFrame(OrderedDict({'onset': cueOnset, 'duration':2.5, \
                    "onsetType":'onset','trialType': 'cue','trialTypeComplete': 'cue'}))
            preTrialDFfirst = pd.DataFrame(OrderedDict({'onset': FirstFixOnset, 'duration':0.5, \
                    "onsetType":'onset','trialType': 'firstFix','trialTypeComplete': 'firstFix'}))
            preTrialDFsecond = pd.DataFrame(OrderedDict({'onset': SecondFixOnset, 'duration':0.5, \
                    "onsetType":'onset','trialType': 'secondFix','trialTypeComplete': 'secondFix'}))

            # for each onset type run through the loop
            outDFs = []
            for onsetKey,durationKey in onsetTypes:
                # now do the same for all the other events in seconds
                onset = 0.001*(clean_data[onsetKey]-start)
                # retrieve the event duration in second
                durations = clean_data[durationKey]*0.001
                # create default dataframe
                outDF = pd.DataFrame(OrderedDict({'onset':onset,'duration':durations,'onsetType':onsetKey}))
                # manual hack to make "onset" being the standard onset type
                if onsetKey == 'stim_on':
                    outDF['onsetType'] = 'onset'
                # add event type information
                for index,row in clean_data.iterrows():
                    # if there is a mistake, add them as such and skip the rest
                    if row.correct == 0:
                        outDF.loc[index,"trialType"] = 'error'
                        outDF.loc[index,"trialTypeComplete"] = 'error'
                        continue
                    # first check the basic event types
                    if row.df == 'forced' and row.switch == False:
                        outDF.loc[index,"trialType"] = 'reRep'
                    elif row.df == 'forced' and row.switch == True:
                        outDF.loc[index,"trialType"] = 'reSwitch'
                    elif row.df == 'free' and row.switch == True:
                        outDF.loc[index,"trialType"] = 'proSwitch'
                    elif row.df == 'free' and row.switch == False:
                        outDF.loc[index,"trialType"] = 'proRep'
                    # second check complete trial type events
                    if row.df == 'free' and row.switch == True and row.trial_type == 0:
                        outDF.loc[index,"trialTypeComplete"] = 'proSwitchTD'
                    elif row.df == 'forced' and row.switch == True and row.trial_type == 1:
                        outDF.loc[index,"trialTypeComplete"] = 'reSwitchTD'            
                    elif row.df == 'free' and row.switch == False and row.trial_type == 0:
                        outDF.loc[index,"trialTypeComplete"] = 'proRepTD'
                    elif row.df == 'forced' and row.switch == False and row.trial_type == 1:
                        outDF.loc[index,"trialTypeComplete"] = 'reRepTD'            
                    elif row.df == 'free' and row.switch == True and row.trial_type == 1:
                        outDF.loc[index,"trialTypeComplete"] = 'proSwitchDD'
                    elif row.df == 'forced' and row.switch == True and row.trial_type == 0:
                        outDF.loc[index,"trialTypeComplete"] = 'reSwitchDD'            
                    elif row.df == 'free' and row.switch == False and row.trial_type == 1:
                        outDF.loc[index,"trialTypeComplete"] = 'proRepDD'
                    elif row.df == 'forced' and row.switch == False and row.trial_type == 0:
                        outDF.loc[index,"trialTypeComplete"] = 'reRepDD'        
                outDFs.append(outDF)

            # concatenate all the event data frames, sort by onset and write to file
            outDF = pd.concat(outDFs+[preTrialDFcue,preTrialDFfirst,preTrialDFsecond])
            outDF = outDF.sort_values(by=['onset'])
            outDF.to_csv(outfilename, index = False, sep = '\t')

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
        print "The provided file does not exist."\
        "Please provide a valid file in the command line."
        sys.exit()

    run(cfg)

