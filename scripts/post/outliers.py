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

import sys
import argparse

import numpy as np

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]

# In order to deal with local outliers, we need to do a "windowed" outlier
# rejection. The number of passes required (and the window size and step size)
# are a matter of taste, and we'll need to investigate what the best defaults
# are. I'm worried about having step_size < window_size, because you end up
# doing outlier rejection multiple times on the same chunk in the same pass. So
# we're not going to do it that way.

def reject_outliers(xs, ys, config):
	# Start with a filter made entirely of zeros.
	filt = np.ones_like(ys).astype(bool)
	xs = xs - np.min(xs)

	# Do n windows, each with a width of n days.
	for width in np.arange(config.passes) + 1:
		# Do a n-day window.
		days = np.unique(np.floor(xs / width))
		for day in days * width:
			window = (day <= xs) & (xs < day + width)

			sigma = np.std(ys[filt & window])
			mean = np.mean(ys[filt & window])

			filt[filt & window] &= ((mean - config.sigma*sigma < ys[filt & window]) & (ys[filt & window] < mean + config.sigma*sigma))

	return filt

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
		parser.add_argument("-si", "--sigma", dest="sigma", type=float, default=4, help="Sigma cutoff for an outlier (default: 4).")
		parser.add_argument("-p", "--passes", dest="passes", type=int, default=3, help="Number of passes when doing windowing (default: 3).")
		parser.add_argument("file", nargs=1)

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")

		main(inf=config.file[0], outf=outf, config=config)

	__wrapped_main__()
