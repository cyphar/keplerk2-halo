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

import sys
import argparse

import numpy as np
import numpy.ma

import astropy
import astropy.io.fits

import utils

# Indexing of Kepler channels is a follows:
# * Each channel belongs to a module and has a number,
#   represented in the form MOD <module>.<number>.
# * The channel number is the number in the list of
#   channels (which ignore the modules {1, 5, 21, 25}.
#
# The numbering of channels is as follows:
#
#  __ __  4  3  8  7 12 11 __ __
#  __ __  1  2  5  6  9 10 __ __
#  15 14 20 19 24 23 25 28 29 32
#  16 13 17 18 21 22 26 27 30 31
#  35 34 39 38 43 42 45 48 49 52
#  36 33 40 37 44 41 46 47 50 51
#  55 54 59 58 62 61 66 65 69 72
#  56 53 60 57 63 64 67 68 70 71
#  __ __ 74 73 78 77 82 81 __ __
#  __ __ 75 76 79 80 83 84 __ __
#
# It should be noted that channels {5, 6, 7, 8, 17, 18, 19}
# are not useful, as the sensors have malfunctioned and produce
# meaningless noise.

# Needs to be reversed, so that it looks right.
NL = 0
CHANNELS = np.array([
  [NL, NL,  4,  3,  8,  7, 12, 11, NL, NL],
  [NL, NL,  1,  2,  5,  6,  9, 10, NL, NL],
  [15, 14, 20, 19, 24, 23, 25, 28, 29, 32],
  [16, 13, 17, 18, 21, 22, 26, 27, 30, 31],
  [35, 34, 39, 38, 43, 42, 45, 48, 49, 52],
  [36, 33, 40, 37, 44, 41, 46, 47, 50, 51],
  [55, 54, 59, 58, 62, 61, 66, 65, 69, 72],
  [56, 53, 60, 57, 63, 64, 67, 68, 70, 71],
  [NL, NL, 74, 73, 78, 77, 82, 81, NL, NL],
  [NL, NL, 75, 76, 79, 80, 83, 84, NL, NL],
])

BLACKLIST = {5, 6, 7, 8, 17, 18, 19, 20}

# In addition, the rows and columns have different axes.
# Each module has axes in each channel such that they look like
# this, **REGARDLESS** of the channel order (which is odd).
#
#  +--> <--+
#  |       |
#  V       V
#
#  ^       ^
#  |       |
#  +--> <--+

ROWS = np.array([
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
  [+1, -1, +1, -1, +1, -1, +1, -1, +1, -1],
])

COLS = ROWS.T

def normalize(frame, config):
	hist, bins = np.histogram(frame.flatten(), config.bins + 1, normed=True)

	cdf = np.cumsum(hist)
	cdf = cdf / np.max(cdf)

	frame = np.interp(frame.flatten(), bins[:-1], cdf).reshape(frame.shape)

	return frame ** 8

def main(fits, outf, config):
	hdulist = astropy.io.fits.open(fits)

	# Make sure the shape is the same for each frame.
	chsize = hdulist[1].data.shape
	assert(hdu.data.shape == chsize for hdu in hdulist[1:])

	# Create the FFI and special "0" arrays.
	ffisize = np.array(CHANNELS.shape) * chsize
	full = np.zeros(ffisize)

	# Frames for special modules.
	null = np.nan * np.ones(chsize)
	black = np.zeros(chsize)

	for position in utils.positions(CHANNELS):
		channel = CHANNELS[position]

		if channel == NL:
			frame = null
		elif channel in BLACKLIST:
			frame = black
		else:
			frame = hdulist[channel].data[::COLS[position],::ROWS[position]]
			frame = normalize(frame, config)

		# Set up slices to broadcast to.
		start = np.array(position) * chsize
		sl = [slice(s, e) for s, e in zip(start, start + chsize)]

		full[sl] = frame

	# Flip vertically to match image origin in top-left.
	full = full[::-1,...]

	newhdus = astropy.io.fits.HDUList([
		astropy.io.fits.PrimaryHDU(),
		astropy.io.fits.ImageHDU(data=full),
	])

	newhdus.writeto(outf, clobber=True)

if __name__ == "__main__":
	def __wrapped_main__():
		parser = argparse.ArgumentParser(description="Generates a fully stitched together FFI from a Kepler FFI file.")
		parser.add_argument("-b", "--bins", dest="bins", type=int, default=10000, help="The number of bins for normalisation (default: 10000).")
		parser.add_argument("-o", "--output", dest="outf", type=str, required=True, help="The output file.")
		parser.add_argument("ffi", nargs=1)

		config = parser.parse_args()
		main(fits=config.ffi[0], outf=config.outf, config=config)

	__wrapped_main__()
