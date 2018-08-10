import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe        # pypeline engine
import nipype.algorithms.modelgen as model  # model generation
import json
import pandas as pd
import sys,os
import os.path as op
from IPython import embed as shell
import pypeUtils as pu
import fmri_workflows as wf

# load configuration file
try:
	jsonfile = sys.argv[1]
except IndexError as e:
    print("Please provide a config file in the command line.")
    sys.exit(-1)
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
os.chdir(baseDir)

subs = cfg['subjects']
#    subs = [int(r) for r in run_mode]
analID = cfg['analID']
workDir = op.abspath(cfg['workDir']).format(analID = analID)
dataDir = op.abspath(op.join(baseDir,'scratch',cfg['fmriprepDir']))
subOutDir_scaf = op.abspath(cfg['subOutDir'].format(analID=cfg['analID']))
outDir = op.abspath(cfg['outDir'])
contrasts = cfg['contrasts']
mniTemplate = cfg['mniTemplate']
fwhm = cfg['fwhm']
analID = cfg['analID']
TR = cfg['TR']
firstlvl_cfg = {'input_units':'secs',
                'TR':2,
                'parameter_source':'FSL',
                'highpass_filter':cfg['highpass_filter'],
                'bases':{'dgamma': {'derivs': True}},
                'model_serial_correlations':True,
                'contrasts':contrasts,
                'fit_armodel':True,
                'mask_size':5,
                'threshold':1000,
                'smooth_autocorr':True}
# make sure root exists
if not op.exists(workDir):
    os.makedirs(workDir)

#########################
###   CREATE NODES   ####
#########################


    #########################
    ###      Helpers      ###
    #########################
fakesubs = subs[:1]
fakesubs = [4,8]

# select one run from the list of all runs
selectSingleRun = pe.Node(util.Function(input_names=['aList','idx'],
                        output_names=['first_item'],function=pu.selectFromList),
                    name="selectSingleRun")
selectSingleRun.inputs.idx = 0 # get the first item

# select one cope from the list of all copes
selectSingleCope = pe.Node(util.Function(input_names=['aList','idx'],
                        output_names=['first_item'],function=pu.selectFromList),
                    name="selectSingleCope")
selectSingleCope.inputs.idx = 0 # get the first item

# select one mask from the list of all masks
selectSingleMask = pe.JoinNode(util.Function(input_names=['aList','idx'],
                        output_names=['first_item'],function=pu.selectFromList),
                    joinsource = 'infosource',joinfield = ['aList'],
                    name="selectSingleMask")
selectSingleMask.inputs.idx = 0 # get the first item



# create a function Node that fills in the subject number for the output
createSubOutDir = pe.Node(util.Function(function = pu.setSubOutDir,
                    input_names=['sub_no','subOutDir'],
                    output_names=['subOutDir']),
                name = 'createSubOutDir')
createSubOutDir.inputs.subOutDir = subOutDir_scaf

    #########################
    ###   Preliminaries   ###
    #########################

# create sub info
infosource = pe.Node(util.IdentityInterface(fields=['sub_no']),name="infosource")
#infosource.iterables = [('sub_no', fakesubs)]
infosource.iterables = [('sub_no', subs)]

# collect all the subject files
templates = {'func': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*MNI*_preproc.nii.gz',
             'mask': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*MNI*_brainmask.nii.gz',
             'events': '/home/data/foraging/sub-{sub_no:02d}/func/sub-{sub_no:02d}*events.tsv',
             'confounds': 'sub-{sub_no:02d}/func/*confounds.tsv'}
selectSubs = pe.Node(nio.SelectFiles(templates,base_directory = dataDir),name='selectSubs')

# create the Bunch Struct
collectRunInfo = pe.MapNode(
                util.Function(function = pu.createDesignInfo,
                    input_names=['evFile','confoundFile','parameters'],
                    output_names=['runInfo']),
                iterfield=['evFile','confoundFile'],name = 'collectRunInfo')
collectRunInfo.inputs.parameters = cfg

# get the RT per subject (using existing functions)
mergeRunInfo = pe.Node(util.Function(function = pu.mergeDesignInfo,
                input_names=['bunch_files'],
                output_names=['merged_dms']),
            name = 'mergeRunInfo')
# create a standard space brain mask, necessary to run FLAMEO per sub
createBrainMask = pe.Node(fsl.FLIRT(),
            name = 'createBrainMask')
createBrainMask.inputs.in_file = mniTemplate
createBrainMask.inputs.no_search = True
createBrainMask.inputs.uses_qform = True
createBrainMask.inputs.apply_xfm = True
createBrainMask.inputs.interp = 'trilinear'

# Scale the median value of the run is set to 10000
getMeanFactor = pe.MapNode(util.Function(function = pu.getmeanscale, 
                    input_names=['median'],
                    output_names=['medianFactor']),
                iterfield=['median'],name = 'getMeanFactor')

meanscale = pe.MapNode(fsl.ImageMaths(suffix='_gms'),
                iterfield=['in_file', 'op_string'],
            name='meanscale')

# Perform temporal highpass filtering on the data
hpFilter = pe.MapNode(fsl.TemporalFilter(),
                iterfield = ['in_file'],name = 'hpFilter')
hpFilter.inputs.highpass_sigma = cfg['highpass_filter']/(2*TR) # corresponds to 50 s

# Add back the mean removed by the hp filter 
meanFunc_hp = pe.MapNode(fsl.MeanImage(),
            iterfield=['in_file'], name='meanFunc_hp')
addmean = pe.MapNode(fsl.BinaryMaths(operation='add'),
                iterfield=['in_file', 'operand_file'],
            name='addmean')


# create a data sink to store some output files
datasink = pe.Node(interface=nio.DataSink(parameterization=True),
            name="datasink")
groupsink = pe.Node(interface=nio.DataSink(parameterization=True),
            name="groupsink")
groupsink.base_directory = op.join(baseDir,'scratch/group_level/{analID}'.format(analID=analID))


    #########################
    ###  Thirdlvl Model   ###
    #########################

if run_mode == 'three-levels':
    # count how many images were concatenated
    getImgDim = pe.Node(
                    util.Function(function = pu.getDimSize,
                        input_names=['image','dim'],
                        output_names=['dimSize']),
                    name = 'getImgDim')
    getImgDim.inputs.dim = 3

    collectSubCopes = pe.JoinNode(
                    util.IdentityInterface(
                        fields=['cope_list','var_cope_list']),
                joinsource = 'infosource',
                joinfield = ['cope_list','var_cope_list'], 
                name = 'collectSubCopes')
    collectSubVarCopes = pe.JoinNode(
                    util.IdentityInterface(
                        fields=['cope_list','var_cope_list']),
                     joinsource = 'infosource',
                     joinfield = ['cope_list','var_cope_list'],
                    name = 'collectSubVarCopes')

    # Collect all the subjects and transform (sub x copes) to (copes x subs)
    transposeSubCopes = pe.Node(
                    util.Function(function = pu.transpose,
                        input_names=['aNestedList'],
                        output_names=['transposedList']),
                     name = 'transposeSubCopes')
    transposeSubVarCopes = pe.Node(
                    util.Function(function = pu.transpose,
                        input_names=['aNestedList'],
                        output_names=['transposedList']),
                    name = 'transposeSubVarCopes')

    # merge subjects, separately for copes
    copemerge_group = pe.MapNode(interface=fsl.Merge(dimension='t'),
            iterfield = ['in_files'], name='copemerge_group')
    varcopemerge_group = pe.MapNode(interface=fsl.Merge(dimension='t'),
            iterfield = ['in_files'], name='varcopemerge_group')   

    # set up 3rd level design matrix -- simple average
    level3model = pe.Node(interface=fsl.L2Model(),
            name='l3model')

    # run thirdlevel model - simple average of 2ndlvl but with Flame
    FLAME12=pe.MapNode(interface=fsl.FLAMEO(
                run_mode='flame12'),
            iterfield = ['cope_file','var_cope_file'],
            name='FLAME12')
    
    smoothest=pe.MapNode(interface=fsl.SmoothEstimate(
                dof = len(subs)),
            iterfield = ['residual_fit_file'], name='smoothest')    

    # cluster-based correction of activatio
    clusterCorrection=pe.MapNode(interface=fsl.Cluster(),
            iterfield = ['in_file','dlh','volume'],name='clusterCorrect')
    clusterCorrection.inputs.threshold = cfg['clusterThreshold']
    clusterCorrection.inputs.use_mm = True
    clusterCorrection.inputs.out_localmax_txt_file = 'cluster_stats.txt'
    clusterCorrection.inputs.out_threshold_file = 'z_thresh.nii.gz'
    clusterCorrection.inputs.connectivity = 26
    clusterCorrection.inputs.minclustersize = True
    clusterCorrection.inputs.pthreshold = 0.001
    clusterCorrection.inputs.out_index_file = 'cluster_mask_z.nii.gz'

    outputspec = pe.Node(util.IdentityInterface(
                    fields=['res4d', 'copes', 'varcopes', 'zstats', 'tstats',\
                'localmax_txt_file','threshold_file','index_file','stats_dir']),
            name='outputspec')

    # have a version with non-parametric test
    randomise = pe.MapNode(interface=fsl.Randomise(),
            iterfield = ['in_file'],name='tfce_correction')
    randomise.inputs.tfce = True
    randomise.inputs.var_smooth = 5
    randomise.inputs.vox_p_values = True
    randomise.inputs.one_sample_group_mean = True

    # extract clusters for ROI analysis from TFCE results

    flattenList = pe.MapNode(util.Function(function=pu.selectFromList,
                        input_names=['aList','idx'],output_names=['first_item']),
                        iterfield = ['aList'], name="flattenList")
    flattenList.inputs.idx = 0 # get the first item   
     
    binarizeTFCE = pe.MapNode(interface=fsl.MultiImageMaths(),
                iterfield = ['in_file','operand_files'],
            name='binarizeTFCE')
    binarizeTFCE.inputs.op_string = '-thr 0.95 -bin -mul %s'
    binarizeTFCE.inputs.out_file = 'thresh_tstat.nii.gz'

    extractCluster = pe.MapNode(interface=fsl.Cluster(threshold = 0.0001),
                iterfield = ['in_file'],
            name='extractCluster')
    extractCluster.inputs.out_localmax_txt_file = 'cluster_lmax.txt'
    extractCluster.inputs.out_index_file = 'cluster_index.nii.gz'
    extractCluster.inputs.out_size_file = 'cluster_size'
    extractCluster.inputs.use_mm = True

    # get the RT per subject (using existing functions)
    computeMeanRT = pe.JoinNode(util.Function(function = pu.getMeanRT,
                    input_names=['evBunch'],
                    output_names=['meanRT']),
                joinsource = 'infosource', joinfield = ['evBunch'],
                name = 'computeMeanRT')

    # select one run from the list of all runs
    printMean = pe.Node(util.Function(input_names=['info'],
                    output_names=[],function=pu.printFile),name="printMean")



###########################
####   CONNECT NODES   ####
###########################
# susan smoothing
susan = wf.createSusan('susan',fwhm = fwhm)
susan.base_dir = workDir # set working directory

# connect first level workflow
firstlevel = wf.createFSL_firstlvl('firstlevel',cfg = firstlvl_cfg)
firstlevel.base_dir = workDir # set working directory

# connect second level workflow
secondlevel = wf.create2ndlvl('secondlevel')
secondlevel.base_dir = workDir # set working directory
secondlevel.inputs.inputspec.groupContrasts = cfg['groupContrasts'] 

# connect third level workflow
if run_mode == 'three-levels':
    thirdlevel = pe.Workflow(name='thirdlevel')
    thirdlevel.base_dir = workDir # set working directory
    thirdlevel.connect(copemerge_group,'merged_file',FLAME12,'cope_file')
    thirdlevel.connect(varcopemerge_group,'merged_file',FLAME12,'var_cope_file')
    thirdlevel.connect(level3model,'design_mat',FLAME12,'design_file')
    thirdlevel.connect(level3model,'design_con',FLAME12,'t_con_file')
    thirdlevel.connect(level3model,'design_grp',FLAME12,'cov_split_file')
    thirdlevel.connect(copemerge_group,'merged_file',selectSingleCope,'aList')
    thirdlevel.connect(selectSingleCope,'first_item',getImgDim,'image')
    thirdlevel.connect(getImgDim,'dimSize',level3model,'num_copes')
    thirdlevel.connect(FLAME12,'zstats',clusterCorrection,'in_file')
    thirdlevel.connect(FLAME12,'res4d',smoothest,'residual_fit_file')
    thirdlevel.connect(smoothest,'dlh',clusterCorrection,'dlh')
    thirdlevel.connect(smoothest,'volume',clusterCorrection,'volume')
    thirdlevel.connect(copemerge_group,'merged_file',randomise,'in_file')
    thirdlevel.connect(randomise,'t_corrected_p_files',flattenList,'aList')
    thirdlevel.connect(flattenList,'first_item',binarizeTFCE,'in_file')
    thirdlevel.connect(randomise,'tstat_files',binarizeTFCE,'operand_files')
    thirdlevel.connect(binarizeTFCE,'out_file',extractCluster,'in_file')
# connect meta flow to subflows and 
metaflow = pe.Workflow(name='metaflow')
metaflow.base_dir = workDir # set working directory
metaflow.config = {
    "execution": {"crashdump_dir": op.abspath(op.join(workDir,'crashdumps'))}}

# preliminaries
metaflow.connect(infosource,'sub_no',selectSubs,'sub_no') 
metaflow.connect(infosource,'sub_no',createSubOutDir,'sub_no')
metaflow.connect(selectSubs,'func',selectSingleRun,'aList')
metaflow.connect(selectSingleRun,'first_item',createBrainMask,'reference')
metaflow.connect(selectSubs,'func',susan,'inputspec.in_files')
metaflow.connect(selectSubs,'mask',susan,'inputspec.mask_files')
metaflow.connect(susan,'outputspec.smoothed_file',meanscale,'in_file')
metaflow.connect(susan,'outputspec.median',getMeanFactor,'median')
metaflow.connect(getMeanFactor,'medianFactor',meanscale,'op_string')
metaflow.connect(meanscale,'out_file',hpFilter,'in_file')
metaflow.connect(meanscale,'out_file',meanFunc_hp,'in_file')
metaflow.connect(meanFunc_hp,'out_file',addmean,'operand_file')
metaflow.connect(hpFilter,'out_file',addmean,'in_file')
# datasinking
metaflow.connect(createSubOutDir,'subOutDir',datasink,'base_directory')

# create a Bunch object and first level
metaflow.connect(selectSubs,'events',collectRunInfo,'evFile')
metaflow.connect(selectSubs,'confounds',collectRunInfo,'confoundFile')
metaflow.connect(collectRunInfo,'runInfo',mergeRunInfo,'bunch_files')
metaflow.connect(mergeRunInfo,'merged_dms',computeMeanRT,'evBunch')
metaflow.connect(computeMeanRT,'meanRT',printMean,'info')
metaflow.connect(collectRunInfo,'runInfo',firstlevel,'inputspec.subject_info')
metaflow.connect(addmean,'out_file',firstlevel,'inputspec.func_files')

# 2nd lvl
metaflow.connect(collectRunInfo,'runInfo',secondlevel,'inputspec.runInfo') 
metaflow.connect(firstlevel,'filmgls.copes',secondlevel,'inputspec.cope_files') 
metaflow.connect(firstlevel,'filmgls.varcopes',secondlevel,'inputspec.varcope_files') 
metaflow.connect(createBrainMask,'out_file',secondlevel,'inputspec.mask_files') 


# 3rd level
if run_mode == 'three-levels':
    metaflow.connect(secondlevel,'outputspec.cope_files',collectSubCopes,'cope_list') 
    metaflow.connect(secondlevel,'outputspec.varcope_files',collectSubCopes,'var_cope_list') 
    metaflow.connect(createBrainMask,'out_file',selectSingleMask,'aList')
    metaflow.connect(selectSingleMask,'first_item',thirdlevel,'FLAME12.mask_file')
    metaflow.connect(collectSubCopes,'cope_list',transposeSubCopes,'aNestedList') 
    metaflow.connect(collectSubCopes,'var_cope_list',transposeSubVarCopes,'aNestedList') 
    metaflow.connect(transposeSubCopes,'transposedList',thirdlevel,'copemerge_group.in_files') 
    metaflow.connect(transposeSubVarCopes,'transposedList',thirdlevel,'varcopemerge_group.in_files') 
    metaflow.connect(selectSingleMask,'first_item',thirdlevel,'smoothest.mask_file')



#3rd lvl sinking
metaflow.connect(thirdlevel,'clusterCorrect.localmax_txt_file',outputspec,'localmax_txt_file')
metaflow.connect(thirdlevel,'clusterCorrect.index_file',outputspec,'index_file')
metaflow.connect(thirdlevel,'clusterCorrect.threshold_file',outputspec,'threshold_file')
metaflow.connect(thirdlevel,'FLAME12.stats_dir',outputspec,'stats_dir')


metaflow.connect(selectSingleMask,'first_item',groupsink,'masks.@brainMaskMNI_native')
metaflow.connect(outputspec,'localmax_txt_file',groupsink,'stats')
metaflow.connect(outputspec,'threshold_file',groupsink,'stats.cluster.@thr')
metaflow.connect(outputspec,'index_file',groupsink,'stats.cluster.@cluster')
metaflow.connect(outputspec,'stats_dir',groupsink,'stats.stats')


###########################
####    RUN WORKFLOW   ####
###########################
# make a graph
metaflow.write_graph(graph2use='colored', format='png',dotfilename=op.join(workDir,'graphs','graph_colored.dot'), simple_form=True)
metaflow.write_graph(graph2use='exec', format='png',dotfilename=op.join(workDir,'graphs','graph_exec.dot'), simple_form=True)

#shell()
#metaflow.run()
#metaflow.run(plugin='MultiProc', plugin_args={'n_procs' : 15})
metaflow.run(plugin='CondorDAGMan')
