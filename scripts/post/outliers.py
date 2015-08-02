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
import warnings

#import statsmodels as sm
#import statsmodels.api

import numpy as np

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]

DETERMINATION_THRESHOLD = 0.5

def reject_outliers(xs, ys, config):
	#regression = sm.api.OLS(xs, ys).fit()
	#outliers = regression.outlier_test()

	# We're very angry here.
	sigma = np.std(ys)
	mean = np.mean(ys)

	return (mean - config.sigma*sigma < ys) & (ys < mean + config.sigma*sigma)

def main(inf, outf, config):
	with open(inf, "r", newline="") as inf:
		cadns, times, fluxs = utils.csv_column_read(inf, FIELDS, start=config.start, end=config.end, casts=CASTS)

	# Remove outliers.
	filt = reject_outliers(times, fluxs, config)

	cadns = cadns[filt]
	times = times[filt]
	fluxs = fluxs[filt]

	utils.csv_column_write(outf, [cadns, times, fluxs], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given the results of several photometric analyses, decorrelate the data using a given type.")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-s", "--save", dest="out", type=str, default=None, help="The output file (default: stdout).")
		#parser.add_argument("-t", "--threshold", dest="threshold", type=float, default=DETERMINATION_THRESHOLD, help="The threshold for the outlier test (default: %f)." % (DETERMINATION_THRESHOLD,))
		parser.add_argument("-si", "--sigma", dest="sigma", type=float, default=3, help="Sigma cutoff for an outlier (default: 3).")
		parser.add_argument("file", nargs=1)

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")

		main(inf=config.file[0], outf=outf, config=config)

	__wrapped_main__()
