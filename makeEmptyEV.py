#!/usr/bin/python

import os
import sys
import os.path as op
import glob
import IO as io
from IPython import embed as shell

def run(evkey,outfile,th =2):
	"""
	Reads event files and counts the number of entries in it. 
	Creates a file with empty EVs per run and subject. 
	Alternatively, excludes additional runs that don't have enough EVs per condition
	"""
	try:
		os.remove(outfile)
	except:
		pass
	all_events = glob.glob('/home/data/exppsy/ora_Amsterdam/sub*/func/%s/*.tsv'%evkey)
	all_events.sort()
	for f in all_events:
		with open(f, 'r') as infile:
			allEvents =  []
			for idx,l in enumerate(infile):
				allEvents.append(io.str2list(l))
			if len(allEvents) < 2 and 'error' not in f:
				evF = op.basename(f)
				specs = '%s\t%s\t%s\n'%(evF[4:6],evF[7:9],evF[10:-4-len(evkey)])
				with open(outfile, 'a') as out:
						out.write(specs)
			
if __name__ == '__main__':

	try:
		evkey = sys.argv[1]
	except IndexError as e:
		print 'You need to specify the feat directories'
		sys.exit()
	try:
		th = int(sys.argv[2])
	except IndexError as e:
		th = 2

	try:
		outfile = op.join('/home/data/exppsy/ora_Amsterdam/generalInfo/',sys.argv[3])
	except IndexError as e:
		outfile = '/home/data/exppsy/ora_Amsterdam/generalInfo/emptyEVs_%s_th-%s.tsv'%(evkey,th)

	run(evkey,outfile,th)