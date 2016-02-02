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

# We need to fake cadence numbers.
def merge():
	pass

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
			_, times, fluxs = utils.csv_column_read(f, FIELDS, casts=CASTS)

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
		TIME = np.append(TIME, times)
		FLUX = np.append(FLUX, fluxs)

	# Do the thing.
	CADN = np.arange(TIME.shape[0]) + 1
	utils.csv_column_write(outf, [CADN, TIME, FLUX], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		DEFAULT_ORDER = 3
		DEFAULT_SIZE = 101

		parser = argparse.ArgumentParser(description="Given the results of a photometric analysis, conduct a high pass filter to remove simple systematics by decorellating a Savgol smoothed version.")
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
