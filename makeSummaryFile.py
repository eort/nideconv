#!/usr/bin/python

import os
import sys
import os.path as op
import glob

try:
	featkey = sys.argv[1]
except IndexError as e:
	print 'You need to specify the feat directories'
	sys.exit()

try:
	outfile = op.abspath(sys.argv[2])
except IndexError as e:
	outfile = '/home/data/exppsy/ora_Amsterdam/lvl1_QC_search.html'

all_feats = glob.glob('/home/data/exppsy/ora_Amsterdam/sub*/models/1stlvl/*%s.feat/'%featkey)
all_feats.sort()

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