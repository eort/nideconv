import glob
import subprocess
from IPython import embed as shell
"""
A little checker function dedicated to inspect event parameters and their
sensibility
"""
evkey = "FreeChoiceME"
all_events = glob.glob('/home/data/foraging/sub*/func/%s/*.tsv'%evkey)
all_events.sort()
for f in all_events:
	a =  subprocess.check_output(["awk", "$2 > 1.0","%s"%f])
	if len(a) != 0 and float(a.split()[0])!=0:
		print f, a