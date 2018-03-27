#!/bin/bash
# Ede in 2016

: '
This script runs the edf2ascii converter over all edf files in a directory
The converter that is used is for windows (default one in cogpsy department)\
Therefore, has to be launched with wine-command
First input argument has to be the path to the directory of interest
Second input specifies output folder where files are moved to after conversion
Third input indicates whether conversion should also be done if corresponding ascii file already exists [yes,no]
Forth input specifies all options for the actual converter. Pass all in quotation marks.

Example: run_edf2asc ~/experiment/data/edf ~/experiment/data/asc "yes" "-ns"
'
# check whether input was passed properly
#First
if [ "$1" == "" ]; then
	echo Conversion failed. You need to specify an input directory!
	exit -1
else
	input="$1"
fi
#Third
if [ "$3" = "" ]; then
	overwrite="no"
else
	overwrite="$3"
fi	
#Forth
if [ "$4" = "" ]; then
	options="-ns" 
else
	options="$4"
fi	

#get current directory
curdir=$(pwd)
echo $input
# create list with edf files of interest
array=$(ls $input )
echo $array
#path to converter
conv="/home/data/foraging/code/"

# loop over files and call wine with options and inputfiles
for i in $array; do
	if echo $i | grep .edf ; then
		outputfile=${i:0:-3}"asc" # make outputfile
		echo $outputfile
		echo $overwrite | $conv/edf2asc $options $input$i
		# if output directory specified move file to there
		if [ "$2" != "" ]; then
			mv $input$outputfile $2$outputfile
		fi
	fi
done
