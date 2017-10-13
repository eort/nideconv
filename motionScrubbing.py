#!/usr/bin/python

import os
import sys
import os.path as op
import glob
from IPython import embed as shell
import subprocess


def run(parentDir, subNo):
    """
    Makes a regression file for volumes in which participants moved a lot. 
    These volumes will not be included in analysis (Method described in: 10.1002/hbm.22307)
    Make also some for files to facilitate QA
    """
    # find all the bold files
    boldfiles = glob.glob('%s/sub-%02d/func/sub-%02d_task-choice_run-[0-1][0-9]_bold.nii.gz'%(parentDir,subNo,subNo))
    boldfiles.sort()
    # make an output file for visual inspection and a file with very bad subjects
    
    out_bad_pp = op.join(parentDir,'QA/exclSubsMotion.html')
    # reset these two files 
    #os.system("rm %s"%outhtml )
    #os.system("rm %s"%out_bad_pp )

    # loop over bolds
    for bold in boldfiles:
        #print('Analzying %s'%bold)
        strippedBold = bold[:-7] # remove file path
        run_no = bold[-14:-12] # extract run number (for plot disambiguation)
        motionDir = '%s/motion_assess'%op.dirname(bold) # folder to QA info
        outhtml = op.join(parentDir,'QA/QA_bold_motion_sub-%02d.html'%subNo)
        if not op.exists(motionDir): # create folder if it doesnt exit yet
            print('Creating new folder %s'%motionDir)
            os.system("mkdir %s"%motionDir)
        
        # find motion outliers using framewise deplacement and threshol of 0.9
        # also creates a confound.txt that can be used for the GLM 
        os.system('fsl5.0-fsl_motion_outliers -i %s -o %s/confound_run-%s.txt --fd --thresh=0.9 -p %s/fd_plot_run-%s -v > %s/outlier_output_run-%s.txt'%(strippedBold,motionDir,run_no,motionDir,run_no,motionDir,run_no))
        # save output information in a global QA file
        os.system("cat %s/outlier_output_run-%s.txt >> %s"%(motionDir, run_no,outhtml))
        os.system("echo '<p>=============<p>FD plot %s <br><IMG BORDER=0 SRC=%s/fd_plot_run-%s.png WIDTH=100%s></BODY></HTML>' >> %s"%(motionDir, motionDir,run_no,'%', outhtml))
        # make an empty confound.txt if there is no motion artefact
        if os.path.isfile("%s/confound_run-%s.txt"%(motionDir,run_no))==False:
          os.system("touch %s/confound_run-%s.txt"%(motionDir,run_no))    
        # mark runs that have particularly many motionartefacts
        output = subprocess.check_output("grep -o 1 %s/confound_run-%s.txt | wc -l"%(motionDir,run_no), shell=True)
        num_scrub = [int(s) for s in output.split() if s.isdigit()]
        if num_scrub[0]>50:
            with open(out_bad_pp, "a") as myfile:
              myfile.write("%s\n"%bold)      


if __name__ == '__main__':
    try:
        parentDir = op.abspath(sys.argv[1])
    except IndexError as e:
        parentDir = '/home/data/exppsy/ora_Amsterdam'
        print('Use default path %s'%parentDir)
    try:
        subNo = int(sys.argv[2])
    except IndexError as e:
        print('need to provide a valid subject number')
        sys.exit()     
    run(parentDir,subNo)
