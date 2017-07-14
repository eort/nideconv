# based on standard file, create specific fsf files for all the runs

# input check
if [ "$1" == "" ]; then
	echo Error. You need to specify the default fsf file!
	exit -1
fi
if [ "$2" == "" ]; then
	subs=6
else
	subs=$2
fi
# populate files
for sub in $(seq 1 $subs);do

		sed -e "s/##SUB##/$sub/g" < $1 > sub-0${sub}/sub-0${sub}.fsf
done
