#!/usr/bin/python
"""
First input is root path were subject folders are located
Second input is number of expected volumes. default to 210
"""
import glob
import os
import sys
import subprocess

try:
    path = os.path.abspath(sys.argv[1])
except:
    path = '/home/data/foraging'
    print("use default path as no other path was specified")
try: nvol = sys.argv[2]
except: nvol=210 # How many volumes do I expect?

files = glob.glob('%s/sub-[0-2][0-9]/func/*nii.gz'%(path))
files.sort()

print len(files) # how many niftis do I have?
for f in files:
    o = subprocess.check_output(["fslnvols", "%s"%f])
    if int(o)<nvol: 
        print(o, os.path.basename(f)) # print out only those that are weird
