# CREATE FMRI LOG FILES	


"""
TODO
CHECK PARTICULARITIES OF SUB 1
CHECK DURATION OF CUE
CHECK SANITY
COMMENT
ADD COLUMNS (WHICH?)
"""

import os
import os.path as op
import pandas as pd
from IPython import embed as shell
import json
import sys
import IO as io
import glob



def run(cfg):

    # set parameters
    baseDir = cfg['baseDir']
    subs = cfg['subs']
    include_col = cfg['include_col']

    # sub for sub, even though you could do it all at once
    for SUB in subs:
        behavDir = op.join(baseDir,cfg["behavDir"])%SUB
        outDir = op.join(baseDir,cfg["funcDir"])%SUB

        print "Start sub: %02d"%SUB
        eyefiles = glob.glob(behavDir+'/*_comp.csv')
        eyefiles.sort()

        for eyef in eyefiles:
            eye = op.basename(eyef)
            RUN = int(eye.split('-')[2][:2])
            # filepath to be written to
            outfilename = op.join(outDir,cfg['outfilename']%(SUB,RUN))
            
            raw_data = pd.read_csv(eyef,header=0,index_col = None,usecols = include_col)

            # filter data
            raw = raw_data.copy()
            shell()
            badSubjIdx = raw.loc[~raw["subject_nr"].isin(cfg["excl_sub"])].index
            firstSacIdx = raw.loc[raw["sac_no"]==raw["resp_saccade"]].index
            tarDirectedSacIdx = raw.loc[raw["sac_to_S"]==raw[cfg["fixatedTarget"]]].index
            practiceIdx = raw.loc[raw["practice"]=='no'].index
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
              conflictIdx & nanIdx & badSubjIdx)

            
            start = raw.startCurRun.iloc[0]
            clean_data = raw.loc[cleanIdx]
            cueOnset = clean_data.CueOnsetTime.unique()-start
            FirstFixOnset = clean_data.FirstFixOnsetTime.unique()-start
            SecondFixOnset = clean_data.SecondFixOnsetTime.unique()-start

            preTrialDF = pd.DataFrame({'onset': cueOnset*0.001, 'duration':2.5, \
                    'trialType': 'cue','trialTypeComplete': 'cue'})

            preTrialDF = preTrialDF.append(pd.DataFrame({'onset': \
                    FirstFixOnset*0.001, 'duration':0.5, \
                    'trialType': 'firstFix','trialTypeComplete': 'firstFix'}))
            preTrialDF= preTrialDF.append(pd.DataFrame({'onset': \
                    SecondFixOnset*0.001, 'duration':0.5, \
                    'trialType': 'secondFix','trialTypeComplete': 'secondFix'}))
            
            onset = clean_data["stim_on"]-start
            durations = clean_data["RT"]*0.001
            outDF = pd.DataFrame({'onset':onset*0.001,'duration':durations})

            for index,row in clean_data.iterrows():

                if row.correct == 0:
                    outDF.loc[index,"trialType"] = 'error'
                    outDF.loc[index,"trialTypeComplete"] = 'error'
                    continue

                if row.df == 'forced' and row.switch == False:
                    outDF.loc[index,"trialType"] = 'reRep'
                elif row.df == 'forced' and row.switch == True:
                    outDF.loc[index,"trialType"] = 'reSwitch'
                elif row.df == 'free' and row.switch == True:
                    outDF.loc[index,"trialType"] = 'proSwitch'
                elif row.df == 'free' and row.switch == False:
                    outDF.loc[index,"trialType"] = 'proRep'

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
            
            outDF = outDF.append(preTrialDF)
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
        print "The provided file does not exist. Either put a default .json file "\
        "in the directory of this script, or provide a valid file in the command line."
        sys.exit()

    run(cfg)

