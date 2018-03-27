#!/usr/bin/python

import os
import sys
import os.path as op
import glob
import local2remote as l2r


def run(key,outfile,mode,conv= True ):
	"""
	key:		Which Analysis directory (keyword, e.g. searchF)
	outfile: 	Which HTML ouput file to use
	mode: 		What kind of information to include
				1:DM,2:MC,3:Reg,4:DM,MC,5:DM,REG,6:REG,MC,7:All
	conv:		Want to convert the file to locale? 1,0
	"""
	all_feats = glob.glob('/home/data/foraging/scratch/sub*/models/1stlvl/*%s.feat/'%key)
	all_feats.sort()

	with open(outfile, 'w') as out:    
	    for f in all_feats:
			out.write("<p>============NEXT RUN==================<br>")
			out.write("<p>%s <br>"%(f))
			if mode in [1,4,5,7]:
				out.write("<p>~~~~~~~~~~~~~DESIGN MATRICES~~~~~~~~~~<br>")
				out.write("<IMG SRC=\"%s/design.png\"> <br>"%f)
				out.write("<IMG SRC=\"%s/design_cov.png\" > <br>"%f)
			if mode in [2,4,6,7]:
				out.write("<p>~~~~~~~~~~~~~MOTION~~~~~~~~~~<br>")
				out.write("<IMG SRC=\"%s/mc/disp.png\"> <br>"%f)
				out.write("<IMG SRC=\"%s/mc/rot.png\"> <br>"%f)
				out.write("<IMG SRC=\"%s/mc/trans.png\" > <br>"%f)		
			if mode in [3,5,6,7]:
				out.write("<p>~~~~~~~~~~~REGISTRATION~~~~~~~~~~~~<br>")
				out.write("<p>~~~~~~~~~~~example_func2highres~~~~~~~~~~~~<br>")
				out.write("<p><IMG SRC=\"%s/reg/example_func2highres.png\" WIDTH=1200> <br>"%f)
				out.write("<p>~~~~~~~~~~~example_func2standard~~~~~~~~~~~~<br>")
				out.write("<p><IMG SRC=\"%s/reg/example_func2standard.png\" WIDTH=1200> <br>"%f)
				out.write("<p>~~~~~~~~~~~highres2standard~~~~~~~~~~~~<br>")			
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
		outfile = '/home/data/exppsy/ora_Amsterdamforaging/QA/QA_lvl1_%s.html'%featkey
	try:
		mode = int(sys.argv[3])
		try: assert mode in range(1,8)
		except AssertionError as e: print('Invalid conversion parameter, will do conversion anyway');conv =1
	except IndexError as e:
		mode = 7

	try:
		conv = int(sys.argv[4])
		try: assert conv in [0,1]
		except AssertionError as e: print('Invalid conversion parameter, will do conversion anyway');conv =1
	except IndexError as e:
		conv = 1

	run(featkey,outfile, mode = mode,conv = conv)