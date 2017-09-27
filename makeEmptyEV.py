#!/usr/bin/python

import os
import sys
import os.path as op
import glob
import IO as io
from IPython import embed as shell

try:
	evkey = sys.argv[1]
except IndexError as e:
	print 'You need to specify the feat directories'
	sys.exit()

try:
	outfile = op.abspath(sys.argv[2])
except IndexError as e:
	outfile = '/home/data/exppsy/ora_Amsterdam/generalInfo/emptyEVs_%s.tsv'%evkey
os.system('rm %s' %outfile)

all_events = glob.glob('/home/data/exppsy/ora_Amsterdam/sub*/func/%s/*.tsv'%evkey)
all_events.sort()

for f in all_events:
	with open(f, 'r') as infile:
		for idx,l in enumerate(infile):
			allVal = sum(io.str2list(l))
			if allVal == 0 and 'error' not in f:
				evF = op.basename(f)
				specs = '%s\t%s\t%s\n'%(evF[4:6],evF[7:9],evF[10:-4-len(evkey)])
				print specs
				with open(outfile, 'a') as out:
						out.write(specs)
			
