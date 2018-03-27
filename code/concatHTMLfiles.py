import sys
from os import path as op
def run(files,outfile):

	with open(outfile, 'w') as out:
		for f in files:
			with open(f) as inf:
				out.write(inf.read())
			out.write('\n')

if __name__=='__main__':
	if len(sys.argv)<3:
		print('Not enough input arguments')
		sys.exit()
	try:
		files = sys.argv[1:-1]
	except IndexError:
		print('You need to provide files to be concatenated')
		sys.exit()  
	try:
		outfile = op.abspath(sys.argv[-1])
	except IndexError:
		print('You need to provide files to be concatenated')
		sys.exit()          
	run(files,outfile)