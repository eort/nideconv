import os
import os.path as op
import sys
import glob
from IPython import embed as shell

def fixOrientation(inputfile,outputfile):
	"""
	Reorients nifti files into standard orientation, by using fslreorient2std
	First input is inputfilename
	Second input is outputfilename
	"""
	os.system("fslreorient2std %s %s"%(inputfile,outputfile))

def fixOriWrapper(basedir,types,re_id='*',overwrite=True):
	"""
	Reorients nifti files into standard orientation, by using fslreorient2std
	basedir: root directory of project
	type: array type with dir names of nifti types to be reoriented
	re_id: regular expression to identify special niftis
	Overwrite: Will inputfile be overwritten, or a new copy created?

	Example: fmriPyTools.fixOriWrapper(os.path.abspath('..'),['anat'],'*T1w.',overwrite=False)
	"""

	for d in types:
		files = glob.glob('%s/sub-[0-2][0-9]/%s/%snii.gz'%(basedir,d,re_id))
		for f in files:
			if not overwrite:
				outputfile = f[:-7] + '_swapped.nii.gz'
			else: outputfile  = f
			fixOrientation(f,outputfile)

def extractBrain(inputfile,outputfile,flags = '-R -m'):
	"""
	Reorients nifti files into standard orientation, by using fslreorient2std
	First input is inputfilename
	Second input is outputfilename
	Third are options for the brain extraction, default: create mask, Robust center estimation
	"""
	os.system("bet %s %s %s"%(inputfile,outputfile,flags))


def extractBrainWrapper(basedir,types,re_id='*',overwrite=False, flags = '-R -m'):
	"""
	Reorients nifti files into standard orientation, by using fslreorient2std
	basedir: root directory of project
	type: array type with dir names of nifti types to be reoriented
	re_id: regular expression to identify special niftis
	Overwrite: Will inputfile be overwritten, or a new copy created?
	flags: which optios should be used for brain extraction

	Example: fmriPyTools.extractBrainWrapper(os.path.abspath('..'),['anat'],'*_swapped.')
	"""
	for d in types:
		files = glob.glob('%s/sub-[0-2][0-9]/%s/%snii.gz'%(basedir,d,re_id))
		for f in files:
			print 'Extracting brain of %s'%f
			if not overwrite:
				outputfile = f[:-7] + '_brain.nii.gz'
			else: outputfile  = f
			extractBrain(f,outputfile,flags=flags)
