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


#########################
###   SET PARAMETERS  ###
#########################
baseDir = cfg['baseDir']
subs = cfg['subjects']
workDir = op.abspath(cfg['workDir'])
dataDir = op.abspath(op.join(baseDir,'scratch',cfg['fmriprepDir']))
subOutDir_scaf = op.abspath(cfg['subOutDir'].format(analID=cfg['analID']))
outDir = op.abspath(cfg['outDir'])
contrasts = cfg['contrasts']
mniTemplate = cfg['mniTemplate']
fwhm = cfg['fwhm']
os.chdir(workDir)

#########################
###   CREATE NODES   ####
#########################


    #########################
    ###      Helpers      ###
    #########################
fakesubs = subs[:1]
# just a couple of printing nodes
printing = pe.Node(util.Function(input_names=["info"],output_names=[],
                    function=pu.printOutput),
                name="printing")
printing3 = pe.Node(util.Function(input_names=["info"],output_names=[],
                    function=pu.printOutput),
                name="printing3")

selectSingleRun = pe.Node(util.Function(input_names=['aList','idx'],
                        output_names=['func_file'],function=pu.selectFromList),
                    name="selectSingleRun")
selectSingleRun.inputs.idx = 0 # get the first item

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
infosource.iterables = [('sub_no', fakesubs)]
#infosource.iterables = [('sub_no', subs)]

# collect all the subject files
templates = {'anat': 'sub-{sub_no:02d}/anat/sub-{sub_no:02d}_T1w*MNI*preproc.nii.gz',
             'func': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*MNI*_preproc.nii.gz',
             'events': '/home/data/foraging/sub-{sub_no:02d}/func/sub-{sub_no:02d}*events.tsv',
             'subInfo': '/home/data/foraging/participants.tsv',
             'confounds': 'sub-{sub_no:02d}/func/*confounds.tsv'}
selectSubs = pe.Node(nio.SelectFiles(templates,base_directory = dataDir),name='selectSubs')

# create the Bunch Struct
collectRunInfo = pe.MapNode(
                util.Function(function = pu.createDesignInfo,
                    input_names=['evFile','confoundFile','parameters'],
                    output_names=['runInfo']),
                iterfield=['evFile','confoundFile'],name = 'collectRunInfo')
collectRunInfo.inputs.parameters = cfg

# create a standard space brain mask, necessary to run FLAMEO
createBrainMask = pe.Node(fsl.FLIRT(),name = 'createBrainMask')
createBrainMask.inputs.in_file = mniTemplate
createBrainMask.inputs.no_search = True

# smoothing
if fwhm > 1:
    smooth = pe.MapNode(fsl.Smooth(fwhm=fwhm),iterfield=['in_file'],name="smooth")

# create a data sink to store some output files
datasink = pe.Node(interface=nio.DataSink(parameterization=False),
            name="datasink")

    #########################
    ###   Firstlvl Model  ###
    #########################

# set up model
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

l1Feat = pe.MapNode(fsl.FEATModel(), iterfield = ['fsf_file','ev_files'], name='l1Feat')

filmgls= pe.MapNode(fsl.FILMGLS(fit_armodel = True,
                mask_size = 5,threshold = 1000,smooth_autocorr=True),
            iterfield = ['design_file','tcon_file','in_file'], name='filmgls')

# drop empty VAR copes
getImgDim = pe.MapNode(
                util.Function(function = pu.getDimSize,
                    input_names=['image','dim'],
                    output_names=['dimSize']),
                iterfield=['image'],name = 'getImgDim')
getImgDim.inputs.dim = 3
    #########################
    ###  Secondlvl Model  ###
    #########################

# Transpose the Run/cope matrix to feed it right into the 2ndlvl
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

copemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
    iterfield = ['in_files'], name='copemerge')
varcopemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
    iterfield = ['in_files'], name='varcopemerge')   
level2model = pe.MapNode(interface=fsl.L2Model(),
    iterfield = ['num_copes'],name='l2model')
FE=pe.MapNode(interface=fsl.FLAMEO(
        run_mode='fe'),
    iterfield = ['design_file','t_con_file','cov_split_file','cope_file','var_cope_file'],
    name='FE')

    #########################
    ###  Thirdlvl Model   ###
    #########################

collect2ndLvlCopes = pe.Node(util.IdentityInterface(
        fields=['copes','varcopes']),
        name="collect2ndLvlCopes")

printing2 = pe.JoinNode(util.Function(input_names=["info"],output_names=[],
                    function=pu.printOutput),
               joinsource = 'infosource', 
               joinfield = ['info'],name="printing2")


transposeSubCopes = pe.JoinNode(
                util.Function(function = pu.transpose,
                    input_names=['aNestedList'],
                    output_names=['transposedList']),
                 joinsource = 'infosource',
                 joinfield = ['aNestedList'], name = 'transposeSubCopes')
transposeSubVarCopes = pe.JoinNode(
                util.Function(function = pu.transpose,
                    input_names=['aNestedList'],
                    output_names=['transposedList']),
                 joinsource = 'infosource',
                 joinfield = ['aNestedList'], name = 'transposeSubVarCopes')

copemerge_group = pe.MapNode(interface=fsl.Merge(dimension='t'),
    iterfield = ['in_files'], name='copemerge_group')
varcopemerge_group = pe.MapNode(interface=fsl.Merge(dimension='t'),
    iterfield = ['in_files'], name='varcopemerge_group')   

level3model = pe.Node(interface=fsl.MultipleRegressDesign(),
                      name='l3model')
FLAME=pe.Node(interface=fsl.FLAMEO(
            run_mode='flame1'),
        name='FE')



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
secondlevel.connect(copemerge,'merged_file',FE,'cope_file')
secondlevel.connect(varcopemerge,'merged_file',FE,'var_cope_file')
secondlevel.connect(copemerge,'merged_file',getImgDim,'image')
secondlevel.connect(getImgDim,'dimSize',level2model,'num_copes')
secondlevel.connect(level2model,'design_mat',FE,'design_file')
secondlevel.connect(level2model,'design_con',FE,'t_con_file')
secondlevel.connect(level2model,'design_grp',FE,'cov_split_file')

# connect meta flow
modelfit = pe.Workflow(name='modelfit')
modelfit.base_dir = workDir # set working directory
modelfit.config = {
    "execution": {"crashdump_dir": op.abspath(op.join(workDir,'nipype/crashdumps'))}}

modelfit.connect(infosource,'sub_no',selectSubs,'sub_no') 
modelfit.connect(infosource,'sub_no',createSubOutDir,'sub_no')

modelfit.connect(createSubOutDir,'subOutDir',datasink,'base_directory')
modelfit.connect(selectSubs,'func',smooth,'in_file')

modelfit.connect(selectSubs,'func',selectSingleRun,'aList')
modelfit.connect(selectSingleRun,'func_file',createBrainMask,'reference')

# create a Bunch object
modelfit.connect(selectSubs,'events',collectRunInfo,'evFile')
modelfit.connect(selectSubs,'confounds',collectRunInfo,'confoundFile')
modelfit.connect(collectRunInfo,'runInfo',firstlevel,'level1.subject_info')
modelfit.connect(smooth,'smoothed_file',firstlevel,'level1.functional_runs')
modelfit.connect(smooth,'smoothed_file',firstlevel,'filmgls.in_file')
#modelfit.connect(createSubOutDir,'subOutDir',firstlevel,'filmgls.results_dir')

# 2nd lvl
modelfit.connect(collectRunInfo,'runInfo',transposeCopes,'bunch_files')
modelfit.connect(collectRunInfo,'runInfo',transposeVarCopes,'bunch_files')

modelfit.connect(firstlevel,'filmgls.copes',transposeCopes,'aNestedList')
modelfit.connect(firstlevel,'filmgls.varcopes',transposeVarCopes,'aNestedList')

modelfit.connect(transposeCopes,'transposedList',secondlevel,'copemerge.in_files')
modelfit.connect(transposeVarCopes,'transposedList',secondlevel,'varcopemerge.in_files')
modelfit.connect(createBrainMask,'out_file',secondlevel,'FE.mask_file')

# 3rd level
"""
modelfit.connect(secondlevel,'FE.copes',collect2ndLvlCopes,'copes') 
modelfit.connect(secondlevel,'FE.var_copes',collect2ndLvlCopes,'varcopes') 
modelfit.connect(collect2ndLvlCopes,'copes',printing2,'info') 
modelfit.connect(secondlevel,'FE.copes',transposeSubCopes,'aNestedList') 
modelfit.connect(secondlevel,'FE.var_copes',transposeSubVarCopes,'aNestedList') 
modelfit.connect(transposeSubCopes,'transposedList',copemerge_group,'in_files') 
modelfit.connect(transposeSubVarCopes,'transposedList',varcopemerge_group,'in_files') 
"""
###########################
####    RUN WORKFLOW   ####
###########################
# make a graph
modelfit.write_graph(graph2use='colored', format='png',dotfilename=op.join(workDir,'graph_colored.dot'), simple_form=True)
modelfit.write_graph(graph2use='exec', format='png',dotfilename=op.join(workDir,'graph_exec.dot'), simple_form=True)

#shell()
res = modelfit.run(plugin='MultiProc', plugin_args={'n_procs' : 10})
#res = modelfit.run()





"""
# Contrasts
cont01 = ['proSwitch>0',      'T', condition_names, [1,0,0,0,0,0]]
cont02 = ['reSwitch>0',       'T', condition_names, [0,1,0,0,0,0]]
cont03 = ['proRep>0',         'T', condition_names, [0,0,1,0,0,0]]
cont04 = ['reRep>0',          'T', condition_names, [0,0,0,1,0,0]]
cont05 = ['proSwitch-proRep', 'T', condition_names, [0.5, 0,-0.5,0,0,0]]
cont06 = ['proRep-proSwitch', 'T', condition_names, [-0.5, 0,0.5,0,0,0]]
cont07 = ['reSwitch-reRep',   'T', condition_names, [0, 0.5,0,-0.5,0,0]]
cont08 = ['reRep-reSwitch',   'T', condition_names, [0, -0.5,0,0.5,0,0]]
cont09 = ['proSC-reSC',       'T', condition_names, [0.5, -0.5,-0.5,0.5,0,0]]
cont10 = ['reSC-proSC',       'T', condition_names, [-0.5, 0.5,0.5,-0.5,0,0]]
cont11 = ['proactive-reactive','T', condition_names, [0.5, -0.5,0.5,-0.5,0,0]]
cont12 = ['reactive-proactive','T', condition_names, [0.5, -0.5,-0.5,0.5,0,0]]
cont13 = ['switch-rep',        'T', condition_names, [0.5, 0.5,-0.5,-0.5,0,0]]
cont14 = ['rep-switch',        'T', condition_names, [-0.5, -0.5,0.5,0.5,0,0]]
cont15 = ['proSwitch-reSwitch','T', condition_names, [0.5, -0.5,0,0,0,0]]
cont16 = ['reSwitch-proSwitch','T', condition_names, [-0.5, 0.5,0,0,0,0]]

contrast_list = [cont01, cont02, cont03, cont04, cont05, cont06, \
                cont07, cont08, cont09, cont10, cont11, cont12,\
                cont13, cont014, cont15, cont16]

# Condition names
condition_names = ['proSwitch', 'reSwitch','proRep','reRep','cue','error']
# Contrasts
contrasts = [\
    ["proSwitch>0",      "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [1,0,0,0,0,0]],\
    ["reSwitch>0",       "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0,1,0,0,0,0]],\
    ["proRep>0",         "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0,0,1,0,0,0]],\
    ["reRep>0",          "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0,0,0,1,0,0]],\
    ["proSwitch-proRep", "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0.5, 0,-0.5,0,0,0]],\
    ["proRep-proSwitch", "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [-0.5, 0,0.5,0,0,0]],\
    ["reSwitch-reRep",   "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0, 0.5,0,-0.5,0,0]],\
    ["reRep-reSwitch",   "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0, -0.5,0,0.5,0,0]],\
    ["proSC-reSC",       "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0.5, -0.5,-0.5,0.5,0,0]],\
    ["reSC-proSC",       "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [-0.5, 0.5,0.5,-0.5,0,0]],\
    ["proactive-reactive","T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0.5, -0.5,0.5,-0.5,0,0]],\
    ["reactive-proactive","T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0.5, -0.5,-0.5,0.5,0,0]],\
    ["switch-rep",        "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0.5, 0.5,-0.5,-0.5,0,0]],\
    ["rep-switch",        "T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [-0.5, -0.5,0.5,0.5,0,0]],\
    ["proSwitch-reSwitch","T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [0.5, -0.5,0,0,0,0]],\
    ["reSwitch-proSwitch","T", ["proSwitch", "reSwitch","proRep","reRep","cue","error"], [-0.5, 0.5,0,0,0,0]]]
"""