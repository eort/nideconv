# based on standard file, create specific fsf files for all the runs
# Only works for all participants
# input check
if [ "$1" == "" ]; then
	echo Error. You need to specify the template fsf!
	exit -1
fi
if [ "$2" == "" ]; then
	echo Error. You need to specify the template fsf!
	exit -1
fi
if [ "$3" == "" ]; then
	ID="None"
else
	ID=$3
fi
if [ "$2" == "9" ]; then
	# populate files
	for sub in 02 04 07 09 15 16 ;do
		sed -e "s/##SUB##/$sub/g" < $1 > sub-${sub}/fsf/2ndlvl/sub-${sub}_${ID}.fsf
	done
fi

if [ "$2" == "8" ]; then
	# populate files
	for sub in 01 05 06 08 1{0..4} 17 21 ;do
		sed -e "s/##SUB##/$sub/g" < $1 > sub-${sub}/fsf/2ndlvl/sub-${sub}_${ID}.fsf
	done
fi

if [ "$2" == "10" ]; then
	# populate files
	for sub in 19; do
		sed -e "s/##SUB##/$sub/g" < $1 > sub-${sub}/fsf/2ndlvl/sub-${sub}_${ID}.fsf
	done
fi
if [ "$2" == "7" ]; then
	# populate files
	for sub in 03; do
		sed -e "s/##SUB##/$sub/g" < $1 > sub-${sub}/fsf/2ndlvl/sub-${sub}_${ID}.fsf
	done
fi