import os,json,glob,sys
import os.path as op
import numpy as np
import nibabel as nib
from multiprocessing import Pool, cpu_count
import IO as io
from IPython import embed as shell
import matplotlib as mpl
mpl.use('Agg')
import seaborn as sns
import matplotlib.pyplot as pl
import FIRDeconvolution.FIRDeconvolution as fir
import pandas as pd

def fooFunc(sub):
    """
    Helper function to allow for paralleliation of devonvolution
    sub:        Subject ID
    returns:    dataframe with deconvolution results
    """

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
    for maskImg in masks:
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

            # perform deconvolution
            fd = fir(
                    signal = ROIdataSignal, 
                    events = events, 
                    event_names = eventTypes, 
                    sample_frequency = signal_sample_frequency,
                    deconvolution_frequency = deconv_sample_frequency,
                    deconvolution_interval = deconvolution_interval
                    )
            fd.create_design_matrix()
            if regressType  == 'lstsq':
                fd.regress(method = 'lstsq')
                fd.bootstrap_on_residuals(nr_repetitions=1000)
            elif regressType == 'ridge':
                fd.ridge_regress(cv = 10, alphas = np.logspace(-5, 3, 15))

            fd.betas_for_events()
            fd.calculate_rsq()
            deconv_results_mask["BOLD"] = fd.betas_per_event_type.flatten().squeeze()
            deconv_results_mask["time"] = np.tile(fd.deconvolution_interval_timepoints,len(eventTypes))
            deconv_results_mask["sub"] = sub
            deconv_results_mask["roi"] = maskLabel
            deconv_results_mask["rsq"] = fd.rsq[0]
            deconv_results_mask["eventTypes"] = np.array([np.repeat(ev,len(fd.deconvolution_interval_timepoints)) for ev in fd.covariates.keys()]).flatten()

            deconv_results = deconv_results.append(deconv_results_mask,ignore_index=True)

            if singleSub_plotting:
                # figure parameters
                figwidth, figheight = 28, 20
                f = pl.figure(figsize = (figwidth, figheight/2))

                # don't plot all covariates
                fd.relCovariates = [key for key in fd.covariates.keys() if key in ['proSwitch','reSwitch','proRep','reRep']]

                s = f.add_subplot(111)
                s.set_title('FIR responses, with bootstrapped SDs, and rsquare of %s'%(fd.rsq))
                for i,(dec,ev) in enumerate(zip(fd.betas_per_event_type.squeeze(),fd.covariates.keys())):
                    if ev not in ['cue','error']:
                        pl.plot(fd.deconvolution_interval_timepoints, dec)  
                        if not regressType == 'ridge':
                            mb = fd.bootstrap_betas_per_event_type[i].mean(axis = -1)
                            sb = fd.bootstrap_betas_per_event_type[i].std(axis = -1)
                   
                            pl.fill_between(fd.deconvolution_interval_timepoints, 
                                        mb - sb, 
                                        mb + sb,
                                        color = 'k',
                                        alpha = 0.1)
                pl.legend(fd.relCovariates)
                sns.despine(offset=10)
                #pl.show()
                pl.savefig(op.join(outDir%sub,"deconvolved.pdf"))
                pl.close()
    return deconv_results


if len(sys.argv)==2:
    jsonfile = sys.argv[1]
else:
    jsonfile = '/home/data/foraging/configFiles/deconvolve_run_cfg.json'
try:
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
except IOError as e:
    print "The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line."
    sys.exit(-1)



""""""""""""""""""""""""""""""
"LOAD CONFIG FILE PARAMETERS"
""""""""""""""""""""""""""""""

# further settings
baseDir = cfg['baseDir'] # root
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

""""""""""""""""""""""""""""""
"RUN DECONVOLUTION"
""""""""""""""""""""""""""""""
if 0:#cfg["parallel"]: 
    pool = Pool(cpu_count()-10)
    #pool.map(fooFunc,SUBS)
    fd_group_results=fd_group_results.append(pool.map(fooFunc,SUBS),ignore_index=True)
elif 0:#not cfg["parallel"]:
    for sub in SUBS:
        # run subjects and store results in a panda dataframe

        fd_group_results=fd_group_results.append(fooFunc(sub),ignore_index=True)
        
    # save results
    fd_group_results.to_csv(op.join(baseDir,'scratch/results/fd_group_%s.csv'%analID),index=False)

#
if cfg["plotting"]: 
    shell()
    fd_group_results = pd.read_csv(op.join(baseDir,'scratch/results/fd_group_%s.csv'%analID),index_col=None)
    #if singleMaskNifti:
    masks = [m for m in fd_group_results.roi.unique()]
    #masks = [m for m in fd_group_results.roi.unique() if m in masks_IDs]
    evTypes  = fd_group_results.eventTypes.unique()
    evTypes = [ev for ev in evTypes if ev in ['proSwitch','reSwitch','proRep','reRep']]
   
    figwidth, figheight = 28, 20
    # plot time series individually per event 
    f = pl.figure(figsize = (figwidth, figheight/2))
    for i in range(len(masks)):
        subdf = fd_group_results[fd_group_results["roi"]==masks[i]]
        subdf = subdf[subdf["eventTypes"].isin(evTypes)]
        s = f.add_subplot(4,2,i+1)
        s.set_title('FIR responses, with bootstrapped SDs, and rsquare of %s in %s'%(subdf['rsq'].mean(),masks[i]))

        sns.tsplot(data=subdf,condition = 'eventTypes',unit= 'sub',value='BOLD',time='time')  
        pl.tight_layout()        
           
        sns.despine(offset=10)
    pl.legend(evTypes)
    pl.savefig(op.join(baseDir,'scratch/results/group_fd_%s_%s.pdf'%(analID,regressType)))
    #pl.show()

    pl.close()
    # plot time series individually per event 
    f = pl.figure(figsize = (figwidth, figheight/2))
    # compute difference waves between switch and repetition
    diffWave = fd_group_results.loc[fd_group_results.eventTypes.isin(['proSwitch','reSwitch'])]
    diffWave.loc[:,'diffBOLD'] = np.nan
    diffWave.loc[diffWave["eventTypes"] == 'proSwitch','diffBOLD'] = \
        diffWave.BOLD.loc[diffWave["eventTypes"] == 'proSwitch'].values - \
        fd_group_results.BOLD.loc[fd_group_results.eventTypes == 'proRep'].values
    diffWave.loc[diffWave["eventTypes"] == 'reSwitch','diffBOLD'] = \
        diffWave.BOLD.loc[diffWave["eventTypes"] == 'reSwitch'].values - \
        fd_group_results.BOLD.loc[fd_group_results.eventTypes == 'reRep'].values
    diffWave.loc[diffWave['eventTypes'] == 'proSwitch','eventTypes'] = 'proactive'
    diffWave.loc[diffWave['eventTypes'] == 'reSwitch','eventTypes'] = 'reactive'

    for i in range(len(masks)):
        subdf = diffWave[diffWave["roi"]==masks[i]]
        s = f.add_subplot(4,2,i+1)
        s.set_title('Diff Wave FIR responses, with bootstrapped SDs, and rsquare of %s in %s'%(subdf['rsq'].mean(),masks[i]))

        sns.tsplot(data=subdf,condition = 'eventTypes',unit= 'sub',value='BOLD',time='time')  
        pl.legend(subdf.eventTypes.unique())
        pl.tight_layout()
        sns.despine(offset=10)

    pl.savefig(op.join(baseDir,'scratch/results/group_fd_%s_%s_diffWave.pdf'%(analID,regressType)))
    #pl.show()

    pl.close()
    # plot time