import os,json,glob,sys
import os.path as op
import numpy as np
import nibabel as nib
from multiprocessing import Pool, cpu_count
from IPython import embed as shell
import matplotlib as mpl
mpl.use('Agg')
import seaborn as sns
import matplotlib.pyplot as pl
import pandas as pd

#os.chdir('/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/foraging/code/')
import response_fytter.response_fytter as rf
import FIRDeconvolution.FIRDeconvolution as fir
try:
    jsonfile = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/foraging/configFiles/deconvolve_run_cfg.json'
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
except: 
    jsonfile = '/home/data/foraging/configFiles/deconvolve_run_cfg.json'    
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
    print 'there is soemthing'

""""""""""""""""""""""""""""""
"LOAD CONFIG FILE PARAMETERS"
""""""""""""""""""""""""""""""

# further settings
baseDir = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/foraging/'
baseDir = '/home/data/foraging/'
sigDir = op.join(baseDir,'scratch',cfg['sigDir']) # time series directory
eventDir = op.join(baseDir,cfg['eventDir']) # event file directory
infoDir = op.join(baseDir,cfg['infoDir']) # general info directory
maskDir = op.join(baseDir,'scratch',cfg['maskDir']) # mask directory
plotDir = op.join(baseDir,'scratch',cfg['plotDir']) # result directory
SUBS = cfg['SUBS'] # all subjects to be included
signalForm = cfg['signal'] # time series
eventTypes = cfg['eventTypes'] # which event types to be modelled
signal_sample_frequency = cfg['signal_sample_frequency'] # recording freq of signal
deconv_sample_frequency = cfg['deconv_sample_frequency'] # how many samples to be taken
deconvolution_interval = cfg['deconvolution_interval'] # time around events
regressType = cfg['regressionType'] # what type of regression to perform
singleSub_plotting = cfg['singleSub_plotting'] # what type of regression to perform
masks_IDs = cfg['masks'] # what type of regression to perform
analID = cfg['analID'] # what type of regression to perform
singleMaskNifti = cfg['singleMaskNifti'] # are all masks stored in a single nifti?

# load dictionary that maps ROI in single mask image to index
if singleMaskNifti: 
    jsonfile = op.join(infoDir,'Control31_maskMap_Switch.json')
    with open(jsonfile) as data_file:    
        clusterMapper = json.load(data_file)

# init dataframe for group results
fd_group_results = pd.DataFrame({'sub': [], 'time': [],'rsq':[],\
                        'eventTypes': [], 'roi': [],'BOLD': [] })
sub = SUBS[0]

    # complete directories
signal_sub = op.join(sigDir,signalForm)%(sub,sub)
eventDir_sub = eventDir%(sub)

if not op.exists(plotDir%sub):
    os.makedirs(plotDir%sub)

print 'start deconvolution of sub %02d'%sub

""""""""""""""""""""""""""""""
"Prepare event files"
""""""""""""""""""""""""""""""
# load event files
events = []

for ev in eventTypes:
    eventFiles = glob.glob(eventDir_sub + '/*%s*'%ev)
    eventFiles.sort()
    evTiming = []
    for evIdx,evF in enumerate(eventFiles):
        with open(evF, 'r') as infile:
            for l in infile:
                llist = l.split()
                onset = float(llist[0])
                if onset != 0.0: # exclude empty runs
                    evTiming.append(420*evIdx+onset)
    events.append(np.array(evTiming))

print "Number of events per condition",[(len(ev)) for ev in events]

""""""""""""""""""""""""""""""
"Prepare deconvolution"
""""""""""""""""""""""""""""""
# load signal
funcImg = nib.load(signal_sub) # load nifti
signal = funcImg.get_data() # extract data

# load mask
masks = glob.glob(maskDir%sub + '/*mask*.nii.gz')
masks.sort()
masks = [maskImg for maskImg in masks if op.basename(maskImg).split('_')[0] in masks_IDs]
 

# dataframe to store deconvolution results in
deconv_results = pd.DataFrame({'sub': [], 'time': [],'rsq':[],\
                        'eventTypes': [], 'roi': [],'BOLD': [] })
deconv_results_mask = pd.DataFrame({'sub': [], 'time': [],'rsq':[],\
                    'eventTypes': [], 'roi': [],'BOLD': [] })

# loop over masks
for maskImg in masks[:1]:
    mask = nib.load(maskImg)
    maskData = mask.get_data()
    if singleMaskNifti:
        uniqueMasks = np.unique(np.round(maskData))[1:]
        uniqueMaskLabels = [clusterMapper[str(int(uM))] for uM in uniqueMasks]
    else: 
        uniqueMasks = [1.0]
        maskLabel = op.basename(maskImg).split('_')[0] 

    for clusterIdx in uniqueMasks:
        if singleMaskNifti:
            maskLabel = uniqueMaskLabels[int(clusterIdx)-1]
        
        maskData_cluster=np.array(maskData)
        maskData_cluster[maskData!=clusterIdx] = 0
        ROIdataSignal = signal[maskData_cluster.astype(bool),:].mean(axis = 0)
        #shell()

rfy = rf.ResponseFytter(
            input_signal=ROIdataSignal, 
            input_sample_frequency=signal_sample_frequency)

for evT,ev in zip(eventTypes,events):
    #shell()
    rfy.add_event(
                basis_set = 'fourier',
                n_regressors = 31,
                event_name=evT,
                onset_times=ev,
                interval=deconvolution_interval)

rfy.regress('ridge')
tc = rfy.get_timecourses()
eventsNames = tc["event type"].unique()
# figure parameters
figwidth, figheight = 28, 20
f = pl.figure(figsize = (figwidth, figheight/2))

# don't plot all covariates
#fd.relCovariates = [key for key in fd.covariates.keys() if key in ['proSwitch','reSwitch','proRep','reRep']]

s = f.add_subplot(111)
s.set_title('FIR responses, with bootstrapped SDs, and rsquare of %s in %s'%(rfy.rsq(),maskLabel))

for ev in eventsNames:
    #if ev not in ['cue','error']:
    pl.plot(tc.t.loc[tc['event type'] == ev],tc.signal.loc[tc['event type'] == ev])  

pl.legend(eventsNames)
sns.despine(offset=10)
pl.savefig('testFig_rf_leg.pdf')


        # perform deconvolution
fd = fir(
        signal = ROIdataSignal, 
        events = events, 
        event_names = eventTypes, 
        sample_frequency = signal_sample_frequency,
        deconvolution_frequency = signal_sample_frequency,
        deconvolution_interval = deconvolution_interval
        )
fd.create_design_matrix()
#fd.regress(method = 'lstsq')
fd.ridge_regress(cv = 10, alphas = np.logspace(-5, 3, 15))

fd.betas_for_events()
fd.calculate_rsq()
figwidth, figheight = 28, 20
f = pl.figure(figsize = (figwidth, figheight/2))

# don't plot all covariates
#fd.relCovariates = [key for key in fd.covariates.keys() if key in ['proSwitch','reSwitch','proRep','reRep']]

s = f.add_subplot(111)
s.set_title('FIR responses, with bootstrapped SDs, and rsquare of %s in %s'%(fd.rsq,maskLabel))

for i,(dec,ev) in enumerate(zip(fd.betas_per_event_type.squeeze(),fd.covariates.keys())):
    pl.plot(fd.deconvolution_interval_timepoints, dec)  

pl.legend(fd.covariates)
sns.despine(offset=10)
pl.savefig('testFig_fir.pdf')
 
