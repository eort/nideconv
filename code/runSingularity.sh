#!/bin/bash
if [ "$1" == "" ]; then
	echo "Need the participant argument"
	exit -1
else
	SUB="$1"
fi

PYTHONPATH="" singularity run -H /home/data/foraging /home/data/foraging/code/poldracklab_fmriprep_1.0.8-2018-02-23-e5a227027e57.img /home/data/foraging/ /home/data/foraging/scratch/fmriPrep participant  --participant-label $SUB -w /home/data/foraging/scratch/tmp_work --output-space T1w fsaverage5 template  --use-syn-sdc --low-mem --nthreads 15 --ignore slicetiming fieldmaps --write-graph --fs-license-file /home/data/foraging/license.txt


#PYTHONPATH="" singularity run -H /home/data/foraging
		# /home/data/foraging/code/poldracklab_fmriprep_latest-2018-01-30-c68cebc75715.img
		# /home/data/foraging
		# /home/data/foraging/scratch/fmriPrep
		# participant
		# --participant-label $SUB 
		# -w /home/data/foraging/scratch/tmp_work  
		# --output-space T1w fsaverage5 template
		# --use-syn-sdc 
		# --low-mem 
		# --nthreads 1 
		# --ignore slicetiming fieldmaps 
		# --write-graph 
		# --fs-license-file /home/ort/license.txt