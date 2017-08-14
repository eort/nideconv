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
for SUB in $(seq -f "%02g" 1 $subs);do
	sed -e "s/##SUB##/$SUB/g" < $1 > sub-${SUB}/fsf/sub-${SUB}_1stLvl.submit
done

