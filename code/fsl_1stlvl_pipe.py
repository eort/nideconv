from __future__ import division, print_function, absolute_import

# Based on Github PoldrackLab script: https://github.com/poldracklab/CNP_task_analysis/blob/master/CNP_analysis.py
# Also based on Github Knapen lab PRF : https://github.com/tknapen/PRF_MB_7T/tree/master/nPRF

# Changed from previous version (_old2) : not using _brainmask.nii outputs from fmriprep
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
from nipype.pipeline.engine import Workflow, Node, MapNode
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces import afni
from nipype.interfaces.base import Bunch
from bids.grabbids import BIDSLayout
import nipype.algorithms.modelgen as model  # model generation

#from preproc_functions import savgol_filter, average_signal, percent_signal_change, natural_sort
import json
import nibabel as nib
import pandas as pd
import numpy as np
import sys,os
import os.path as op
from builtins import str
from builtins import range
from IPython import embed as shell

# load configuration file
try:
	jsonfile = sys.argv[1]
except IndexError as e:
	jsonfile = '/home/data/foraging/configFiles/nipype/GLM_1stlvl_nipype.json'
try:	
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
except IOError as e:
        print("The provided file does not exist. Either put a default .json file \
        in the directory of this script, or provide a valid file in the command line.")
        sys.exit(-1)


# create variables
baseDir = cfg['baseDir']
subs = cfg['subjects']
dataDir = op.join(baseDir, 'scratch', cfg['fmriprepDir'])
fmriprepDir = op.join(baseDir, 'scratch', cfg['fmriprepDir'])
tmpworkDir = op.join(baseDir, 'scratch', cfg['tmpworkDir'])
eventDir = op.join(baseDir, cfg['eventDir'])
confoundDir = op.join(fmriprepDir, cfg['confoundDir'])

shell()
datasource = nio.DataGrabber(infields=['subject_id'], outfields=['func', 'struct'])

# Condition names
condition_names = ['proSwitch', 'reSwitch','proRep','reRep','cue','error']
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


for SUB in subs: 
    pass

modelfit = pe.Workflow(name='modelfit')
modelfit.basedir = baseDir
smooth = pe.Node(Smooth(fwhm=fwhm_size),
            output_type = 'NIFTI_GZ',
            name="smooth")
level1 = pe.Node(SpecifyModel(
            subject_info = info,
            input_units='secs',
            time_repetition=cfg['TR'],
            high_pass_filter_cutoff=cfg['highpass_filter'] # set to -1 for no filtering as already have done SG filtering
        ), name='level1')

level1design = pe.Node(Level1Design(
            interscan_interval=analysis_info['TR'],
            bases={'dgamma': {'derivs': True}},
            model_serial_correlations=True,
            contrasts=contrasts), 
            name='l1design')
l1featmodel = Node(FEATModel(), name='l1model')

modelgen = pe.MapNode(
    interface=fsl.FEATModel(),
    name='modelgen',
    iterfield=['fsf_file', 'ev_files'])
modelestimate = pe.MapNode(
    interface=fsl.FILMGLS(smooth_autocorr=True, mask_size=5, threshold=1000),
    name='modelestimate',
    iterfield=['design_file', 'in_file'])