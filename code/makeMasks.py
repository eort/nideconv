import os
import os.path as op
import glob
from IPython import embed as shell
import subprocess


def prob2mask(infile, outfile = None, threshold = 0):
    """
    Some fslmath magic on an image. Can threshold an image at a certain
    level and/or binarize it in order to make a mask from it
    If outfile is left None, the suffix '_mask' is added to the image
    """
    if outfile == None:
        baseList = op.basename(infile).split('.')
        baseList[0] = baseList[0]+'_mask'
        dirName = op.dirname(infile)
        outfile  = op.join(dirName,'.'.join(baseList))

    os.system("fslmaths {infile} -thr {thr} -bin {outfile} -odt short".
        format(infile=infile, thr = threshold, outfile = outfile))
    os.system("mv {f} {out}".format(f=outfile,out = op.join(dirName,'../bin')))

def extractClusters(infile, outdir = None,):
    """
    Given a statistical image with several binarized clusters in them, 
    this function creates new images with each individual cluster in that file
    """
    
    if outdir == None:
        in_d,in_f = op.split(infile)
        outfile = op.join(in_d,'cluster_%d.nii.gz')
    else:
        outfile = op.join(outdir,'cluster_%d.nii.gz')
    
    py2output = subprocess.check_output(['fslstats',infile,'-R'])
    noClusters = int(float(py2output.split(' ')[1]))
    for idx in range(1,noClusters+1):
        out = outfile%idx
        os.system('fslmaths -dt int {f} -thr {idx} -uthr {idx} -bin {out}'.format(
                    f=infile,out=out,idx=idx))
                    
def MNI2FMRIPREP(infile,reffile=None,outfile=None):
    if reffile == None:
        reffile = '/home/data/foraging/scratch/group_level/masks/brain/MNIstandard_1mm_fmriprepNative.nii.gz'
    if outfile == None:
        in_d,in_f = op.split(infile)
        baseList =  in_f.split('.')
        outfile = op.join(in_d,'.'.join([baseList[0]+'_fmriprepNat']+baseList[1:]))        

    # run the transform
    os.system('flirt -in {f} -ref {ref} -out {out} -applyxfm -interp trilinear \
        -nosearch -usesqform'.format(f=infile,ref=reffile,out=outfile))    # binarize the results (threhsold 0.5 corresponds to orignal size (~))
    os.system('fslmaths {f} -thr 0.5 -bin {f}'.format(f=outfile))
    # move to right folder
    os.system("mv {f} {out}".format(f=outfile,out = op.join(in_d,'../../fmriprepNative/bin')))

def mergeMasks(mask1, mask2, outmask):
    '''
    takes the intersection of two masks
    '''
    #shell()
    # first add the masks
    errorcode = os.system("fslmaths {mask1} -add {mask2} {out}".format(mask1=mask1,\
                mask2 =mask2, out=outmask))
    print(errorcode)
    # next threshold it (to get only the intersection)
    if errorcode == 0:
        os.system("fslmaths {infile} -thr 1.1 -bin {outfile}".format(\
            infile=outmask, outfile = outmask))

def filterMasks(infile, thr=1):
    '''
    Filters out (deletes) images whose max value is too low
    (filter out empty masks)
    '''
    py2output = subprocess.check_output(['fslstats',infile,'-R'])
    maxVal = int(float(py2output.split(' ')[1]))
    if maxVal < thr:
        print('Remove following mask:\t %s'%infile)
        os.system('rm -r {infile}'.format(infile=infile))

# remove empty masks
fileDir= '/home/data/foraging/scratch/group_level/masks/func/fmriprepNative/switchROI/ROI/'
files = glob.glob(fileDir + "*")
for f in files: 
    filterMasks(f)

"""
# merge significant cluster with anatomical masks
roidir = '/home/data/foraging/scratch/group_level/masks/anat/fmriprepNative/bin'
roimasks = glob.glob(roidir + "/*nii.gz")
clusterdir = '/home/data/foraging/scratch/group_level/masks/func/fmriprepNative/switchROI/clustercorrect'
clustermasks = glob.glob(clusterdir + "/*nii.gz")
clustermasks.sort()
clustermasks = [clustermasks[5]] + clustermasks[7:]


clustermapper = ['CEREBELLUM','NEUBERT','JUELICH']
clusterindex = [5,7,8]

for cluster,roicode,ci in zip(clustermasks,clustermapper,clusterindex):
    for roi in roimasks:
        if roicode in roi:
            suffix_temp = op.basename(roi).split('.')
            suffix = '.'.join([suffix_temp[0] +'_cluster%d'%ci] + suffix_temp[1:])
            out = '/home/data/foraging/scratch/group_level/masks/func/fmriprepNative/switchROI/ROI/%s'%suffix
            mergeMasks(cluster,roi,out)  


# binarize and threshold probabilistical anatomical maps
basedir = '/home/data/foraging/scratch/group_level/masks/anat/MNI/prob'
rawmasks = glob.glob(basedir + "/*nii.gz")

for mask in rawmasks:
    print("Converting {}".format(mask))
    if 'JUELICH' in mask:
        threshold = 30
    else:
        threshold = 50

    prob2mask(mask,threshold = threshold)


# convert MNI spaced mask to Fmriprep native mask
basedir = '/home/data/foraging/scratch/group_level/masks/anat/MNI/bin'
infiles = glob.glob(basedir + "/*mask.nii.gz")
for infile in infiles:
    print('Converting {}'.format(infile))
    MNI2FMRIPREP(infile)
"""


#infile = '/home/data/foraging/scratch/group_level/masks/func/fmriprepNative/switchROI/clustercorrect/allClustersCC.nii.gz'
#extractClusters(infile)

"""
switchROI_clusterMapper = dict(
                            cluster1='C1_BA23ab_pCinG_BL',
                            cluster2='C2_BA17_IntCalcCx_BL',
                            cluster3='C3_antINS_L',
                            cluster4='C4_tempOccITG_R',
                            cluster5='C5_Cereb_R',
                            cluster6='C6_LOC_ITG_L',
                            cluster7='C7_PFC_BL',
                            cluster8='C8_PPC_BL')
"""




"""
def mergeMasks(mask1, mask2, outmask):
    '''
    takes the intersection of two masks
    '''

    # first add the masks
    errorcode = os.system("fslmaths {mask1} -add {mask2} {out}".format(mask1=mask1,\
                mask2 =mask2, out=outmask))
    print(errorcode)
    # next threshold it (to get only the intersection)
    if errorcode == 0:
        os.system("fslmaths {infile} -thr 1.1 -bin {outfile}".format(\
            infile=outmask, outfile = outmask))

def subtractMasks(mask1, mask2, outmask):
    '''
    Subtract two masks from each other
    '''
"""