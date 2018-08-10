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

# load configuration file
try:
	jsonfile = sys.argv[1]
except IndexError as e:
	jsonfile = '/home/data/foraging/derivatives/configFiles/nipype/GLM_1stlvl_nipype.json'
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
workDir = op.abspath(cfg['workDir'])
dataDir = op.abspath(op.join(baseDir,'scratch',cfg['fmriprepDir']))
subOutDir_scaf = op.abspath(cfg['subOutDir'].format(analID=cfg['analID']))
outDir = op.abspath(cfg['outDir'])
contrasts = cfg['contrasts']
mniTemplate = cfg['mniTemplate']
fwhm = cfg['fwhm']
analID = cfg['analID']
TR = cfg['TR']

#########################
###   CREATE NODES   ####
#########################


    #########################
    ###      Helpers      ###
    #########################
fakesubs = subs[3:4]

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

# create a function Node that fills in the subject number for the output
makeDesignFigures = pe.MapNode(util.Function(
                function = pu.makeDesignFig,
                    input_names=['design_file'],
                    output_names=[]),
                iterfield = ['design_file'], name = 'makeDesignFigures')


    #########################
    ###   Preliminaries   ###
    #########################

# create sub info
infosource = pe.Node(util.IdentityInterface(fields=['sub_no']),name="infosource")
#infosource.iterables = [('sub_no', fakesubs)]
infosource.iterables = [('sub_no', subs)]

# collect all the subject files
templates = {'func': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*MNI*_preproc.nii.gz',
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

# create a standard space brain mask, necessary to run FLAMEO per sub
createBrainMask = pe.Node(fsl.FLIRT(),
            name = 'createBrainMask')
createBrainMask.inputs.in_file = mniTemplate
createBrainMask.inputs.no_search = True
createBrainMask.inputs.uses_qform = True
createBrainMask.inputs.apply_xfm = True
createBrainMask.inputs.interp = 'trilinear'

# get the median intensity for a run, needed for SUSAN
# filled with mask file
get_median = pe.MapNode(fsl.ImageStats(
            op_string='-k %s -p 50'),
    iterfield=['in_file'], name='get_median') 

# get the brightness median and threshold it at 75%, for SUSAN
getBtThreshold = pe.MapNode(
                util.Function(function = pu.getBrightnessThreshold,
                    input_names=['median_values'],
                    output_names=['median_thresholded']),
                iterfield=['median_values'],name = 'getBtThreshold')

# get the usans to be used in SUSAN
getUSANs = pe.MapNode(
                util.Function(function = pu.getUsans,
                    input_names=['func_file','median'],
                    output_names=['usan']),
                iterfield=['func_file','median'],name = 'getUSANs')

# create the mean functional image
meanFunc = pe.MapNode(fsl.MeanImage(),
        iterfield=['in_file'], name='meanFunc')
#smooth = pe.MapNode(fsl.Smooth(fwhm=fwhm),
#            iterfield=['in_file'],name="smooth")
smooth = pe.MapNode(fsl.SUSAN(fwhm=fwhm),
    iterfield=['in_file','brightness_threshold','usans'],name="smooth")

   
# create a data sink to store some output files
datasink = pe.Node(interface=nio.DataSink(parameterization=True),
            name="datasink")
groupsink = pe.Node(interface=nio.DataSink(parameterization=True),
            name="groupsink")
groupsink.base_directory = op.join(baseDir,'scratch/group_level/{analID}'.format(analID=analID))
    #########################
    ###   Firstlvl Model  ###
    #########################

# set up 1stllvl model
level1 = pe.MapNode(model.SpecifyModel(
                input_units='secs',
                time_repetition=cfg['TR'],
                high_pass_filter_cutoff=cfg['highpass_filter']),
            iterfield = ['subject_info','functional_runs'],name='level1')

# Further specify model
level1Design = pe.MapNode(fsl.Level1Design(
                interscan_interval=cfg['TR'],
                bases={'dgamma': {'derivs': True}},
                model_serial_correlations=True,
                contrasts=contrasts), 
            iterfield = ['session_info'],name='level1Design')

# Set up feat
l1Feat = pe.MapNode(fsl.FEATModel(), 
            iterfield = ['fsf_file','ev_files'], name='l1Feat')

# level 1 model estimation
filmgls= pe.MapNode(fsl.FILMGLS(fit_armodel = True,
                mask_size = 5,threshold = 1000,smooth_autocorr=True),
            iterfield = ['design_file','tcon_file','in_file'], name='filmgls')

    #########################
    ###  Secondlvl Model  ###
    #########################

# Transpose (run x cope) to (cope x run)
transposeCopes = pe.Node(
                util.Function(function = pu.transposeAndSelect,
                    input_names=['aNestedList','bunch_files'],
                    output_names=['transposedList']),
                name = 'transposeCopes')
transposeVarCopes = pe.Node(
                util.Function(function = pu.transposeAndSelect,
                    input_names=['aNestedList','bunch_files'],
                    output_names=['transposedList']),
                name = 'transposeVarCopes')

# based on the 4 event PEs, construct the full contrast matrix
make2ndlvlCopes = pe.Node(
                util.Function(function = pu.make2ndLvlDesignMatrix,
                    input_names=['copes'],
                    output_names=['regressors']),
                name = 'make2ndlvlCopes')

# first average across runs
runmergeCOPE = pe.MapNode(interface=fsl.Merge(dimension='t'),
            iterfield = ['in_files'], name='runmergeCOPE')
runmergeVARCOPE = pe.MapNode(interface=fsl.Merge(dimension='t'),
            iterfield = ['in_files'], name='runmergeVARCOPE')  
# Second average across copes, so that new contrasts can be 
# computed, that are specified as regressors in the multi. regression
copeMerge = pe.Node(interface=fsl.Merge(dimension='t'),
            name='copeMerge')
varcopeMerge = pe.Node(interface=fsl.Merge(dimension='t'),
            name='varcopeMerge')    

# regression model to add group level contrasts possible        
level2model = pe.Node(interface=fsl.MultipleRegressDesign(),
            name='multregmodel')
level2model.inputs.contrasts = cfg['groupContrasts']

# fixed effects 2nd lvl model
FE=pe.Node(interface=fsl.FLAMEO(run_mode='fe'),
            name='FE')

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

    # run thirdlevel_F12 model - simple average of 2ndlvl but with Flame
    FLAME12=pe.MapNode(interface=fsl.FLAMEO(
                run_mode='flame12'),
            iterfield = ['cope_file','var_cope_file'],
            name='FLAME12')

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


    smoothest=pe.MapNode(interface=fsl.SmoothEstimate(
                dof = len(subs)),
            iterfield = ['residual_fit_file'], name='smoothest')    

    outputspec = pe.Node(
                util.IdentityInterface(
            fields=['res4d', 'copes', 'varcopes', 'zstats', 'tstats',\
                'localmax_txt_file','threshold_file','index_file','stats_dir']),
name='outputspec')

###########################
####   CONNECT NODES   ####
###########################

# connect first level workflow
firstlevel = pe.Workflow(name='firstlevel')
firstlevel.base_dir = workDir # set working directory
firstlevel.connect(level1,'session_info',level1Design,'session_info')
firstlevel.connect(level1Design,'fsf_files',l1Feat,'fsf_file')
firstlevel.connect(level1Design,'ev_files',l1Feat,'ev_files')
firstlevel.connect(l1Feat,'con_file',filmgls,'tcon_file')
firstlevel.connect(l1Feat,'design_file',filmgls,'design_file')

# connect second level workflow
secondlevel = pe.Workflow(name='secondlevel')
secondlevel.base_dir = workDir # set working directory
secondlevel.connect(runmergeCOPE,'merged_file',copeMerge,'in_files')
secondlevel.connect(runmergeVARCOPE,'merged_file',varcopeMerge,'in_files')
secondlevel.connect(copeMerge,'merged_file',FE,'cope_file')
secondlevel.connect(varcopeMerge,'merged_file',FE,'var_cope_file')
secondlevel.connect(make2ndlvlCopes,'regressors',level2model,'regressors')
secondlevel.connect(level2model,'design_mat',FE,'design_file')
secondlevel.connect(level2model,'design_con',FE,'t_con_file')
secondlevel.connect(level2model,'design_grp',FE,'cov_split_file')

# connect third level workflow
if run_mode == 'three-levels':
    thirdlevel_F12 = pe.Workflow(name='thirdlevel_F12')
    thirdlevel_F12.base_dir = workDir # set working directory
    thirdlevel_F12.connect(copemerge_group,'merged_file',FLAME12,'cope_file')
    thirdlevel_F12.connect(varcopemerge_group,'merged_file',FLAME12,'var_cope_file')
    thirdlevel_F12.connect(level3model,'design_mat',FLAME12,'design_file')
    thirdlevel_F12.connect(level3model,'design_con',FLAME12,'t_con_file')
    thirdlevel_F12.connect(level3model,'design_grp',FLAME12,'cov_split_file')
    thirdlevel_F12.connect(copemerge_group,'merged_file',selectSingleCope,'aList')
    thirdlevel_F12.connect(selectSingleCope,'first_item',getImgDim,'image')
    thirdlevel_F12.connect(getImgDim,'dimSize',level3model,'num_copes')
    thirdlevel_F12.connect(FLAME12,'zstats',clusterCorrection,'in_file')
    thirdlevel_F12.connect(FLAME12,'res4d',smoothest,'residual_fit_file')
    thirdlevel_F12.connect(smoothest,'dlh',clusterCorrection,'dlh')
    thirdlevel_F12.connect(smoothest,'volume',clusterCorrection,'volume')

# connect meta flow to subflows and 
metaflow = pe.Workflow(name='metaflow_fixError')
metaflow.base_dir = workDir # set working directory
metaflow.config = {
    "execution": {"crashdump_dir": op.abspath(op.join(workDir,'nipype/crashdumps'))}}

# preliminaries
metaflow.connect(infosource,'sub_no',selectSubs,'sub_no') 
metaflow.connect(infosource,'sub_no',createSubOutDir,'sub_no')
metaflow.connect(selectSubs,'func',selectSingleRun,'aList')
metaflow.connect(selectSingleRun,'first_item',createBrainMask,'reference')
#metaflow.connect(firstlevel,'l1Feat.design_file',makeDesignFigures,'design_file')
metaflow.connect(selectSubs,'func',get_median,'in_file')
metaflow.connect(selectSubs,'func',smooth,'in_file')
metaflow.connect(get_median,'out_stat',getBtThreshold,'median_values')
metaflow.connect(getBtThreshold,'median_thresholded',getUSANs,'median')
metaflow.connect(selectSubs,'func',meanFunc,'in_file')
metaflow.connect(meanFunc,'out_file',getUSANs,'func_file')
metaflow.connect(getBtThreshold,'median_thresholded',smooth,'brightness_threshold')
metaflow.connect(getUSANs,'usan',smooth,'usans')

# datasinking
metaflow.connect(createSubOutDir,'subOutDir',datasink,'base_directory')

# create a Bunch object and first level
metaflow.connect(selectSubs,'events',collectRunInfo,'evFile')
metaflow.connect(selectSubs,'confounds',collectRunInfo,'confoundFile')
metaflow.connect(collectRunInfo,'runInfo',firstlevel,'level1.subject_info')
metaflow.connect(smooth,'smoothed_file',firstlevel,'level1.functional_runs')
metaflow.connect(smooth,'smoothed_file',firstlevel,'filmgls.in_file')
#metaflow.connect(createSubOutDir,'subOutDir',firstlevel,'filmgls.results_dir')

# 2nd lvl
metaflow.connect(collectRunInfo,'runInfo',transposeCopes,'bunch_files')
metaflow.connect(collectRunInfo,'runInfo',transposeVarCopes,'bunch_files')
metaflow.connect(firstlevel,'filmgls.copes',transposeCopes,'aNestedList')
metaflow.connect(firstlevel,'filmgls.varcopes',transposeVarCopes,'aNestedList')

metaflow.connect(transposeCopes,'transposedList',secondlevel,'make2ndlvlCopes.copes')
metaflow.connect(transposeCopes,'transposedList',secondlevel,'runmergeCOPE.in_files')
metaflow.connect(transposeVarCopes,'transposedList',secondlevel,'runmergeVARCOPE.in_files')
metaflow.connect(createBrainMask,'out_file',secondlevel,'FE.mask_file')

# 3rd level
if run_mode == 'three-levels':

    metaflow.connect(createBrainMask,'out_file',selectSingleMask,'aList')
    metaflow.connect(selectSingleMask,'first_item',thirdlevel_F12,'FLAME12.mask_file')
    metaflow.connect(secondlevel,'FE.copes',collectSubCopes,'cope_list') 
    metaflow.connect(secondlevel,'FE.var_copes',collectSubCopes,'var_cope_list') 
    metaflow.connect(collectSubCopes,'cope_list',transposeSubCopes,'aNestedList') 
    metaflow.connect(collectSubCopes,'var_cope_list',transposeSubVarCopes,'aNestedList') 

    metaflow.connect(transposeSubCopes,'transposedList',thirdlevel_F12,'copemerge_group.in_files') 
    metaflow.connect(transposeSubVarCopes,'transposedList',thirdlevel_F12,'varcopemerge_group.in_files') 
    metaflow.connect(selectSingleMask,'first_item',thirdlevel_F12,'smoothest.mask_file')

#3rd lvl sinking
metaflow.connect(thirdlevel_F12,'clusterCorrect.localmax_txt_file',outputspec,'localmax_txt_file')
metaflow.connect(thirdlevel_F12,'clusterCorrect.index_file',outputspec,'index_file')
metaflow.connect(thirdlevel_F12,'clusterCorrect.threshold_file',outputspec,'threshold_file')
metaflow.connect(thirdlevel_F12,'FLAME12.stats_dir',outputspec,'stats_dir')


metaflow.connect(selectSingleMask,'first_item',groupsink,'masks.@brainMaskMNI_native')
metaflow.connect(outputspec,'localmax_txt_file',groupsink,'stats')
metaflow.connect(outputspec,'threshold_file',groupsink,'stats.cluster.@thr')
metaflow.connect(outputspec,'index_file',groupsink,'stats.cluster.@cluster')
metaflow.connect(outputspec,'stats_dir',groupsink,'stats.stats')


###########################
####    RUN WORKFLOW   ####
###########################
# make a graph
metaflow.write_graph(graph2use='colored', format='png',dotfilename=op.join(workDir,'graph_colored.dot'), simple_form=True)
metaflow.write_graph(graph2use='exec', format='png',dotfilename=op.join(workDir,'graph_exec.dot'), simple_form=True)

#shell()
#res = metaflow.run(plugin='MultiProc', plugin_args={'n_procs' : 15})
#res = metaflow.run(plugin='CondorDAGMan')
