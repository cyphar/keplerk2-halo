#!/bin/zsh

OUT="${OUT:-done.csv}"

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
done

echo ":: merge"
./scripts/etc/merge.py -s $working/merged.csv $working/ppm/*.csv

echo ":: outlier"
./scripts/post/outliers.py -si 4 -p 10 -s "$OUT" $working/merged.csv
