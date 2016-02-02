#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>
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

import numpy as np

import utils

FIELDS = ["t", "flux"]
CASTS = [float, float]

def main(inf, outf, config):
	with open(inf, "r", newline="") as f:
		times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

	fx, fy = utils.lombscargle_amplitude(times, fluxs, mult=config.mult, upper=config.upper)

	# Output the FFT.
	utils.csv_column_write(outf, [fx, fy], ["frequency", "amplitude"])

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given the results of a photometric analysis, conduct a high pass filter to remove simple systematics by decorellating a Savgol smoothed version.")
		parser.add_argument("-sm", "--sampling", dest="mult", type=float, default=1, help="The multiplicative factor to the minimal sampling rate, higher is oversampling (default: 1).")
		parser.add_argument("-uf", "--upper-frequency", dest="upper", type=float, default=None, help="Upper frequency to compute up to (default: optimistic nyquist).")
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

