#!/usr/bin/python

import os
import sys
import os.path as op
import glob
from IPython import embed as shell
import subprocess

try:
	parentDir = sys.argv[1]
except IndexError as e:
    parentDir = '/home/data/exppsy/ora_Amsterdam'
    print 'Use default path %s'%parentDir
	

boldfiles = glob.glob('%s/sub-[0-2][0-9]/func/sub-[0-2][0-9]_task-choice_run-[0-1][0-9]_bold.nii.gz'%(parentDir))
boldfiles.sort()

outhtml = op.join(parentDir,'generalInfo/QA_bold_motion.html')
out_bad_pp = op.join(parentDir,'generalInfo/exclSubsMotion.html')

os.system("rm %s"%outhtml )
os.system("rm %s"%out_bad_pp )


for bold in boldfiles:
    print('Analzying %s'%bold)
    strippedBold = bold[:-7] # remove file path
    curDir = op.dirname(bold)
    motionDir = '%s/motion_assess'%curDir
    if not op.exists(motionDir): # fsf dir
        print('Creating new folder %s'%motionDir)
        os.system("mkdir %s"%motionDir)
    
    os.system('fsl5.0-fsl_motion_outliers -i %s -o %s/confound.txt --fd --thresh=0.9 -p %s/fd_plot -v > %s/outlier_output.txt'%(strippedBold,motionDir,motionDir,motionDir))
    os.system("cat %s/outlier_output.txt >> %s"%(motionDir, outhtml))
    os.system("echo '<p>=============<p>FD plot %s <br><IMG BORDER=0 SRC=%s/fd_plot.png WIDTH=100%s></BODY></HTML>' >> %s"%(motionDir, motionDir,'%', outhtml))
    if os.path.isfile("%s/confound.txt"%motionDir)==False:
      os.system("touch %s/confound.txt"%motionDir)    
      
    output = subprocess.check_output("grep -o 1 %s/confound.txt | wc -l"%motionDir, shell=True)
    num_scrub = [int(s) for s in output.split() if s.isdigit()]
    shell()
    if num_scrub[0]>45:
        with open(out_bad_pp, "a") as myfile:
          myfile.write("%s\n"%motionDir)      
    
