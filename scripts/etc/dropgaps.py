#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2016 Aleksa Sarai <cyphar@cyphar.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import csv
import sys
import argparse

import numpy

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]


def main(inf, outf, config):
	with open(inf, "r", newline="") as f:
		cadns, times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

	diffs = numpy.diff(times).copy()
	assert(numpy.all(diffs >= 0))

	for idx, gap in zip(*numpy.where(diffs > config.width), diffs[diffs > config.width]):
		# We only remove the gap to the scale of the median.
		gap -= gap % numpy.median(diffs)

		# Remove the gap. This isn't a concurrent modification because the diffs aren't views.
		times[idx+1:] -= gap

	# Output the FFT.
	utils.csv_column_write(outf, [cadns, times, fluxs], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given the results of a photometric analysis, conduct a high pass filter to remove simple systematics by decorellating a Savgol smoothed version.")
		parser.add_argument("-w", "--width", dest="width", type=float, required=True, help="Minimum width of gap to drop in days.")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-s", "--save", dest="out", type=str, default=None, help="The output file (default: stdout).")
		parser.add_argument("file", nargs=1)

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")
		main(inf=config.file[0], outf=outf, config=config)

	__wrapped_main__()

