#!/usr/bin/python

import os
import sys
import os.path as op
import glob
from IPython import embed as shell
import subprocess


	
def run(parentDir):
    # find all the bold files
    boldfiles = glob.glob('%s/sub-[0-2][0-9]/func/sub-[0-2][0-9]_task-choice_run-[0-1][0-9]_bold.nii.gz'%(parentDir))
    boldfiles.sort()
    # make an output file for visual inspection and a file with very bad subjects
    outhtml = op.join(parentDir,'generalInfo/QA_bold_motion.html')
    out_bad_pp = op.join(parentDir,'generalInfo/exclSubsMotion.html')
    # reset these two files 
    os.system("rm %s"%outhtml )
    os.system("rm %s"%out_bad_pp )

    # loop over bolds
    for bold in boldfiles:
        print('Analzying %s'%bold)
        strippedBold = bold[:-7] # remove file path
        run_no = bold[-14:-12] # extract run number (for plot disambiguation)
        motionDir = '%s/motion_assess'%op.dirname(bold) # folder to QA info
        if not op.exists(motionDir): # create folder if it doesnt exit yet
            print('Creating new folder %s'%motionDir)
            os.system("mkdir %s"%motionDir)
        
        # find motion outliers using framewise deplacement and threshol of 0.9
        # also creates a confound.txt that can be used for the GLM 
        os.system('fsl5.0-fsl_motion_outliers -i %s -o %s/confound.txt --fd --thresh=0.9 -p %s/fd_plot_run-%s -v > %s/outlier_output.txt'%(strippedBold,motionDir,motionDir,run_no,motionDir))
        # save output information in a global QA file
        os.system("cat %s/outlier_output.txt >> %s"%(motionDir, outhtml))
        os.system("echo '<p>=============<p>FD plot %s <br><IMG BORDER=0 SRC=%s/fd_plot_run-%s.png WIDTH=100%s></BODY></HTML>' >> %s"%(motionDir, motionDir,run_no,'%', outhtml))
        # make an empty confound.txt if there is no motion artefact
        if os.path.isfile("%s/confound.txt"%motionDir)==False:
          os.system("touch %s/confound.txt"%motionDir)    
        # mark runs that have particularly many motionartefacts
        output = subprocess.check_output("grep -o 1 %s/confound.txt | wc -l"%motionDir, shell=True)
        num_scrub = [int(s) for s in output.split() if s.isdigit()]
        if num_scrub[0]>30:
            with open(out_bad_pp, "a") as myfile:
              myfile.write("%s\n"%motionDir)      


if __name__ == '__main__':
    try:
        parentDir = op.abspath(sys.argv[1])
    except IndexError as e:
        parentDir = '/home/data/exppsy/ora_Amsterdam'
        print 'Use default path %s'%parentDir
    run(parentDir)
