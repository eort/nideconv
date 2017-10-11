#!/usr/bin/python

import os
import sys
import os.path as op
import glob
import local2remote as l2r


def run(key,outfile,conv= True):
	all_feats = glob.glob('/home/data/exppsy/ora_Amsterdam/sub*/models/1stlvl/*%s.feat/'%key)
	all_feats.sort()

	with open(outfile, 'w') as out:    
	    for f in all_feats:
			out.write("<p>============NEXT RUN==================<br>")
			out.write("<p>%s <br>"%(f))
			out.write("<p>____________DESIGN MATRICES__________<br>")
			out.write("<IMG SRC=\"%s/design.png\"> <br>"%f)
			out.write("<IMG SRC=\"%s/design_cov.png\" > <br>"%f)
			out.write("<p>________________MOTION_____________<br>")
			out.write("<IMG SRC=\"%s/mc/disp.png\"> <br>"%f)
			out.write("<IMG SRC=\"%s/mc/rot.png\"> <br>"%f)
			out.write("<IMG SRC=\"%s/mc/trans.png\" > <br>"%f)
			out.write("<p>____________Registration__________<br>")
			out.write("<p>____________example_func2highres__________<br>")
			out.write("<p><IMG SRC=\"%s/reg/example_func2highres.png\" WIDTH=1200> <br>"%f)
			out.write("<p>____________example_func2standard__________<br>")
			out.write("<p><IMG SRC=\"%s/reg/example_func2standard.png\" WIDTH=1200> <br>"%f)
			out.write("<p>____________highres2standard__________<br>")			
			out.write("<p><IMG SRC=\"%s/reg/highres2standard.png\" WIDTH=1200> <br>"%f)
	if conv:
		infile, extension = op.splitext(outfile)
		outputfile = infile + '_loc' + extension
		l2r.run(outfile,'rem2loc',outputfile)

if __name__ == '__main__':
	try:
		featkey = sys.argv[1]
	except IndexError as e:
		print 'You need to specify the feat directories'
		sys.exit()
	try:
		outfile = op.abspath(sys.argv[2])
	except IndexError as e:
		outfile = '/home/data/exppsy/ora_Amsterdam/generalInfo/QA_lvl1_%s.html'%featkey
	try:
		conv = int(sys.argv[3])
		try: assert conv in [0,1]
		except AssertionError as e: print('Invalid conversion parameter, will do conversion anyway');conv =1
	except IndexError as e:
		conv = 1

	run(featkey,outfile, conv = conv)