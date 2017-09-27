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
    baseDir = cfg['baseDir']
    rawfiles = glob.glob(baseDir+'sub-*'+'/'+cfg["compDir"]+'/'+'*_comp.csv')
    raw_data = pd.concat([pd.read_csv(f,header=0,index_col = None) for f in rawfiles],ignore_index=True)
    ##################################################
    #Select clean trials
    ##################################################
    print "Trial selection"
    # find index
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
    nanIdx = raw.loc[~pd.isnull(raw["switch"])].index
    #exclude
    clean_data = raw.loc[firstSacIdx & tarDirectedSacIdx & practiceIdx &\
          firstTrialIdx & missIdx & outlierIdx & RTIdx &\
          conflictIdx & accIdx & nanIdx & badSubjIdx]
    
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
    switchPlot.set(ylim=(340, 500))
    switchPlot.set(ylabel="Saccade Latency (ms)")
    switchPlot.set(xlabel="Target Availability")
    switchPlot.set_xticklabels(['One Target Available','Both Targets Available'])
    sns.despine()
    fig = switchPlot.get_figure()
    fig.savefig(os.path.join(cfg['baseDir'],cfg['plotDir'],"SC_behaviour.pdf"))
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
