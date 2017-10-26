#!/usr/bin/python
import os
import glob

fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/models/1stlvl/*Control*')
for f in fil:
    os.system("rm -r %s"%f)
fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/models/2ndlvl/Control*')
for f in fil:
    os.system("rm -r %s"%f)