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
import warnings

import numpy as np
import numpy.random

import utils

FIELDS = ["cadence", "t", "flux"]
CASTS = [int, float, float]

def fake_data(cadn, time):
	return 0.5 * np.sin(53*time) + 0.15 * np.sin(82*time + 132)

# TODO: Drop larger chunks, more valid.
def drop_data(samples, chance):
	return np.random.random(samples) < chance

def main(outf, config):
	cadns = np.linspace(1, config.samples, config.samples)
	times = np.linspace(config.start, config.end, config.samples)
	fluxs = fake_data(cadns, times)

	# Drop random parts of the data.
	filt = drop_data(config.samples, config.chance)

	cadns = cadns[filt]
	times = times[filt]
	fluxs = fluxs[filt]

	utils.csv_column_write(outf, [cadns, times, fluxs], FIELDS)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Given the results of several photometric analyses, decorrelate the data using a given type.")
		parser.add_argument("-ns", "--num-samples", dest="samples", type=int, default=500, help="Number of samples (default: 500).")
		parser.add_argument("-c", "--chance", dest="chance", type=float, default=0.8, help="Number of samples (default: 500).")
		parser.add_argument("-st", "--start-time", dest="start", type=float, default=0, help="Start time (default: 0).")
		parser.add_argument("-et", "--end-time", dest="end", type=float, default=30, help="End time (default: 30).")
		parser.add_argument("-s", "--save", dest="out", type=str, default=None, help="The output file (default: stdout).")

		config = parser.parse_args()

		outf = config.out
		if outf == None:
			outf = sys.stdout
		else:
			outf = open(outf, "w", newline="")

		main(outf=outf, config=config)

	__wrapped_main__()
