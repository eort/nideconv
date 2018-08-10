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
	jsonfile = '/home/data/foraging/derivatives/configFiles/nipype/sinktest_nipype.json'
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
#########################
###   CREATE NODES   ####
#########################


    #########################
    ###      Helpers      ###
    #########################
fakesubs = subs[1:2]

# select one run from the list of all runs
selectSingleCope1 = pe.Node(util.Function(input_names=['aList','idx'],
                        output_names=['first_item'],function=pu.selectFromList),
                    name="selectSingleCope1")
selectSingleCope1.inputs.idx = 0 # get the first item

# select one cope from the list of all copes
selectSingleCope2 = pe.Node(util.Function(input_names=['aList','idx'],
                        output_names=['first_item'],function=pu.selectFromList),
                    name="selectSingleCope2")
selectSingleCope2.inputs.idx = 0 # get the first item
# select one cope from the list of all copes
selectSingleCope3 = pe.Node(util.Function(input_names=['aList','idx'],
                        output_names=['first_item'],function=pu.selectFromList),
                    name="selectSingleCope3")
selectSingleCope3.inputs.idx = 0 # get the first item

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

# collect all the subject files
templates = {'func': 'sub-{sub_no:02d}/func/sub-{sub_no:02d}*MNI*_preproc.nii.gz'}
selectSubs = pe.Node(nio.SelectFiles(templates,base_directory = dataDir),name='selectSubs')


# smoothing
smooth1 = pe.MapNode(fsl.Smooth(fwhm=fwhm),
            iterfield=['in_file'],name="smooth1")
smooth2 = pe.MapNode(fsl.Smooth(fwhm=fwhm),
            iterfield=['in_file'],name="smooth2")
smooth3 = pe.MapNode(fsl.Smooth(fwhm=fwhm),
            iterfield=['in_file'],name="smooth3")
smooth4 = pe.MapNode(fsl.Smooth(fwhm=fwhm),
            iterfield=['in_file'],name="smooth4")
smooth5 = pe.MapNode(fsl.Smooth(fwhm=fwhm),
            iterfield=['in_file'],name="smooth5")
smooth6 = pe.MapNode(fsl.Smooth(fwhm=fwhm),
            iterfield=['in_file'],name="smooth6")
groupsink = pe.Node(interface=nio.DataSink(parameterization=True),
            name="groupsink")
groupsink.base_directory = op.join(baseDir,'scratch/tmp_work/sinking/{analID}'.format(analID=analID))


outputspec = pe.Node(
                util.IdentityInterface(
            fields=['smoothed_file1', 'smoothed_file2', 'smoothed_files', 'firstItem']),
name='outputspec')
    #########################
    ###   Firstlvl Model  ###
    #########################


# connect first level workflow
firstlevel = pe.Workflow(name='firstlevel')
firstlevel.base_dir = workDir # set working directory
firstlevel.connect(smooth1,'smoothed_file',smooth2,'in_file')

# connect second level workflow
secondlevel = pe.Workflow(name='secondlevel')
secondlevel.base_dir = workDir # set working directory
secondlevel.connect(smooth3,'smoothed_file',smooth4,'in_file')

# connect third level workflow
thirdlevel = pe.Workflow(name='thirdlevel')
thirdlevel.base_dir = workDir # set working directory
thirdlevel.connect(smooth5,'smoothed_file',smooth6,'in_file')


# connect meta flow to subflows and 
metaflow = pe.Workflow(name='metaflow_fixError')
metaflow.base_dir = workDir # set working directory
metaflow.config = {
    "execution": {"crashdump_dir": op.abspath(op.join(workDir,'nipype/crashdumps'))}}

# preliminaries
metaflow.connect(infosource,'sub_no',selectSubs,'sub_no') 
metaflow.connect(infosource,'sub_no',createSubOutDir,'sub_no')
metaflow.connect(selectSubs,'func',firstlevel,'smooth1.in_file')
metaflow.connect(firstlevel,'smooth2.smoothed_file',secondlevel,'smooth3.in_file')
metaflow.connect(secondlevel,'smooth4.smoothed_file',thirdlevel,'smooth5.in_file')
metaflow.connect(thirdlevel,'smooth6.smoothed_file',selectSingleCope1,'aList')

#3rd lvl sinking
metaflow.connect(selectSingleCope1,'first_item',outputspec,'firstItem')
metaflow.connect(thirdlevel,'smooth6.smoothed_file',outputspec,'smoothed_files')
metaflow.connect(secondlevel,'smooth4.smoothed_file',outputspec,'smoothed_file2')
metaflow.connect(firstlevel,'smooth2.smoothed_file',outputspec,'smoothed_file1')


metaflow.connect(selectSingleCope1,'first_item',groupsink,'masks.@brainMaskMNI_native')
metaflow.connect(outputspec,'firstItem',groupsink,'stats')
metaflow.connect(outputspec,'smoothed_files',groupsink,'stats.cluster.@thr')
metaflow.connect(outputspec,'smoothed_file2',groupsink,'stats.cluster.@cluster')
metaflow.connect(outputspec,'smoothed_file1',groupsink,'stats.stats')


###########################
####    RUN WORKFLOW   ####
###########################
# make a graph
metaflow.write_graph(graph2use='colored', format='png',dotfilename=op.join(workDir,'graph_colored.dot'), simple_form=True)

#shell()
res = metaflow.run(plugin='MultiProc', plugin_args={'n_procs' : 15})
#res = metaflow.run(plugin='CondorDAGMan')
