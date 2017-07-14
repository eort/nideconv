# -*- coding: utf-8 -*-
"""
Merging all subjects files into one data_frame. 
Running preprocessing steps 
Stats
"""
import os
import sys
import glob
import pandas as pd
from IPython import embed as shell
import numpy as np
import json
import seaborn as sns

def run(cfg):
    # set paths
    baseDir = cfg['baseDir']
    # read files
    if len(sys.argv) < 2:
       rawfiles = glob.glob(baseDir+'sub-*'+'/'+cfg["compDir"]+'/'+'*_comp.csv')
    # selected trial columns
    raw_data = pd.concat([pd.read_csv(f,header=0,index_col = None) for f in rawfiles],ignore_index=True)
    #shell()
    ##################################################
    #Select clean trials
    ##################################################
    print "Trial selection"
    #shell()
    raw = raw_data.copy()
    print raw.shape
    raw = raw.loc[~raw["subject_nr"].isin(cfg["excl_sub"])]# exclude bad subjects
    print raw.shape
    raw = raw.loc[raw["sac_no"]==raw["resp_saccade"]] # select only first fixation in trial
    print raw.shape
    raw = raw.loc[raw["sac_to_S"]==raw[cfg["fixatedTarget"]]]
    print raw.shape
    raw = raw.loc[raw["practice"]=='no'] # select only non practice trials
    print raw.shape
    proc = raw.copy() # data frame to compute accuracy
    proc = proc.loc[proc["miss"]==0] # select only non missed trials
    print proc.shape
    proc = proc.loc[proc["trial_no"]!=1] # exclude first trials
    print proc.shape
    proc =proc.dropna(subset =["switch"]) # only switches and repetitions
    print proc.shape
    proc = proc.loc[proc["outlier"]==False] # exclude speed outliers
    print proc.shape
    proc = proc.loc[proc["RT"]>100] # exclude speed outliers
    print proc.shape
    proc = proc.loc[proc["conflict"]==False] # exclude speed outliers
    print proc.shape
    #proc = proc.loc[proc["conflict"]==0] # exclude speed outliers
    acc_data = proc.copy()
    clean_data = acc_data.loc[acc_data["correct"]==1] # only take correct trials
    print clean_data.shape
    ##################################################
    #Analysis1
    ##################################################    
    print "Analysis 1"
    anal1 = clean_data.copy()
    Firstlvl1=anal1.groupby(['subject_nr','run_no','df','switch'])['RT'].agg([np.mean,np.std,np.size]).rename(columns = {'mean':'mRT','std':'sdRT','size':'count'}).reset_index()
    Secondlvl1=Firstlvl1.groupby(['subject_nr','df','switch'])['mRT','sdRT','count'].mean().reset_index()
    Thirdlvl1=Secondlvl1.groupby(['df','switch'])['mRT','sdRT','count'].mean().reset_index()
    print Firstlvl1
    print Secondlvl1
    print Thirdlvl1
    print "Analysis 2"
    anal2 = clean_data.copy()
    Firstlvl2=anal2.groupby(['subject_nr','trial_type','df','switch'])['sacLatency'].agg([np.mean,np.std,np.size]).rename(columns = {'mean':'mRT','std':'sdRT','size':'count'}).reset_index()
    Secondlvl2=Firstlvl2.groupby(['trial_type','df','switch'])['mRT','sdRT','count'].mean().reset_index()
    print Secondlvl2
    print "plotting"
    sns.set_style("white")
    
    switchPlot = sns.barplot(x="df", y="mRT", hue="switch",
                                palette= ('dimgrey','darkgrey','dimgrey','darkgrey'),data=Secondlvl1,ci=68)
    switchPlot.set(ylim=(200, 300))
    switchPlot.set(ylabel="Saccade Latency (ms)")
    switchPlot.set(xlabel="Mode of Cognitive Control")
    
    sns.despine()
    fig = switchPlot.get_figure()
    #fig.savefig(os.path.join(plotDir,"SwitchCosts.pdf"))
    #sns.plt.show()
if __name__ == '__main__':  
    try:
        jsonfile = sys.argv[1]
    except IndexError as e:
        jsonfile = 'cfg.json'   
    try:
        with open(jsonfile) as data_file:    
            cfg = json.load(data_file)
        data_file.close()
    except IOError as e:
        print "The provided file does not exist. Either put a default .json file "\
        "in the directory of this script, or provide a valid file in the command line."
    run(cfg)
