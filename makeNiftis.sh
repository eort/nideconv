#!/bin/bash

## check input

if [ "$1" == "" ]; then
    echo ERROR. You need to specify the directory of the raw files
    exit -1
else 
    rawDir="$1"
fi

## prepare folders for extraction
array=$(ls $rawDir | grep .tar.gz) 

# set a couple of variables
home="/home/data/exppsy/ora_Amsterdam/"

echo $array
python heudiconv -d 'raw/dcm/%s' -s $array -f $home/raw/code/heudiconv_heuristic.py -o $home --anon-cmd $home/raw/code/anon_id.py
echo "finished"
