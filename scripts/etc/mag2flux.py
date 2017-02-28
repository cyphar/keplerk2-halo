#!/usr/bin/env python3
# keplerk2-halo: Halo Photometry of Contaminated Kepler/K2 Pixels
# Copyright (C) 2017 Aleksa Sarai <cyphar@cyphar.com>
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

import os
import sys
import argparse

import utils
import numpy

def main(ifile, config):
	with open(ifile) as f:
		ts, Vs = utils.csv_column_read(f, ["t", "V"], casts=[float, float])

	# For any given spectral band, the apparent magnitude is given by:
	#   m_x = -5 log_{100} (\frac{F_x}{F_{x,0}})
	# And a difference (m_1 - m_2) is given by:
	#   dm  = -5 log_{100} (\frac{F_1}{F_2})
	# Which means that F (as a fraction of some reference F_{x,0}) is given by:
	#   F   = 100^{\frac{m}{5}}

	fluxs = 100 ** (Vs / 5.0)

	if config.inverse:
		fluxs = 1.0 / fluxs

	out = sys.stdout
	if config.ofile:
		out = open(config.ofile)

	utils.csv_column_write(out, [ts, fluxs], ["t", "flux"])
	out.close()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generates a HR diagram from a file output from find_interesting.py.")
	parser.add_argument("-s", "--save", dest="ofile", type=str, default=None, help="The output file.")
	parser.add_argument("-i", "--inverse", dest="inverse", action="store_const", default=False, const=True, help="Invert the flux, which should be done if m = m_target - m_ref.")
	parser.add_argument("--no-inverse", dest="inverse", action="store_const", default=False, const=False, help="Do not invert the flux, which should be done if m = m_ref - m_target. (default)")
	parser.add_argument("csv", nargs=1)

	args = parser.parse_args()
	main(ifile=args.csv[0], config=args)
