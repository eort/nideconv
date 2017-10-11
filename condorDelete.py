#!/usr/bin/python
import os
import glob

fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/fsf/search')
for f in fil:
    os.system("rm -r %s"%f)
fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/fsf/2ndlvl/search')
for f in fil:
    os.system("rm -r %s"%f)
fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/models/2ndlvl/search_*')
for f in fil:
    os.system("rm -r %s"%f)
fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/models/*search_*')
for f in fil:
    os.system("rm -r %s"%f)
fil = glob.glob('/home/data/exppsy/ora_Amsterdam/sub-*/models/1stlvl/*search.*')
for f in fil:
    os.system("rm -r %s"%f)
fil = glob.glob('/home/data/exppsy/ora_Amsterdam/group_level/search')
for f in fil:
    os.system("rm -r %s"%f)