import glob
import os
import subprocess
from IPython import embed as shell

search_phrase = '/home/data/foraging/sub-*/func'+'/*.tsv'
ev_files = glob.glob(search_phrase)
ev_files.sort()
for ev in ev_files:
    a =  subprocess.check_output(["awk", "$2 < 0.1","%s"%ev])
    print ev, a

