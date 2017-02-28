#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2017 Aleksa Sarai <cyphar@cyphar.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import argparse

import utils
import numpy

def main(ifile, config):
	out = sys.stdout
	if config.ofile:
		out = open(config.ofile)

	with open(ifile) as f:
		first = f.readline().strip()
		fields = first.split(",")

		try:
			t_idx = fields.index("t")
		except ValueError:
			sys.stderr.write("No 't' entry in CSV.\n")
			sys.exit(1)

		out.write(first + "\n")
		for line in f:
			entries = line.strip().split(",")
			entries[t_idx] = "%.17g" % (float(entries[t_idx]) * config.period + config.offset,)
			out.write(",".join(entries) + "\n")
		out.flush()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a HR diagram from a file output from find_interesting.py.")
	parser.add_argument("-p", "--period", dest="period", type=float, default=1.0, help="Period to expand the phase to.")
	parser.add_argument("-O", "--offset", dest="offset", type=float, default=0.0, help="Offset to add to the phase (in terms of _time_ not phase).")
	parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
	parser.add_argument("csv", nargs=1)

	args = parser.parse_args()
	main(ifile=args.csv[0], config=args)
