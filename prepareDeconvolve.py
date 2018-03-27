#import nipype.algorithms.modelgen as model
import os,json,glob,sys
import os.path as op
import numpy as np
from multiprocessing import Pool, cpu_count
import nibabel as nib
import IO as io
from IPython import embed as shell

def computePercentSignalChange(signal,avg_signal):
	"""
	Converts a time series in a %%-signal change series
	Divide by mean of series, multiply by 100, subtract 100
	Returns a 0 centered in percent times series
	"""
	new_signal = (np.divide(signal,avg_signal[:,:,:,np.newaxis],
		out=np.zeros_like(signal), where=avg_signal[:,:,:,np.newaxis]!=0)* 100)-100
	return new_signal

def fooFunc(sub):
	"""
	Function that allows parallelization of the script
	"""
	out = op.join(baseDir,outDir,'percentSignal')%(sub)
	if not op.exists(out):
		os.makedirs(out)
		print('Creating new folder %s'%(out))

	if cfg['runPercentSignalChange']:
		# loop over subjects and runs, %signal change, concat
		# create folders where necessary
		# first output folder for all the signal runs
		for run in range(1,runsPerSubject[sub]+1): 

			outfile = op.join(out,'sub-%02d-%02d_percentSignal.nii.gz'%(sub,run))

			# load niftis
			feat = 'sub-%02d-%02d_%s.feat'%(sub,run,ID)
			imgDir = op.join(baseDir, 'scratch',funcLoc,feat)%sub
			# Once the filtered signal
			funcImg = nib.load(op.join(imgDir,signal))
			# and once the mean signal per run
			meanImg = nib.load(op.join(imgDir,avg_signal))

			# extract data 
			funcData = funcImg.get_data()
			meanData = meanImg.get_data()
			# compute percentage signal change
			funcData_percent = computePercentSignalChange(funcData,meanData)
			# write new time signal to file
			outImg = nib.Nifti1Image(funcData_percent, funcImg.affine, funcImg.header)			
			nib.save(outImg, outfile)
			print('Signal %%-change conversion finished for run %d of participant %d'%(run,sub))

	if cfg['runConcatRuns']:

		print('start concatenating runs for participant %d'%(sub))
		# find all runs for a subject
		subRuns = glob.glob(out + '/sub-%02d-*_percentSignal.nii.gz'%sub)
		if cfg['dropEmptyRuns']: # if you want to remove runs with 0 or barely any events
			runs = emptyRuns['%02d'%sub]
			if len(runs)>0:
				outlier_runs = {int(b[0]) for b in runs}
			else:
			   outlier_runs = []
			# exclude runs that don't have all events
			for R in outlier_runs:
				subRuns = [subrun for subrun in subRuns if 'sub-%02d-%02d'%(sub,R) not in subrun] 
		# sort the runs
		subRuns.sort()
		outMerge = op.join(out,'sub-%02d-exEmpty_percentSignal.nii.gz'%sub)
		mergeParameters = [outMerge] + subRuns 
		os.system("fslmerge -t {}".format(' '.join(mergeParameters)))

	if cfg['makeMasks']:
		"Create masks for subject %02d"%sub
		masks = glob.glob(op.join(baseDir,maskDir) + '/all*ready*')
		originDir = os.getcwd()
		if not os.path.isfile(sta2hr_warp%(sub,sub)):
			print("Computing the structural warp")		
			formatters = [highres2standard_warp%(sub,sub),sta2hr_warp%(sub,sub),highres%(sub,sub)]	
			os.system("invwarp -w %s -o %s -r %s"%tuple(formatters))
		for mask in masks:
			funcMaskDir = op.join(baseDir,outDir%sub)
			if not op.exists(funcMaskDir): # submit dir
				os.makedirs(funcMaskDir)

			func_mask = op.join(funcMaskDir, op.basename(mask).split(os.extsep)[0]+'_func.nii.gz')			
			ex_func = op.join(funcMaskDir,'percentSignal','sub-%02d_percentSignal.nii.gz')%sub
			print("Applying warp for mask %s"%mask)
			os.system("applywarp -i %s -r %s -o %s -w %s \
				--postmat=%s "%(mask,ex_func,func_mask,sta2hr_warp%(sub,sub),hr2func_mat%(sub,sub)))
			if binarize:
				os.system("fslmaths %s -thr 0.01 -bin %s"%(func_mask,func_mask))

if len(sys.argv)<2:
    jsonfile = '/home/data/foraging/configFiles/deconvolve_prepare_cfg.json'
else:
    jsonfile = sys.argv[1]
try:
    with open(jsonfile) as data_file:    
        cfg = json.load(data_file)
    data_file.close()
except IOError as e:
    print "The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line."
    sys.exit(-1)

baseDir = cfg['baseDir']
funcLoc = cfg['funcLoc']
outDir = cfg['outDir']
infoDir = op.join(baseDir,cfg['infoDir'])
maskDir = op.join(baseDir,cfg['maskDir'])
transformDir = op.join(baseDir,cfg['transformDir'])
sta2hr_warp = op.join(transformDir,cfg['sta2hr_warp'])
hr2func_mat = op.join(transformDir,cfg['hr2func_mat'])
highres2standard_warp = op.join(transformDir,'highres2standard_warp')
highres = op.join(transformDir,'highres')
ID = cfg['analID']
SUBS = cfg['SUBS']
signal = cfg['signal']
avg_signal = cfg['avg_signal']
binarize = cfg['binarize']

# How many runs per subject are there
runsPerSubjectFile = op.join(baseDir,'generalInfo',cfg['runsPerSubject']) # filename
runsPerSubject = dict() # init container
with open(runsPerSubjectFile, 'r') as infile:
	for x,l in enumerate(infile):
		runs = io.str2list(l)
		runsPerSubject[runs[0]] = runs[1] # add subject:run dict   

# What are the bad runs
emptyEVfile = op.join(infoDir,cfg['emptyRuns'])
emptyRuns = {'%02d'%i:[] for i in range(1,25)}
with open(emptyEVfile, 'r') as infile:
	for x,l in enumerate(infile):
		llist = l.split()
		emptyRuns[llist[0]].append(llist[1:])


if cfg["parallel"]: 
	pool = Pool(cpu_count()-10)
	pool.map(fooFunc,SUBS)
else:
	for sub in SUBS:
		fooFunc(sub)
#shell()
