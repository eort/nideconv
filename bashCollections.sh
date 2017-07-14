# based on standard file, create specific fsf files for all the runs

# move BIDS formatted files from subfolder to subfolder, for all subjects
for i in 0{1..9} {10..24}; do mv sub-$i*.edf sub-$i/edf/; done;


# Change filenames in current directort
find . -name 'file*.tsv' -exec rename 's/s-/sub-/' {} \;
