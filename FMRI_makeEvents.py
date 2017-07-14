# CREATE FMRI LOG FILES	
import os
import pandas as pd
from IPython import embed as shell
import json
import sys
import IO as io
import glob

def makeLog(data,event = None):
     outFile = []
     start = data.startCurRun.iloc[0]
     if event == None:
		print 'You need to specify which events you want to write!'  
     elif event == 'error':
		for index,row in data.iterrows():
			if row.correct == 0 and  row.miss == 0:
				if min(row.dist_to_s1,row.dist_to_s2,row.dist_to_s3,row.dist_to_s4,row.dist_to_s5)<55:
					outFile.append([(row.stim_on-start)*0.001,row.RT*0.001,1])  
     elif event == 'firstFix':
         for block in data.FirstFixOnsetTime.unique():
			outFile.append([(block-start)*0.001,500,1])  
     elif event == 'secondFix':
         for block in data.SecondFixOnsetTime.unique():
			outFile.append([(block-start)*0.001,500,1])  
     elif event == 'cue':
         for block in data.CueOnsetTime.unique():
			outFile.append([(block-start)*0.001,2500,1])  
     elif event == 'proSwitch':
		for index,row in data.iterrows():
			if row.df == 'free' and row.switch == True and row.correct == 1:
				outFile.append([(row.stim_on-start)*0.001,row.RT*0.001,1])
     elif event == 'reSwitch':
		for index,row in data.iterrows():
			if row.df == 'forced' and row.switch == True and row.correct == 1:
				outFile.append([(row.stim_on-start)*0.001,row.RT*0.001,1])
     elif event == 'proRep':
		for index,row in data.iterrows():
			if row.df == 'free' and row.switch == False and row.correct == 1:
				outFile.append([(row.stim_on-start)*0.001,row.RT*0.001,1])
     elif event == 'reRep':
		for index,row in data.iterrows():
			if row.df == 'forced' and row.switch == False and row.correct == 1:
				outFile.append([(row.stim_on-start)*0.001,row.RT*0.001,1])
     return outFile
 
def run(cfg):
    baseDir = cfg['baseDir']
    eyefiles = glob.glob(baseDir+'sub-*'+'/'+cfg["compDir"]+'/'+'*_comp.csv')
    eyefiles.sort();

    for fIdx in range(len(eyefiles)):
        f = os.path.basename(eyefiles[fIdx])
        if int(f[4:6]) in cfg["excl_sub"]:
            continue
        print "Start file: %s"%f
        eventDir = os.path.join(baseDir,'sub-%.2i'%int(f[4:6]),cfg['eventDir'])
        io.makeDirs(eventDir)
        
        rawdata = pd.read_csv(eyefiles[fIdx],header=0,index_col = None)
        
        raw = rawdata.copy()
        raw = raw.loc[raw["sac_no"]==raw["resp_saccade"]] # select only first fixation in trial
        raw = raw.loc[raw["sac_to_S"]==raw[cfg["fixatedTarget"]]]
        raw = raw.loc[raw["practice"]=='no'] # select only non practice trials
        proc = raw.copy() # data frame to compute accuracy
        #proc = proc.loc[proc["miss"]==0] # select only non missed trials
        proc = proc.loc[proc["trial_no"]!=1] # exclude first trials
        proc =proc.dropna(subset =["switch"]) # only switches and repetitions
        proc = proc.loc[proc["outlier"]==False] # exclude speed outliers
        proc = proc.loc[proc["RT"]>100] # exclude speed outliers
        proc = proc.loc[proc["conflict"]==False] # exclude speed outliers
        acc_data = proc.copy()
        #clean_data = acc_data.loc[acc_data["correct"]==1] # only take correct trials
        clean_data =acc_data
        events = ['reSwitch','reRep','proSwitch','proRep','error','firstFix','secondFix','cue']
        
        for event in events:
            outFile = makeLog(clean_data,event)
            name = 'sub-%.2i-%.2i_'%(clean_data.subject_nr.iloc[0],clean_data.run_no.iloc[0]) + event + '.tsv'
            eventfile = os.path.join(eventDir,name)
            with open(eventfile, "w") as txtfile:
                for val in outFile:
                    txtfile.write("%f\t%f\t%f \n"%(val[0], val[1], val[2] ))
            txtfile.close()
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
