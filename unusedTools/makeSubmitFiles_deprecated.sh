# based on standard file, create specific fsf files for all the runs

# input check
if [ "$1" == "" ]; then
	echo Error. You need to specify the default fsf file!
	exit -1
fi

if [ "$2" == "" ]; then
	echo "Specify which fsf files you want to use"
	exit -1
else
	ID=$2
fi
if [ "$3" == "" ]; then
	echo "Specify which level"
	exit -1
else
	LVL=$3
fi
if [ "$4" == "" ]; then
	subs=21
else
	subs=$4
fi


# populate files
for SUB in $(seq -f "%02g" 1 $subs);do
	sed -e "s/##SUB##/$SUB/g; s/##ID##/$ID/g" < $1 > sub-${SUB}/models/sub-${SUB}_${ID}_${LVL}.submit
done

