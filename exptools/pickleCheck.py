# -*- coding: utf-8 -*-
"""
Spyder Editor

This temporary script file is located here:
/home/slnib/.spyder2/.temp.py
"""

import pickle
import os

os.chdir('/home/slnib/studies/psyinf/experiments/Foraging/exp_files')
#a = open('data/sub-06/run-01/Settings_run01.pkl','rb')
a = open('defaultSettings.pkl','rb')
b = pickle.load(a)
len(b['target_pairs_free'])
len(b['target_pairs_forced'])