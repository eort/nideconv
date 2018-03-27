# -*- coding: utf-8 -*-
"""
Created on Mon Apr 24 18:30:18 2017

@author: ede
"""

import pickle
import numpy as np

session = int(raw_input('Which session? '))
timepoint = int(raw_input('Before or after (0 or 1)? '))
#Input  = open(('/home/ede/Desktop/FINALFILES/data/colors-%.2i.pkl' %session), 'rb')
Input  = open(('/home/slnib/studies/psyinf/experiments/Foraging/exp_files/colors-%.2i-%.2i.pkl' %(session,timepoint)), 'rb')
colors = pickle.load(Input)
Input.close()

target_pairs_free =[['red','green'],['brown','green'],['blue','green'],['purple','green'],['brown','red'],\
			['blue','red'],['purple','red'],['blue','brown'],['purple','brown'],['purple','blue']]*2
target_pairs_forced =[['red','green'],['brown','green'],['blue','green'],['purple','green'],['brown','red'],\
			['blue','red'],['purple','red'],['blue','brown'],['purple','brown'],['purple','blue']]*2
free_seqs = [np.array([0,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,0,0,0]),\
		np.array([1,1,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,0,0,0]),
		np.array([0,0,1,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,1,1,1,0,0,1,1,0,0,0,0,0]),
		np.array([0,0,0,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0])]
df_idx =None
run_no = 0
block_no = 0
colors  = {k:list(l) for k,l in colors.items()}
Outdata = {'colors': colors,'target_pairs_free':target_pairs_free,'target_pairs_forced':target_pairs_forced,'block_no':block_no,'run_no':run_no,'free_seqs':free_seqs,'df_idx':df_idx}
output = open('defaultSettings.pkl', 'wb')
pickle.dump(Outdata, output)
output.close()
