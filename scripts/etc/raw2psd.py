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
import argparse

import numpy as np

import utils

def main(inf, outf, config):
	FIELDS = ["frequency", "amplitude"]
	CASTS = [float, float]

	with open(inf, "r", newline="") as f:
		fx, fy = utils.csv_column_read(f, FIELDS, casts=CASTS)

	# Do the thing.
	fx, fy = utils.raw_to_psd(fx, fy, config.variance)

	# Output the PSD.
	FIELDS[1] = "psd"
	utils.csv_column_write(outf, [fx, fy], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given a 'raw' periodogram, produce a PSD.")
		parser.add_argument("-v", "--variance", dest="variance", type=float, help="The variance of the flux.")
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

