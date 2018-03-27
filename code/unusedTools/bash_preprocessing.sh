#!/bin/bash
# Ede in 2017
if [ "$1" == "" ]; then
	echo Need to specify lower limit of pp number
	exit -1
else
	min="$1"
fi
#Third
if [ "$2" = "" ]; then
	echo Need to specify upper limit of pp number
	exit -1
else
	max="$2"
fi

for SUB in $( seq -w $min $max ) 
	do 
	mkdir sub-$SUB/asc sub-$SUB/edf sub-$SUB/os_csv;
	for RUN in $( seq -w 1 10 ) 
		do
		mv sub-$SUB/run-$RUN/* sub-$SUB; 
	done
	mv sub-$SUB/*.edf sub-$SUB/edf;
	mv sub-$SUB/*.csv sub-$SUB/os_csv;
	

done
