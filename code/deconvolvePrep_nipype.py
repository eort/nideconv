import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe        # pypeline engine
import nipype.algorithms.modelgen as model  # model generation
import json
import pandas as pd
import sys,os,glob
import os.path as op
from IPython import embed as shell
import pypeUtils as pu
import fmri_workflows as wf


# load configuration file
try:
	jsonfile = sys.argv[1]
except IndexError as e:
	jsonfile = '/home/data/foraging/derivatives/configFiles/deconvolution/deconvolve_nipype.json'
try:	
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
except IOError as e:
        print("The provided file does not exist. Either put a default .json file \
        in the directory of this script, or provide a valid file in the command line.")
        sys.exit(-1)

# add option to run only two levels. This makes it possible 
# to spread subjects across nodes and speed up the analysis
# (maybe, haven't tested it, and it depends on how many nodes I get, I suppose)
try:
    run_mode = sys.argv[2]
except IndexError as e:
    run_mode = 'three-levels'

#########################
###   SET PARAMETERS  ###
#########################
baseDir = cfg['baseDir']

maskID = cfg['maskID']
analID = cfg['analID']
preprocID= cfg['preprocID']
subs = ['sub-{sub:02d}'.format(sub=sub) for sub in cfg['subjects']]
workDir = op.abspath(op.join(baseDir,cfg['workDir'].format(analID=analID)))
dataDir = op.abspath(op.join(baseDir,cfg['fmriprepDir']))
maskDir = op.abspath(op.join(baseDir,cfg['maskDir']))
TR = cfg['TR']
hpfilter_cutoff = cfg['hpfilter_cutoff']
preprocNifti_dir = cfg['PreprocFunc'].format(preprocID=preprocID)
preprocDM_dir = cfg['PreprocDM'].format(analID=analID)
preprocMask_dir = cfg['PreprocMask'].format(maskID=maskID)
    #########################
    ###     META FLOW     ###
    #########################

fakesubs = subs[:1]

# create sub info
infosource = pe.Node(util.IdentityInterface(fields=['sub']),name="infosource")
#infosource.iterables = [('sub', fakesubs)]
infosource.iterables = [('sub', subs)]

# collect all the subject files
templates = {'func': '{sub}/func/{sub}*MNI*_preproc.nii.gz',
             'events': '/home/data/foraging/{sub}/func/{sub}*events.tsv',
             'confounds': '{sub}/func/*confounds.tsv'}
# depending on mode, add already preprocessed data

try: 
    # analyses already run,i.e. do folders exist?
    fooNiftis = glob.glob(op.join(baseDir,preprocNifti_dir.format(sub='*')))
    fooDMs = glob.glob(op.join(baseDir,preprocDM_dir.format(sub='*')))
    # if folders exist, are files in there and do I want to load them as well?
    if (len(fooNiftis) != 0 and len(fooDMs)== len(fooNiftis)) and \
        cfg['preloadFunc']:  
        templates['merged_psc_files'] = op.join(baseDir,preprocNifti_dir)
        runPreprocFlow = 0
    else:
        raise Exception
except: 
    runPreprocFlow = 1

# depending on mode, add already created masks
try:
    fooMasks = glob.glob(op.join(baseDir,preprocMask_dir))
    if len(fooMasks) != 0 and cfg['preloadMask']:
        templates['mask_files'] = op.join(baseDir,preprocMask_dir)
        runMaskFlow = 0
    else:
        raise Exception
except:
    runMaskFlow = 1
    mask_cfg = cfg['mask_cfg']
    
# collect func files and set up the sinking
selectSubs = pe.Node(nio.SelectFiles(templates,base_directory = dataDir),
            name='selectSubs')

preproc_sink = pe.Node(interface=nio.DataSink(parameterization=False),
            name="datasink")
preproc_sink.inputs.base_directory = cfg['preprocSignalDir']


# collect all the different ROI masks
selectMasks = pe.Node(nio.DataGrabber(
            base_dir=maskDir,template=cfg['mask_template']), 
        name = 'selectMasks')

# function to extract mask label
extractMaskNames = pe.MapNode(util.Function(function = pu.extractMaskNames,
                    input_names=['mask_file'],
                    output_names=['mask_name']),
                  iterfield = ['mask_file'], name = 'extractMaskNames')

# set up signal extraction    
inputspec_model = pe.Node(util.IdentityInterface(
                fields=['merged_func_file','rois','mask_names']),
            name='inputspec_model')

extractSignal = pe.MapNode(util.Function(function = pu.extractSignal,
                    input_names=['in_file','roi'],
                    output_names=['av_signal']),
                  iterfield = ['roi'], name = 'extractSignal')
###########################
####  CONNECT WORKFLOW ####
###########################

# connect deconvolution workflow
modelflow = pe.Workflow(name='modelflow')
modelflow.base_dir = workDir # set working directory
modelflow.connect(inputspec_model,'rois',extractSignal,'roi')
modelflow.connect(inputspec_model,'merged_func_file',extractSignal,'in_file')

# connect meta flow to subflows
metaflow = pe.Workflow(name='metaflow')
metaflow.base_dir = workDir # set working directory
metaflow.config = {
    "execution": {"crashdump_dir": op.abspath(op.join(workDir,'crashdumps'))}}
metaflow.connect(infosource,'sub',selectSubs,'sub')
metaflow.connect(infosource,'sub',preproc_sink,'container')

#sink extracted signals
metaflow.connect(modelflow, 'extractSignal.av_signal', preproc_sink, 'deconvolution.analyses.{analID}.timeseries'.format(analID=analID))

# connect mask workflow
if runMaskFlow:
    print('Run mask workflow')
    maskflow = wf.createMaskFlow(mask_cfg)
    maskflow.base_dir = workDir # set working directory
    metaflow.connect(selectMasks,'outfiles',maskflow,'inputspec_mask.mask_files')
    metaflow.connect(maskflow,'outputspec_masks.mask_files',modelflow,'inputspec_model.rois')
    metaflow.connect(maskflow,'outputspec_masks.mask_names',modelflow,'inputspec_model.mask_names')
    #sink mask files 
    # TO BE IMPLEMENTED
else:
    print('Skip mask flow. Use masks in {path} instead'.format(path=preprocMask_dir))
    metaflow.connect(selectSubs,'mask_files',extractMaskNames,'mask_file')
    metaflow.connect(selectSubs,'mask_files',modelflow,'inputspec_model.rois')
    metaflow.connect(extractMaskNames,'mask_name',modelflow,'inputspec_model.mask_names')

# connect preproc workflow
if runPreprocFlow:
    print('Run preprocessing pipeline')
    preprocflow = wf.createDeconvolutionPreproc(cfg)
    preprocflow.base_dir = workDir # set working directory
    # connect meta to preproc
    metaflow.connect(selectSubs,'func',preprocflow,'inputspec_preproc.func_files')
    metaflow.connect(selectSubs,'events',preprocflow,'inputspec_preproc.event_files')
    metaflow.connect(selectSubs,'confounds',preprocflow,'inputspec_preproc.confound_files')
    # preproc to model
    metaflow.connect(preprocflow,'outputspec_preproc.merged_psc_files',modelflow,'inputspec_model.merged_func_file')
    # sinking
    metaflow.connect(preprocflow, 'addmean.out_file', preproc_sink, 'deconvolution.preprocNifti.{preprocID}.filtered'.format(preprocID=preprocID))
    metaflow.connect(preprocflow, 'computePSC.out_file', preproc_sink, 'deconvolution.preprocNifti.{preprocID}.psc'.format(preprocID=preprocID))
    metaflow.connect(preprocflow, 'collectRunInfo.runPickle', preproc_sink, 'deconvolution.analyses.{analID}.eventFiles'.format(analID=analID))
    metaflow.connect(preprocflow, 'outputspec_preproc.merged_psc_files', preproc_sink, 'deconvolution.preprocNifti.{preprocID}.psc.@psc'.format(preprocID=preprocID))
    metaflow.connect(preprocflow, 'outputspec_preproc.merged_design_matrices', preproc_sink, 'deconvolution.analyses.{analID}.eventFiles.@eventFiles'.format(analID=analID))
else:
    print('Skip preprocessing pipeline. Instead use {path}'.format(path=preprocNifti_dir))
    metaflow.connect(selectSubs,'merged_psc_files',modelflow,'inputspec_model.merged_func_file')
    
###########################
####    RUN WORKFLOW   ####
###########################

# make a graph
metaflow.write_graph(graph2use='colored', format='png',dotfilename=op.join(workDir,'graphs','graph_colored.dot'), simple_form=True)
#metaflow.write_graph(graph2use='exec', format='png',dotfilename=op.join(workDir,'graphs','graph_exec.dot'), simple_form=True)
# save settings of analysis
os.system('cp {json} {cfg}'.format(json=jsonfile,cfg=op.join(workDir,'config.json')))
os.system('cp {file} {script}'.format(file=__file__,script=op.join(workDir,'script.py')))


#metaflow.run()
#metaflow.run(plugin='MultiProc')
metaflow.run(plugin='CondorDAGMan')
