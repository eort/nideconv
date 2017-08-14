# based on standard file, create specific fsf files for all the runs

# move BIDS formatted files from subfolder to subfolder, for all subjects
for i in 0{1..9} {10..24}; do mv sub-$i*.edf sub-$i/edf/; done;


# Change filenames in current directort
find . -name 'file*.tsv' -exec rename 's/s-/sub-/' {} \;


#doing the same thing from within a function (not sure why above script didnt work)

f () { find . -name "$1" -exec rename 's/run-/run-0/' {} \; ;}
for i in $( seq -f "%02g" 2 21); do  cd sub-$i/func/; f '*task-choice*'; cd ../.. ; done

