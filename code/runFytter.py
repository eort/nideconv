import os,json,glob,sys
import os.path as op
import numpy as np
import IO as io
from IPython import embed as shell
import matplotlib as mpl
import cPickle as pickle
mpl.use('Agg')
import seaborn as sns
import matplotlib.pyplot as pl
from fir import FIRDeconvolution 
import pandas as pd
import scipy as sp
from joblib import Parallel, delayed

assert len(sys.argv)==3

try:
    jsonfile = sys.argv[1]
    sub = int(sys.argv[2])
except:
    print "The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line."
    sys.exit(-1)
else:
    with open(jsonfile) as f:    
        cfg = json.load(f)

# set up variables do save writing later
regressType = cfg['regressType'] # what type of regression to perform
analID = cfg['analID']
sigID = cfg['sigID']
baseDir = cfg['baseDir'] # root
signalDir = op.join(baseDir,cfg['signalDir']).format(sub=sub,sigID=sigID) # time series directory
dmDir = op.join(baseDir,cfg['dmDir']).format(sub=sub,sigID=sigID) # event file directory
outDir = op.join(baseDir,cfg['outDir']).format(sub=sub,sigID=sigID,analID=analID) # stats directory
statsDir = op.join(baseDir,outDir,'stats') # stats directory
plotDir = op.join(baseDir,outDir,'figures') # plot directory    
signalTemplate = cfg['signalTemplate']
signal_sample_frequency = cfg['sample_frequency'] # recording freq of signal
deconv_sample_frequency = cfg['deconvolution_frequency'] # how many samples to be taken
deconvolution_interval = cfg['deconvolution_interval'] # time around events

# make folders if they dont exist yet
if not op.exists(plotDir):
    os.makedirs(plotDir)
if not op.exists(statsDir):
    os.makedirs(statsDir)

# load datamatrix
with open(op.join(dmDir,'sub-{sub:02d}_mergedEVs.pkl'.format(sub=sub))) as f:
    dm = pickle.load(f)
events = [np.array(ev) for ev in dm.onsets]
# load data
in_files = glob.glob(signalDir+signalTemplate)
print("Do subject: {sub}".format(sub=sub))

# loop over time series (per ROI)
for f in in_files:
    signal = np.load(f)
    in_d,in_f = op.split(f)    
    
    maskLabel = '-'.join(in_f.split('_')[1:3])
    print("Do mask: {roi}".format(roi=maskLabel))
    
    # run deconvolution
    fd = FIRDeconvolution(
            signal = signal, 
            events = events, 
            event_names = dm.conditions, 
            sample_frequency = signal_sample_frequency,
            durations = {cond:np.array(dm.durations[dm.conditions.index(cond)]) for cond in dm.conditions},
            deconvolution_frequency = deconv_sample_frequency,
            deconvolution_interval = deconvolution_interval)

    fd.create_design_matrix()
    if cfg['add_covariates']:
        all_nuisances = sp.signal.resample(dm.regressors, fd.resampled_signal_size, axis = -1)
        fd.add_continuous_regressors_to_design_matrix(all_nuisances)
    if regressType  == 'lstsq':
        fd.regress(method = 'lstsq')
        fd.bootstrap_on_residuals(nr_repetitions=1000)
    elif regressType == 'ridge':
        fd.ridge_regress(cv = 10, alphas = np.logspace(-5, 3, 15))
    # extract results
    fd.betas_for_events()
    fd.calculate_rsq()

    # plot single subject, per mask, across conditions
    figwidth, figheight = 28, 20
    fig = pl.figure(figsize = (figwidth, figheight/2))

    # don't plot all covariates
    fd.relCovariates = [key for key in fd.covariates.keys() if key in ['proSwitch','reSwitch','proRep','reRep']]
    #fd.relCovariates = fd.covariates
    s = fig.add_subplot(111)
    s.set_title('FIR responses, with bootstrapped SDs, and rsquare of %s in %s'%(fd.rsq[0],maskLabel))
    for i,(dec,ev) in enumerate(zip(fd.betas_per_event_type.squeeze(),fd.covariates.keys())):
        # skip irrelevant conditions
        if ev not in ['cue','error']:
            pl.plot(fd.deconvolution_interval_timepoints, dec)  
            if not regressType == 'ridge':
                # if we haven't used ridge, we can draw CI internvals
                mb = fd.bootstrap_betas_per_event_type[i].mean(axis = -1)
                sb = fd.bootstrap_betas_per_event_type[i].std(axis = -1)
                pl.fill_between(fd.deconvolution_interval_timepoints, 
                            mb - sb, 
                            mb + sb,
                            color = 'k',
                            alpha = 0.1)
    pl.legend(fd.relCovariates)
    sns.despine(offset=10)
    pl.savefig(op.join(plotDir,'deconvolved_sub-%02d_%s_%s.pdf'%(sub,maskLabel,regressType)))
    pl.close()
                      
    # save FIR object for group analysis               
    deconv_results = pd.DataFrame(
                        {'sub': sub, 
                         'rsq':fd.rsq[0],
                         'roi': maskLabel,
                         'eventTypes': np.repeat(fd.covariates.keys(),len(fd.deconvolution_interval_timepoints)),
                         'time': np.tile(fd.deconvolution_interval_timepoints,len(fd.covariates)),
                         'betas': fd.betas_per_event_type.squeeze().flatten()})
    deconv_results.to_csv(op.join(statsDir.format(sub=sub,sigID=sigID,analID=analID),'betas_sub-%02d_%s_%s.csv'%(sub,maskLabel,regressType)))

# copy script and settings to results directory
os.system('cp {json} {cfg}'.format(json=jsonfile,cfg=op.join(outDir,'config.json')))
os.system('cp {file} {script}'.format(file=__file__,script=op.join(outDir,'script.py')))