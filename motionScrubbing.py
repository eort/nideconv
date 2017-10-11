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

shell()

for bold in boldfiles:
    strippedBold = bold[:-7] # remove file path
    curDir = op.dirname(bold)
    motionDir = '%s/motion_assess'%curDir
    if not op.exists(motionDir): # fsf dir
        print('Creating new folder %s'%motionDir)
        os.system("mkdir %s"%motionDir)
    
    os.system('fsl_motion_outliers -i -o %s/confound.txt --fd --thresh=0.9 -p %s/fd_plot -v > %s/outlier_output.txt'%(strippedBold,motionDir,motionDir,motionDir))
    os.system("cat %s/outlier_output.txt >> %s"%(motionDir, outhtml))
    os.system("echo '<p>=============<p>FD plot %s <br><IMG BORDER=0 SRC=%s/fd_plot.png WIDTH=100%s></BODY></HTML>' >> %s"%(motionDir, motionDir,'%', outhtml))
    if os.path.isfile("%s/confound.txt"%motionDir)==False:
      os.system("touch %s/confound.txt"%motionDir)    
      
    output = subprocess.check_output("grep -o 1 %s/confound.txt | wc -l"%motionDir, shell=True)
    num_scrub = [int(s) for s in output.split() if s.isdigit()]
    shell()
    if num_scrub[0]>45:
        with open(out_bad_bold_list, "a") as myfile:
          myfile.write("%s\n"%(cur_bold))      
    
with open(outfile, 'w') as out:    
    for f in all_feats:
		out.write("<p>============================================")
		out.write("<p>%s"%(f))
		out.write("<IMG SRC=\"%s/design.png\">"%f)
		out.write("<IMG SRC=\"%s/design_cov.png\" >"%f)
		out.write("<IMG SRC=\"%s/disp.png\">"%f)
		out.write("<IMG SRC=\"%s/rot.png\">"%f)
		out.write("<IMG SRC=\"%s/trans.png\" >"%f)
		out.write("<p><IMG SRC=\"%s/example_func2highres.png\" WIDTH=1200>"%f)
		out.write("<p><IMG SRC=\"%s/example_func2standard.png\" WIDTH=1200>"%f)
		out.write("<p><IMG SRC=\"%s/highres2standard.png\" WIDTH=1200>"%f)