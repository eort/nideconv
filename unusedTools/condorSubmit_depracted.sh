# based on standard file, create specific fsf files for all the runs

if [ "$1" == "" ]; then
	echo "Specify which fsf files you want to use"
	exit -1
else
	ID=$1
fi
if [ "$2" == "" ]; then
	echo "Specify which level"
	exit -1
else
	LVL=$2
fi
if [ "$3" == "" ]; then
	subs=24
else
	subs=$3
fi

# populate files
for SUB in $(seq -f "%02g" 1 $subs);do
	condor_submit sub-${SUB}/models/sub-${SUB}_${ID}_${LVL}.submit
done

