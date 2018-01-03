#import nipype.algorithms.modelgen as model
import os,json,glob,sys
import os.path as op
import numpy as np
import subprocess
import nibabel as nib
#import nilearn.plotting
from IPython import embed as shell
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as pl

baseDir = '/home/data/foraging/scratch'
copeDir = 'sub-%02d/models/2ndlvl/FIR/FIR_cope-%d.gfeat/cope1.feat'
exampleFuncDir = 'sub-%02d/models/1stlvl/sub-%02d-01_FIR.feat'
maskDir = 'group_level/Control-31/cope-17.gfeat/masks'
transformDir = 'sub-%02d/models/1stlvl/sub-%02d-01_FIR.feat/reg'
outDir = 'sub-%02d/models/2ndlvl/FIR/masks'

sampleSize = 19
subs = range(1,18) +[19]+ [21]
noMasks = 7

EVs = [['proS',1],['reS',3],['proR',5],['reR',7]]
timecourse = np.zeros((noMasks,len(EVs),len(subs),10))
for subI,sub in enumerate(subs):
	print("Extracting time series for subject %02d"%sub)
	for evI,ev in enumerate(EVs): 
		print("Extracting time series for condition %s"%ev[0])
		funcMaskDir = op.join(baseDir,outDir%sub)
		funcMasks = glob.glob(funcMaskDir + '/*func*')
		
		copes = glob.glob(op.join(baseDir,copeDir%(sub,ev[1]))+ '/stats/cope*.gz')
		if len(copes) == 0:
			continue
		copes.sort(); copes = [copes[0]]+ copes[2:] + [copes[1]]
		for mI,mask in enumerate(funcMasks):
			pes = [float(subprocess.check_output(["fslmeants", "-i", "%s"%cope, "-m", "%s"%mask]).split()[0]) for cope in copes]
			timecourse[mI,evI,subI,:] = pes

np.save("ts_complete.npy",timecourse)
shell()
group_average = timecourse.mean(axis = 2)

# plotting

f,axes = pl.subplots(len(subs),noMasks,sharex=True)
f.set_figwidth(20)
f.set_figheight(30)
xaxis = np.arange(-2,18,2)

col = ['r--','g--','b--','y--']
cond = ['proS','reS','proR','reR']
for sub in range(len(subs)):
	#for aI,ax in enumerate(axes):
	for aI in range(axes.shape[1]):
		plots = []
		ax = axes[sub,aI]
		for eI in range(timecourse.shape[1]):
			plotdata = timecourse[aI,eI,sub,:]
			plots.append(ax.plot(xaxis,plotdata,col[eI])[0])
			ax.set_title('%s'%op.basename(funcMasks[aI]))
			ax.axvline(0)
			ax.axvline(6)

pl.setp(axes,xticks = xaxis,xticklabels = xaxis)
pl.figlegend(tuple(plots),cond,'upper right')
f.tight_layout()
f.savefig('HRF_individual.pdf')


# individual difference plots
f,axes = pl.subplots(len(subs),noMasks,sharex=True)
f.set_figwidth(20)
f.set_figheight(30)
xaxis = np.arange(-2,18,2)

col = ['r--','b--']
cond = ['pro','re']
for sub in range(len(subs)):
	#for aI,ax in enumerate(axes):
	for aI in range(axes.shape[1]):
		plots = []
		ax = axes[sub,aI]
		for eI in range(2):
			plotdata_swi = timecourse[aI,eI,sub,:]
			plotdata_rep = timecourse[aI,eI+2,sub,:]
			plotdata = plotdata_swi - plotdata_rep
			plots.append(ax.plot(xaxis,plotdata,col[eI])[0])
			ax.set_title('%s'%op.basename(funcMasks[aI]))
			ax.axvline(0)
			ax.axvline(6)

pl.setp(axes,xticks = xaxis,xticklabels = xaxis)
pl.figlegend(tuple(plots),cond,'upper right')
f.tight_layout()
f.savefig('HRF_individual_diffWav.pdf')
# group

f,axes = pl.subplots(1,noMasks,sharex=True)
f.set_figwidth(24)
f.set_figheight(4)
xaxis = np.arange(-2,18,2)

col = ['r--','y--','b--','g--']
cond = ['reR','reS','proS','proR']
#for aI,ax in enumerate(axes):
for aI,ax in enumerate(axes):
	plots = []
	for eI in range(group_average.shape[1]):
		plotdata = group_average[aI,eI,:]
		plots.append(ax.plot(xaxis,plotdata,col[eI])[0])
		ax.set_title('%s'%op.basename(funcMasks[aI]))
		ax.axvline(0)
		ax.axvline(6)

pl.setp(axes,xticks = xaxis,xticklabels = xaxis)
pl.figlegend(tuple(plots),cond,'upper right')
f.tight_layout()
f.savefig('HRF_group.pdf')

# group diffwave
f,axes = pl.subplots(1,noMasks,sharex=True)
f.set_figwidth(24)
f.set_figheight(4)
xaxis = np.arange(-2,18,2)

col = ['r--','b--']
cond = ['pro','re']
#for aI,ax in enumerate(axes):
for aI,ax in enumerate(axes):
	plots = []
	for eI in range(2):
		plotdata_swi = timecourse[aI,eI,sub,:]
		plotdata_rep = timecourse[aI,eI+2,sub,:]
		plotdata = plotdata_swi - plotdata_rep
		plots.append(ax.plot(xaxis,plotdata,col[eI])[0])
		ax.set_title('%s'%op.basename(funcMasks[aI]))
		ax.axvline(0)
		ax.axvline(6)

pl.setp(axes,xticks = xaxis,xticklabels = xaxis)
pl.figlegend(tuple(plots),cond,'upper right')
f.tight_layout()
f.savefig('HRF_group_diffWav.pdf')
