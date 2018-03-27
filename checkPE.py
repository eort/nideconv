#import nipype.algorithms.modelgen as model
import os,json,glob,sys
import os.path as op
import numpy as np
import nibabel as nib
#import nilearn.plotting
from IPython import embed as shell
import matplotlib.pylab as pl

baseDir = '/run/user/1000/gvfs/sftp:host=medusa.ovgu.de,user=ort/home/data/foraging/scratch'
#baseDir = '/home/data/foraging/scratch'


subDir = 'models/1stlvl/sub-07-05_FIR.feat'
proS = [nib.load(op.join(baseDir,subDir,'stats/pe%d.nii.gz'%idx)) for idx in range(1,11)]
proSdata = [img.get_data() for img in proS]

reS = [nib.load(op.join(baseDir,subDir,'stats/pe%d.nii.gz'%idx)) for idx in range(11,21)]
reSdata = [img.get_data() for img in reS]

proR = [nib.load(op.join(baseDir,subDir,'stats/pe%d.nii.gz'%idx)) for idx in range(21,31)]
proRdata = [img.get_data() for img in proR]

reR = [nib.load(op.join(baseDir,subDir,'stats/pe%d.nii.gz'%idx)) for idx in range(31,41)]
reRdata = [img.get_data() for img in reR]

shell()

plotar1 = [proSdata[i][36:42,42:48,23:29].mean() for i in range(len(proSdata))]
plotar2 = [reSdata[i][36:42,42:48,23:29].mean() for i in range(len(proSdata))]
plotar3 = [proRdata[i][36:42,42:48,23:29].mean() for i in range(len(proSdata))]
plotar4 = [reRdata[i][36:42,42:48,23:29].mean() for i in range(len(proSdata))]
pl.plot(np.arange(-2,18,2),plotar1,'r--')
pl.plot(np.arange(-2,18,2),plotar2,'y--')
pl.plot(np.arange(-2,18,2),plotar3,'b--')
pl.plot(np.arange(-2,18,2),plotar4,'g--')

plotar1 = [proSdata[i][39,45,26] for i in range(len(proSdata))]
plotar2 = [reSdata[i][39,45,26] for i in range(len(proSdata))]
plotar3 = [proRdata[i][39,45,26] for i in range(len(proSdata))]
plotar4 = [reRdata[i][39,45,26] for i in range(len(proSdata))]
pl.plot(np.arange(-2,18,2),plotar1,'r--')
pl.plot(np.arange(-2,18,2),plotar2,'y--')
pl.plot(np.arange(-2,18,2),plotar3,'b--')
pl.plot(np.arange(-2,18,2),plotar4,'g--')

plotar1 = [proSdata[i][39,14,8] for i in range(len(proSdata))]
plotar2 = [reSdata[i][39,14,8] for i in range(len(proSdata))]
plotar3 = [proRdata[i][39,14,8] for i in range(len(proSdata))]
plotar4 = [reRdata[i][39,14,8] for i in range(len(proSdata))]
pl.plot(np.arange(-2,18,2),plotar1,'r--')
pl.plot(np.arange(-2,18,2),plotar2,'y--')
pl.plot(np.arange(-2,18,2),plotar3,'b--')
pl.plot(np.arange(-2,18,2),plotar4,'g--')


plotar1 = [proSdata[i][43:48,53:57,20:24].mean() for i in range(len(proSdata))]
plotar2 = [reSdata[i][43:48,53:57,20:24].mean() for i in range(len(proSdata))]
plotar3 = [proRdata[i][43:48,53:57,20:24].mean() for i in range(len(proSdata))]
plotar4 = [reRdata[i][43:48,53:57,20:24].mean() for i in range(len(proSdata))]
pl.plot(np.arange(-2,18,2),plotar1,'r--')
pl.plot(np.arange(-2,18,2),plotar2,'y--')
pl.plot(np.arange(-2,18,2),plotar3,'b--')
pl.plot(np.arange(-2,18,2),plotar4,'g--')

nilearn.plotting.plot_glass_brain(imgs[0],display_mode='lyrz', colorbar=True, plot_abs=False, threshold=2.3)

