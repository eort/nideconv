# CREATE FMRI LOG FILES	
import os
import pandas as pd
from IPython import embed as shell
import json
import sys
import IO as io
import glob

def makeLog(data,cleanIdx,errorIdx,evOnset,evDur,event = None):
    outFile = []
    start = data.startCurRun.iloc[0]
    clean_data = data.loc[cleanIdx]
    err_data = data.loc[errorIdx]
    if event == None:
    	print 'You need to specify which events you want to write!'  
    elif event == 'error':
        for index,row in err_data.iterrows():
             outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'firstFix':
        for block in data.FirstFixOnsetTime.unique():
			outFile.append([(block-start)*0.001,0.5,1])  
    elif event == 'secondFix':
        for block in data.SecondFixOnsetTime.unique():
			outFile.append([(block-start)*0.001,0.5,1])  
    elif event == 'cue':
        for block in data.CueOnsetTime.unique():
			outFile.append([(block-start)*0.001,2.5,1])  
    elif event == 'proSwitch':
		for index,row in clean_data.iterrows():
			if row.df == 'free' and row.switch == True:
				outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'reSwitch':
		for index,row in clean_data.iterrows():
			if row.df == 'forced' and row.switch == True:
				outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'proRep':
		for index,row in clean_data.iterrows():
			if row.df == 'free' and row.switch == False:
				outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'reRep':
		for index,row in clean_data.iterrows():
			if row.df == 'forced' and row.switch == False:
				outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'proSwitchTD':
        for index,row in clean_data.iterrows():
            if row.df == 'free' and row.switch == True and row.trial_type == 0:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'reSwitchTD':
        for index,row in clean_data.iterrows():
            if row.df == 'forced' and row.switch == True and row.trial_type == 1:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'proRepTD':
        for index,row in clean_data.iterrows():
            if row.df == 'free' and row.switch == False and row.trial_type == 0:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'reRepTD':
        for index,row in clean_data.iterrows():
            if row.df == 'forced' and row.switch == False and row.trial_type == 1:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])    
    elif event == 'proSwitchDD':
        for index,row in clean_data.iterrows():
            if row.df == 'free' and row.switch == True and row.trial_type == 1:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'reSwitchDD':
        for index,row in clean_data.iterrows():
            if row.df == 'forced' and row.switch == True and row.trial_type == 0:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'proRepDD':
        for index,row in clean_data.iterrows():
            if row.df == 'free' and row.switch == False and row.trial_type == 1:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    elif event == 'reRepDD':
        for index,row in clean_data.iterrows():
            if row.df == 'forced' and row.switch == False and row.trial_type == 0:
                outFile.append([(row[evOnset]-start)*0.001,row[evDur]*0.001,1])
    if len(outFile) == 0:
        shell()
        outFile.append([0,0,0])
    return outFile
 
def run(cfg):
    analID = cfg["analID"]
    baseDir = cfg['baseDir']
    eyefiles = glob.glob(baseDir+'derivatives/sub-*'+'/'+cfg["compDir"]+'/'+'*_comp.csv')
    eyefiles.sort();
    for fIdx in range(len(eyefiles)):
        if fIdx < 20:
            continue
        f = os.path.basename(eyefiles[fIdx])
        print "Start file: %s"%f
        eventDir = os.path.join(baseDir,'sub-%.2i'%int(f[4:6]),cfg['eventDir'])
        #io.makeDirs(eventDir)
        raw_data = pd.read_csv(eyefiles[fIdx],header=0,index_col = None)
        raw = raw_data.copy()
        badSubjIdx = raw.loc[~raw["subject_nr"].isin(cfg["excl_sub"])].index
        firstSacIdx = raw.loc[raw["sac_no"]==raw["resp_saccade"]].index
        tarDirectedSacIdx = raw.loc[raw["sac_to_S"]==raw[cfg["fixatedTarget"]]].index
        practiceIdx = raw.loc[raw["practice"]=='no'].index
        firstTrialIdx = raw.loc[raw["trial_no"]!=1].index
        missIdx = raw.loc[raw["miss"]==0].index
        outlierIdx = raw.loc[raw["outlier"]==False].index
        RTIdx = raw.loc[raw["RT"]>100].index
        conflictIdx = raw.loc[raw["conflict"]==False].index
        accIdx = raw.loc[raw["correct"]==1].index
        errorIdx = raw.loc[(raw["correct"]==0) & (raw["miss"]==0) & (raw["sac_no"]==raw["resp_saccade"])].index
        nanIdx = raw.loc[~pd.isnull(raw["switch"])].index
        
        # combine index
        cleanIdx = (firstSacIdx & tarDirectedSacIdx & practiceIdx &\
          firstTrialIdx & missIdx & outlierIdx & RTIdx &\
          conflictIdx & accIdx & nanIdx & badSubjIdx)

        events = cfg['events']
        #['reSwitch','reRep','proSwitch','proRep','error','cue','firstFix','secondFix']
        #events = ['reSwitchTD','reRepTD','proSwitchTD','proRepTD','error',\
        #            'reSwitchDD','reRepDD','proSwitchDD','proRepDD','cue','firstFix','secondFix']
        for event in events:
            outFile = makeLog(raw,cleanIdx,errorIdx,cfg['evOnset'],cfg['evDur'],event)
            name = 'sub-%.2i-%.2i_'%(raw.subject_nr.iloc[0],raw.run_no.iloc[0]) + event + analID + '.tsv'
            eventfile = os.path.join(eventDir,analID,name)
            """
            if not os.path.exists(os.path.dirname(eventfile)):
                    os.makedirs(os.path.dirname(eventfile))
            
            with open(eventfile, 'w') as txtfile:
                for val in outFile:
                    if any([pd.isnull(value) for value in val]):
                        continue
                    txtfile.write('%f\t%f\t%f \n'%(val[0], val[1], val[2] ))
            txtfile.close()
            """
        print "Finished file: %s"%f
if __name__== '__main__':
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
