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

import sklearn as sk
import sklearn.preprocessing

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]

def reduce_sum(fluxs):
	# Normalise and sum.
	fluxs = sk.preprocessing.normalize(fluxs, axis=1)
	fluxs = np.sum(fluxs, axis=0)
	return fluxs

def reduce_mean(fluxs):
	# Normalise and get the mean.
	fluxs = sk.preprocessing.normalize(fluxs, axis=1)
	fluxs = np.mean(fluxs, axis=0)
	return fluxs

def reduce_median(fluxs):
	# Normalise and get the median.
	fluxs = sk.preprocessing.normalize(fluxs, axis=1)
	fluxs = np.median(fluxs, axis=0)
	return fluxs

def main(files, outf, config):
	# Cadences.
	cadns = []
	times = []
	fluxs = []
	for fname in files:
		with open(fname, "r", newline="") as f:
			# Get CSV.
			_cadn, _time, _flux = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

		# Convert to numpy arrays.
		cadns.append(_cadn)
		times.append(_time)
		fluxs.append(_flux)

	# Get unique set.
	inter = cadns[0]
	for cadn in cadns[1:]:
		inter = np.intersect1d(inter, cadn)

	# Filter out each array.
	for i, cadn in enumerate(cadns):
		filt = np.in1d(cadn, inter)

		cadns[i] = cadns[i][filt]
		times[i] = times[i][filt]
		fluxs[i] = fluxs[i][filt]

	# Convert filtered version to arrays (now everything is the same shape).
	cadns = np.median(cadns, axis=0)
	times = np.median(times, axis=0)
	fluxs = np.array(fluxs, dtype=float)

	# Combine the flux values.
	fluxs = config.reduce(fluxs)
	utils.csv_column_write(outf, [cadns, times, fluxs], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given the results of several photometric analyses, reduce the data for all cadences present in all data files.")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-s", "--save", dest="out", type=str, default=None, help="The output file (default: stdout).")
		parser.add_argument("files", nargs='+')
		o_reduce = parser.add_mutually_exclusive_group(required=True)
		o_reduce.add_argument("--sum", dest="reduce", action="store_const", const=reduce_sum, help="Combine by normalising and summing the values.")
		o_reduce.add_argument("--mean", dest="reduce", action="store_const", const=reduce_mean, help="Combine by normalising and averaging the values.")
		o_reduce.add_argument("--median", dest="reduce", action="store_const", const=reduce_median, help="Combine by normalising and getting the median of the values.")

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")

		main(files=config.files, outf=outf, config=config)

	__wrapped_main__()
