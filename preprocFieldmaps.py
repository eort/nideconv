"""
Processes fieldmaps so that they can be used for B0 field distortion correction
During the process a couple of temporary images are being created and deleted
in the end. 
"""
import nibabel as nib
import os 
from IPython import embed as shell
import glob
import sys
import json

# load json sidecar
try:
    jsonfile = sys.argv[1]
except IndexError:
    print('You need to specify configuration file for this analysis')
    sys.exit()
try:
    with open(jsonfile) as data_file:    
        settings = json.load(data_file)
except IOError as e:
    print("The provided file does not exist. Either put a default .json file "\
    "in the directory of this script, or provide a valid file in the command line.")
    sys.exit()

#load parameters
baseDir = settings['baseDir'] # root directory on server
skip = settings['skip'] # which subjects have already been converted
EES = settings["EES"]
wfs = settings["wfs"]# Water-fat-shift

fmaps1 = glob.glob(baseDir + '/sub-*/fmap/*fmap1.nii.gz')

for fmapfile in fmaps1:
    if any(["sub-{:02d}".format(sk) in fmapfile for sk in skip]):
        print("Skip nifti file {}".format(fmapfile))
        continue 

    print("Process {}".format(fmapfile))
    fmap2file = fmapfile.replace("fmap1","fmap2")

    # load field maps
    fmap1 = nib.load(fmapfile)
    fmap2 = nib.load(fmap2file)

    # find out which is magnitude and which is phase
    if int(fmap1.dataobj.inter) == -217:
        fmap_mag = fmap2
        fmap_phs = fmap1
    elif int(fmap2.dataobj.inter) == -217:
        fmap_mag = fmap1
        fmap_phs = fmap2

    # save images (phase only temp because it needs to be corrected)
    nib.save(fmap_mag, fmapfile.replace("fmap1","fmap_mag"))
    nib.save(fmap_phs, fmapfile.replace("fmap1","fmap_phs_temp"))
    # use fslmaths to correct phase
    infile = fmapfile.replace("fmap1","fmap_phs_temp")
    outfile = fmapfile.replace("fmap1","fmap_phs")
    os.system("fslmaths {} -div {} -mul 6.2831 {} -odt float".format(infile,wfs,outfile))

    # delete later
    temp_phase1 = infile
    temp_phase2 = outfile

    # regularize phase
    infile = outfile
    outfile = fmapfile.replace("fmap1","fieldmap")
    os.system("fugue --loadfmap={} -m --savefmap={}".format(infile,outfile))

    # extraxt brain from magnitude and then erode it(remove noisy voxels at edge)
    infile = fmapfile.replace("fmap1","fmap_mag")
    outfile = fmapfile.replace("fmap1","fmap_mag_brain_noEro")
    os.system("bet {} {}".format(infile,outfile))
    temp_mag = outfile
    temp_mag2 = infile
    infile = outfile
    outfile = fmapfile.replace("fmap1","magnitude")
    os.system("fslmaths {} -ero {}".format(infile,outfile))

    # remove unnecessary files
    os.system("rm -r {} {} {} {}".format(temp_phase1,temp_phase2,temp_mag,temp_mag2))