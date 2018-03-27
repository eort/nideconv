#!/bin/bash

## check input

if [ "$1" == "" ]; then
    echo ERROR. You need to specify the directory of the raw files
    exit -1
else 
    rawDir="$1"
fi

## prepare folders for extraction
#array=$(ls $rawDir | grep .tar.gz) 
array=$(ls $rawDir | grep  .tar.gz) #-v 'bf68*') 

# set a couple of variables
home="/home/data/foraging"

echo $array
heudiconv -d 'raw/dcm/{subject}' -s $array -f $home/code/heudiconv_heuristic.py -o $home -a $home --anon-cmd $home/code/anon_id.py -b
echo "finished"
