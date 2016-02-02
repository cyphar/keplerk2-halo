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
import math
import argparse

import astropy
import astropy.convolution

import numpy as np

import scipy as sp
import scipy.signal
import scipy.interpolate

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]

def highpass(ts, ys, config):
	# Smooth using a Savgol filter.
	itp = sp.interpolate.interp1d(ts, ys, kind='linear')
	smooth = sp.signal.savgol_filter(itp(ts), config.size, config.order)

	# Subtract a smoothed version then add the mean to produce a realistic value.
	ys -= smooth - ys.mean()

	# Convert to ppm.
	if config.residual:
		ys = (ys - ys.mean()) / ys.mean()
		ys *= 1e6

	return ts, ys

def main(inf, outf, config):
	with open(inf, "r", newline="") as f:
		cadns, times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS, start=config.start, end=config.end)

	# Do the thing.
	times, fluxs = highpass(times, fluxs, config)
	utils.csv_column_write(outf, [cadns, times, fluxs], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		DEFAULT_ORDER = 3
		DEFAULT_SIZE = 101

		parser = argparse.ArgumentParser(description="Given the results of a photometric analysis, conduct a high pass filter to remove simple systematics by decorellating a Savgol smoothed version.")
		parser.add_argument("-sc", "--start", dest="start", type=int, default=None, help="Start cadence (default: None).")
		parser.add_argument("-ec", "--end", dest="end", type=int, default=None, help="End cadence (default: None).")
		parser.add_argument("-r", "--residual", dest="residual", action="store_const", const=True, default=False, help="Return residuals in ppm.")
		parser.add_argument("--no-residual", dest="residual", action="store_const", const=False, default=False, help="Return just corrected light curve (default).")
		parser.add_argument("-w", "--width", dest="size", type=int, default=DEFAULT_SIZE, help="Window size of filter (default: %f)." % (DEFAULT_SIZE,))
		parser.add_argument("-o", "--order", dest="order", type=int, default=DEFAULT_ORDER, help="Order of polynomial (default: %f)." % (DEFAULT_ORDER,))
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
