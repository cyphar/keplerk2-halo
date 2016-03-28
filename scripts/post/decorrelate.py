#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2015 Aleksa Sarai <cyphar@cyphar.com>
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
import warnings

import numpy as np

import scipy as sp
import scipy.stats
import scipy.signal

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]

DETERMINATION_THRESHOLD = 0.5

def decorrelate_data(tp, xs, ys):
	R = 0

	if tp == "linear":
		# We do a simple linear regression to remove any (trivial) linear
		# systematics. This doesn't solve the general case, but it does help
		# with decorrelating common systematics not solved by accurate tracking
		# data.

		# y = m*x + C
		_, _, R, _, _ = sp.stats.linregress(xs, ys)
		ys = sp.signal.detrend(ys, type="linear")

	return ys, R

def main(inf, outf, config):
	with open(inf, "r", newline="") as inf:
		cadns, times, fluxs = utils.csv_column_read(inf, FIELDS, start=config.start, end=config.end, casts=CASTS)

	# Decorrelate flux.
	fluxs, _ = decorrelate_data(config.tp, times, fluxs)
	utils.csv_column_write(outf, [cadns, times, fluxs], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given the results of several photometric analyses, decorrelate the data using a given type.")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-s", "--save", dest="out", type=str, default=None, help="The output file (default: stdout).")
		parser.add_argument("file", nargs=1)
		o_type = parser.add_mutually_exclusive_group(required=True)
		o_type.add_argument("--linear", dest="tp", action="store_const", const="linear", help="Decorrelate using linear regression.")

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")

		main(inf=config.file[0], outf=outf, config=config)

	__wrapped_main__()
