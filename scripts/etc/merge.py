#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2016 Aleksa Sarai <cyphar@cyphar.com>
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

import csv
import sys
import math
import argparse

import numpy

import utils

FIELDS = ["t", "flux"]
CASTS = [float, float]

def main(files, outf, config):
	TIME = []
	FLUX = []

	# We split the filename into <fname>[:<start>:<end>].
	for fname in files:
		start = 0
		end = -1

		# Allow slices in fnames.
		if ":" in fname:
			fname, start, end = fname.split(":")

		# Float.
		start = float(start)
		end = float(end)

		# Open file.
		with open(fname, "r", newline="") as f:
			times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS)

		# Times.
		offset = times - times.min()

		# Allow negative slices.
		if end < 0:
			end = offset.max() + (end + 1)

		# Filter.
		filt = (start <= offset) & (offset <= end)
		times = times[filt]
		fluxs = fluxs[filt]

		# Append.
		TIME = numpy.append(TIME, times)
		FLUX = numpy.append(FLUX, fluxs)

	# Fake the cadence numbers.
	CADN = numpy.arange(TIME.shape[0]) + 1

	# We need to sort by the time. This is a bit of a pain, because the operation
	# of "sorting rows" isn't a thing in numpy. We need to switch out to Python
	# lists.
	tosort = numpy.array([TIME, FLUX]).T
	tosort = sorted(list(tosort), key=lambda arr: arr[0])
	TIME, FLUX = numpy.array(tosort).T

	utils.csv_column_write(outf, [CADN, TIME, FLUX], ["cadence"] + FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		DEFAULT_ORDER = 3
		DEFAULT_SIZE = 101

		parser = argparse.ArgumentParser(description="Given a set of time series, merge them into one. You can use slice syntax at the end of the file to use subsets of time series.")
		parser.add_argument("-s", "--save", dest="out", type=str, default=None, help="The output file (default: stdout).")
		parser.add_argument("files", nargs='+')

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")

		main(files=config.files, outf=outf, config=config)

	__wrapped_main__()
