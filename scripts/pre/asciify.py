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

# Converts a given frame in a FITS file to ASCII (for usage with aperture
# selection during analysis).

import math
import argparse

import numpy as np

import astropy as ap
import astropy.io.fits

import utils

def asciify(array, scale="log"):
	mask = ~np.isnan(array)

	if scale == "log":
		array[mask] = np.log10(array[mask])
	elif scale == "linear":
		pass
	else:
		raise ValueError("invalid scale '%s'" % (scale,))

	# Fractional of largest.
	array[mask] -= np.min(array[mask])
	array[mask] /= np.max(array[mask])

	# Order.
	CHARS = [".", "-", ":", "=", "+", "*", "#", "%", "@"]
	WIDTH = 1.0 / len(CHARS)

	out = np.zeros_like(array, dtype=str)
	for index in utils.positions(array):
		val = array[index]
		out[index] = CHARS[math.ceil(val / WIDTH) - 1]

	return out

def main(fits, txt, frame, **kwargs):
	with ap.io.fits.open(fits) as hdulist:
		flximg = utils.filter_img(hdulist)

	rows = asciify(flximg["FLUX"][frame])

	with open(txt, "w") as f:
		# NOTE: We flip the output vertically so that it looks like (0, 0) is the
		#       bottom left. It isn't, but it makes it easier to see what's going
		#       on.
		for row in reversed(rows):
			for cell in row:
				f.write(cell)
			f.write("\n")
		f.flush()

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Take a Kepler Long Cadence K2 FITS File, and generate an ASCII version of the frame (one character per pixel). Since postage stamps are not square, blank spaces should be treated as being pixels not inside the postage stamp.")
		parser.add_argument("-f", "--frame", dest="frame", required=True, type=int, default=0, help="The frame number to ASCIIfy (default: 0).")
		parser.add_argument("input", nargs=1)
		parser.add_argument("output", nargs=1)

		args = parser.parse_args()

		main(fits=args.input[0], txt=args.output[0], **vars(args))

	__wrapped_main__()
