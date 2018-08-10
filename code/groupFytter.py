import os,json,glob,sys
import os.path as op
import matplotlib as mpl
mpl.use('Agg')
import pandas as pd
import plotUtils as plot

from IPython import embed as shell

assert len(sys.argv)==3

try:
    jsonfile = sys.argv[1]
    ROI = sys.argv[2]
except:
    print "The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line."
    sys.exit(-1)
else:
    with open(jsonfile) as f:    
        cfg = json.load(f)

# further settings
analID = cfg['analID']
baseDir = cfg['baseDir'] # root
outDir = op.join(baseDir,cfg['outDir'].format(analID = analID))
plotDir = op.join(outDir,'figures')
statsDir = op.join(outDir,'stats')
if not op.exists(plotDir):
    os.makedirs(plotDir)
if not op.exists(statsDir):
    os.makedirs(statsDir)
    
search_key = cfg['search_key'].format(sigID = cfg['sigID'],analID = analID)

all_files = glob.glob(baseDir + search_key)

# collect all subjects for certain ROI in one data frame
fd_group = pd.DataFrame()
for fil in all_files:
    if ROI == fil.split('_')[-2]:        
        fd_group = pd.concat([fd_group,pd.read_csv(fil)],axis = 0)

evTypes  = ['proSwitch','reSwitch','proRep','reRep']

# truncate
truncate = 1
if truncate:
    time_points = fd_group.time.unique()
    lowcutoff = -5
    highcutoff = 10
    fd_group = fd_group[(fd_group["time"]>lowcutoff) & (fd_group["time"]<highcutoff)]


# first plot raw BOLD estimates
fd_group.loc[:,'condDiff'] = 'no'
fd = fd_group[fd_group["eventTypes"].isin(evTypes)]
# create pairwise comparisons
proSwi = fd['betas'].loc[fd["eventTypes"].isin(['proSwitch'])].copy()
reSwi = fd['betas'].loc[fd["eventTypes"].isin(['reSwitch'])].copy()
prorebetas = fd.loc[fd["eventTypes"].isin(['reSwitch'])].copy()
prorebetas.loc[:,'betas'] = proSwi.values-reSwi.values
prorebetas.loc[:,'eventTypes'] = 'proSwitch-reSwitch'
prorebetas.loc[:,'condDiff'] = 'yes'

fd = pd.concat([fd,prorebetas])

outfile = op.join(plotDir,'{ROI}_{analID}_group.pdf'.format(ROI=ROI,analID=analID))
plot_cfg = {'outfile':outfile}
plot.plotTimeCourse(fd,plot_cfg)

# second plot, looking at the substraction of switch minus repetition (baseline?)
proSwi =  fd_group['betas'].loc[fd_group["eventTypes"].isin(['proSwitch'])].copy()
proRep =  fd_group['betas'].loc[fd_group["eventTypes"].isin(['proRep'])].copy()
probetas = fd_group.loc[fd_group["eventTypes"].isin(['proRep'])].copy()
probetas.loc[:,'betas'] = proSwi.values-proRep.values
probetas.loc[:,'eventTypes'] = 'Proactive'
reSwi =  fd_group['betas'].loc[fd_group["eventTypes"].isin(['reSwitch'])].copy()
reRep =  fd_group['betas'].loc[fd_group["eventTypes"].isin(['reRep'])].copy()
rebetas = fd_group.loc[fd_group["eventTypes"].isin(['reRep'])].copy()
rebetas.loc[:,'betas'] = reSwi.values-reRep.values
rebetas.loc[:,'eventTypes'] = 'Reactive'
SC = fd_group.loc[fd_group["eventTypes"].isin(['reRep'])].copy()
SC.loc[:,'betas'] = (proSwi.values-proRep.values)-(reSwi.values-reRep.values)
SC.loc[:,'eventTypes'] = 'Proactive-Reactive' 
SC.loc[:,'condDiff'] = 'yes'

fd_diff = pd.concat([probetas,rebetas,SC])
outfile = op.join(plotDir,'{ROI}_{analID}_group_diff.pdf'.format(ROI=ROI,analID=analID))
plot_cfg = {'outfile':outfile}
plot.plotTimeCourse(fd_diff,plot_cfg)

print('Finished ROI: {roi}'.format(roi=ROI))