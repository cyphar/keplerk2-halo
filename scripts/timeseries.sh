#!/bin/zsh

mkdir -p tmp
export TEMPDIR=$(pwd)/tmp

local working=$(mktemp -d)
echo ":: working in $working"

mkdir -p $working/{highpass,ppm,outlier}

for file in $*
do
	echo ":: highpass => $file"
	./scripts/post/highpass.py -s $working/highpass/$(basename $file) $file

	echo ":: ppm => $file"
	./scripts/post/ppm.py -s $working/{ppm,highpass}/$(basename $file)

	echo ":: outlier => $file"
	./scripts/post/outliers.py -si 4 -p 10 -s $working/{outlier,ppm}/$(basename $file)

done

echo ":: merge"
./scripts/etc/merge.py -s merged.csv $working/outlier/*.csv
