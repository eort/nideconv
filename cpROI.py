#import nipype.algorithms.modelgen as model
import os,json,glob,sys
import os.path as op
import numpy as np
import nibabel as nib
#import nilearn.plotting
from IPython import embed as shell

#baseDir = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/foraging/scratch'
baseDir = '/home/data/foraging/scratch'
copeDir = 'sub-%02d/models/2ndlvl/FIR/FIR_cope-%d.gfeat/cope1.feat'
#exampleFuncDir = 'sub-%02d/models/1stlvl/sub-%02d-01_FIR.feat'
maskDir = 'group_level/Control-31/cope-17.gfeat/masks'
transformDir = 'sub-%02d/models/1stlvl/sub-%02d-01_preprocess.feat/reg'
outDir = 'sub-%02d/models/2ndlvl/FIR/masks'

sampleSize = 19
subs = range(1,18) +[19]+ [21]

# making masks
masks = glob.glob(op.join(baseDir,maskDir) + '/*ready*')
for sub in subs: 
	print("creating masks for subject %02d"%sub)
	workDir = op.join(baseDir,transformDir%(sub,sub))
	try:
		os.chdir(workDir)
	except:
		workDir = op.join(baseDir,'sub-%02d/models/1stlvl/sub-%02d-02_FIR.feat/reg'%(sub,sub))
		os.chdir(workDir)

	sta2hr_warp = 'standard2highres_warp.nii.gz'
	hr2func_mat = 'highres2example_func.mat'
	
	# make the inverse transform from standard to structural
	print("Computing the structural warp")
	#if not op.isfile(sta2hr_warp):
	#	os.system("invwarp -w highres2standard_warp -o %s -r highres"%sta2hr_warp)
	for mask in masks:
		funcMaskDir = op.join(baseDir,outDir%sub)
		if not op.exists(funcMaskDir): # submit dir
			os.makedirs(funcMaskDir)
		func_mask = op.join(funcMaskDir, op.basename(mask)[:-7]+'_func.nii.gz')
		if not op.isfile(op.join(funcMaskDir,func_mask)) or 1:
			ex_func = op.join(baseDir,copeDir,'example_func.nii.gz')%(sub,1)
			print("Applying warp for mask %s"%mask)
			#shell()
			#os.system("applywarp -i %s -r %s -o %s -w %s \
			#	--postmat=%s "%(mask,ex_func,func_mask,sta2hr_warp,hr2func_mat))
			#os.system("fslmaths %s -thr 0.01 -bin %s"%(func_mask,func_mask))
		os.system("cp %s %s"%(mask,func_mask))

