#import nipype.algorithms.modelgen as model
import os,json,glob,sys
import os.path as op
import numpy as np
import nibabel as nib
#import nilearn.plotting
from IPython import embed as shell
import matplotlib.pylab as pl

baseDir = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/foraging/scratch'
copeDir = 'sub-%02d/models/2ndlvl/FIR/FIR_cope-%d.gfeat/cope1.feat'
exampleFuncDir = 'sub-%02d/models/1stlvl/sub-%02d-01_FIR.feat'
maskDir = 'group_level/Control-31/cope-17.gfeat/masks'
transformDir = 'sub-%02d/models/1stlvl/sub-%02d-01_FIR.feat/reg'
outDir = 'sub-%02d/models/2ndlvl/FIR/masks'

sampleSize = 19
subs = range(1,18) +[19]+ [21]
create_masks = 1



EVs = dict(proS=1,reS=3,proR=5,reR=7)
timecourse = np.zeros((len(EVs.keys()),len(masks),len(subs),10))
for evI,ev in enumerate(EVs): 
	for subI,sub in enumerate(subs):
		funcMaskDir = op.join(baseDir,outDir%sub)
		funcMasks = glob.glob(funcMaskDir + '/*func*')
		for mask in funcMasks:

			workDir = glob.glob(op.join(baseDir,copeDir%(subNo,EVs[ev]))+ '/stats/cope*.gz')
			shell()
			#files =glob.glob(baseDir+'/sub-*'+'/models/2ndlvl/FIR/FIR_cope-%d.gfeat/cope1.feat/stats/cope*.gz'%EVs[ev])
			#files.sort()
		
		reR= [nib.load(f) for f in files if 'sub-%02d'%subNo in f]
		try:
			reR =  [reR[0]] + reR[2:] + [reR[1]]
		except:
			continue
		if len(reR) != 0:
			timecourse[evI,subI,:]= [img.get_data().mean() for img in reR]   


shell()
